from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.models.event import Event
from app.models.user import User
from tests.conftest import auth_headers, register_and_login
from tests.test_event_polls import create_poll, get_invite_token
from tests.test_events import create_event

ADMIN_EMAIL = "admin@example.com"


@pytest.fixture(autouse=True)
def admin_emails():
    with patch("app.models.user.settings.admin_emails", ADMIN_EMAIL):
        yield


def _verify(db_session, email):
    user = db_session.query(User).filter_by(email=email).one()
    user.email_verified_at = datetime.now(timezone.utc)
    db_session.commit()
    return user


def _admin_token(client, db_session):
    token = register_and_login(client, ADMIN_EMAIL)
    _verify(db_session, ADMIN_EMAIL)
    return token


def test_stats_requires_auth(client):
    assert client.get("/admin/stats").status_code == 401


def test_stats_rejects_non_admin(client, db_session):
    token = register_and_login(client, "someone@example.com")
    _verify(db_session, "someone@example.com")
    assert client.get("/admin/stats", headers=auth_headers(token)).status_code == 403


def test_stats_rejects_admin_email_that_is_not_verified(client):
    token = register_and_login(client, ADMIN_EMAIL)
    assert client.get("/admin/stats", headers=auth_headers(token)).status_code == 403


def test_me_exposes_is_admin(client, db_session):
    admin_token = _admin_token(client, db_session)
    other_token = register_and_login(client, "someone@example.com")
    assert client.get("/users/me", headers=auth_headers(admin_token)).json()["is_admin"] is True
    assert client.get("/users/me", headers=auth_headers(other_token)).json()["is_admin"] is False


def test_stats_counts_users_events_polls_and_attendances(client, db_session):
    admin_token = _admin_token(client, db_session)
    friend_token = register_and_login(client, "friend@example.com")
    register_and_login(client, "idle@example.com")  # never does anything
    google_user = User(
        email="google@example.com", first_name="Goo", last_name="Gle", hashed_password=None,
        email_verified_at=datetime.now(timezone.utc), language="en",
    )
    db_session.add(google_user)
    db_session.commit()

    event = create_event(client, admin_token).json()
    invite = client.get(
        f"/events/{event['id']}/invite-link", headers=auth_headers(admin_token)
    ).json()["invite_token"]
    client.post(f"/events/invite/{invite}/join", headers=auth_headers(friend_token))
    poll = create_poll(client, admin_token).json()
    poll_token = get_invite_token(client, poll["id"], admin_token)
    client.post(
        f"/event-polls/invite/{poll_token}/vote",
        json={"option_ids": [poll["date_options"][0]["id"]]},
        headers=auth_headers(friend_token),
    )

    response = client.get("/admin/stats", headers=auth_headers(admin_token))
    assert response.status_code == 200
    stats = response.json()

    users = stats["users"]
    assert users["registered"] == {"total": 4, "last_24h": 4, "last_7d": 4, "last_30d": 4}
    assert users["with_password"] == 3
    assert users["google_only"] == 1
    assert users["email_verified"] == 2  # admin + google
    assert users["email_unverified"] == 2
    assert users["language_en"] == 1
    assert users["never_engaged"] == 2  # idle + google
    assert users["active"]["total"] == 2  # admin (created) + friend (joined/voted)
    assert users["with_push"] == 0
    assert sum(day["count"] for day in users["signups_by_day"]) == 4
    assert len(users["signups_by_day"]) == 30
    assert users["recent_signups"][0]["login_method"] in {"password", "google"}
    assert {s["login_method"] for s in users["recent_signups"]} == {"password", "google"}

    assert stats["events"]["created"]["total"] == 1
    assert stats["events"]["upcoming"] + stats["events"]["past"] == 1
    assert stats["events"]["avg_attendees"] == 1.0
    assert stats["polls"]["created"]["total"] == 1
    assert stats["polls"]["open"] == 1
    assert stats["polls"]["resolved"] == 0
    assert stats["polls"]["avg_participants"] == 1.0
    assert stats["attendances"]["total"] == 1


def test_stats_windows_exclude_old_records(client, db_session):
    admin_token = _admin_token(client, db_session)
    old_token = register_and_login(client, "old@example.com")
    old_user = db_session.query(User).filter_by(email="old@example.com").one()
    old_user.created_at = datetime.now(timezone.utc) - timedelta(days=40)
    db_session.commit()
    create_event(client, old_token)
    event = db_session.query(Event).one()
    event.created_at = datetime.now(timezone.utc) - timedelta(days=10)
    db_session.commit()

    stats = client.get("/admin/stats", headers=auth_headers(admin_token)).json()
    assert stats["users"]["registered"] == {"total": 2, "last_24h": 1, "last_7d": 1, "last_30d": 1}
    assert stats["events"]["created"] == {"total": 1, "last_24h": 0, "last_7d": 0, "last_30d": 1}
    assert stats["users"]["active"]["last_7d"] == 0
    assert stats["users"]["active"]["last_30d"] == 1


def test_stats_counts_locked_out_accounts(client, db_session):
    admin_token = _admin_token(client, db_session)
    register_and_login(client, "stale@example.com")
    stale = db_session.query(User).filter_by(email="stale@example.com").one()
    stale.created_at = datetime.now(timezone.utc) - timedelta(days=8)
    db_session.commit()

    stats = client.get("/admin/stats", headers=auth_headers(admin_token)).json()
    assert stats["users"]["locked_out"] == 1


def test_stats_with_empty_database_has_no_division_errors(client, db_session):
    admin_token = _admin_token(client, db_session)
    stats = client.get("/admin/stats", headers=auth_headers(admin_token)).json()
    assert stats["events"]["avg_attendees"] == 0.0
    assert stats["polls"]["avg_participants"] == 0.0
