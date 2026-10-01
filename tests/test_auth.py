from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.models.email_verification_token import EmailVerificationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from tests.conftest import auth_headers, login, register, register_and_login


def test_register_creates_user(client):
    response = register(client, "owner@example.com")
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "owner@example.com"
    assert body["full_name"] == "Test User"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email_rejected(client):
    register(client, "owner@example.com")
    response = register(client, "owner@example.com")
    assert response.status_code == 409


def test_login_success(client):
    register(client, "owner@example.com")
    response = client.post(
        "/auth/login", data={"username": "owner@example.com", "password": "secret123"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password_rejected(client):
    register(client, "owner@example.com")
    response = client.post(
        "/auth/login", data={"username": "owner@example.com", "password": "wrongpass"}
    )
    assert response.status_code == 401


def test_login_unknown_email_rejected(client):
    response = client.post(
        "/auth/login", data={"username": "nobody@example.com", "password": "secret123"}
    )
    assert response.status_code == 401


def test_me_requires_auth(client):
    response = client.get("/users/me")
    assert response.status_code == 401


def test_me_returns_current_user(client):
    token = register_and_login(client, "owner@example.com")
    response = client.get("/users/me", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["email"] == "owner@example.com"


def test_register_sends_verification_email(client, mock_send_email):
    response = register(client, "owner@example.com")
    assert response.status_code == 201
    assert response.json()["email_verified_at"] is None
    mock_send_email.assert_called_once()
    assert mock_send_email.call_args.args[0] == "owner@example.com"


def test_verify_email_with_valid_token(client, db_session):
    register(client, "owner@example.com")
    user = db_session.query(User).filter_by(email="owner@example.com").first()
    token = db_session.query(EmailVerificationToken).filter_by(user_id=user.id).first()

    response = client.post("/auth/verify-email", json={"token": token.token})
    assert response.status_code == 204

    db_session.refresh(user)
    assert user.email_verified_at is not None


def test_verify_email_with_invalid_token_rejected(client):
    response = client.post("/auth/verify-email", json={"token": "does-not-exist"})
    assert response.status_code == 400


def test_verify_email_with_expired_token_rejected(client, db_session):
    register(client, "owner@example.com")
    user = db_session.query(User).filter_by(email="owner@example.com").first()
    token = db_session.query(EmailVerificationToken).filter_by(user_id=user.id).first()
    token.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()

    response = client.post("/auth/verify-email", json={"token": token.token})
    assert response.status_code == 400


def test_resend_verification_for_unknown_email_is_silent(client, mock_send_email):
    response = client.post("/auth/resend-verification", json={"email": "nobody@example.com"})
    assert response.status_code == 204
    mock_send_email.assert_not_called()


def test_resend_verification_issues_new_token(client, db_session, mock_send_email):
    register(client, "owner@example.com")
    user = db_session.query(User).filter_by(email="owner@example.com").first()
    old_token = db_session.query(EmailVerificationToken).filter_by(user_id=user.id).first().token
    mock_send_email.reset_mock()

    response = client.post("/auth/resend-verification", json={"email": "owner@example.com"})
    assert response.status_code == 204
    mock_send_email.assert_called_once()

    tokens = db_session.query(EmailVerificationToken).filter_by(user_id=user.id).all()
    assert len(tokens) == 1
    assert tokens[0].token != old_token


def test_resend_verification_uses_requested_language_not_saved_language(client, mock_send_email):
    # Account was created with the default saved language ("es"), but the
    # page asking to resend is in English right now — the email should
    # follow the page, not the (possibly stale) saved account language.
    register(client, "owner@example.com")
    mock_send_email.reset_mock()

    response = client.post(
        "/auth/resend-verification", json={"email": "owner@example.com", "language": "en"}
    )
    assert response.status_code == 204
    subject = mock_send_email.call_args.args[1]
    assert subject == "Confirm your email on Prendete"


def test_resend_verification_noop_once_verified(client, db_session, mock_send_email):
    register(client, "owner@example.com")
    user = db_session.query(User).filter_by(email="owner@example.com").first()
    user.email_verified_at = datetime.now(timezone.utc)
    db_session.commit()
    mock_send_email.reset_mock()

    response = client.post("/auth/resend-verification", json={"email": "owner@example.com"})
    assert response.status_code == 204
    mock_send_email.assert_not_called()


def test_login_allowed_unverified_within_grace_period(client):
    register(client, "owner@example.com")
    response = client.post(
        "/auth/login", data={"username": "owner@example.com", "password": "secret123"}
    )
    assert response.status_code == 200


def test_login_blocked_unverified_after_grace_period(client, db_session):
    register(client, "owner@example.com")
    user = db_session.query(User).filter_by(email="owner@example.com").first()
    user.created_at = datetime.now(timezone.utc) - timedelta(days=8)
    db_session.commit()

    response = client.post(
        "/auth/login", data={"username": "owner@example.com", "password": "secret123"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "email_not_verified"


def test_verifying_unlocks_login_after_grace_period(client, db_session):
    register(client, "owner@example.com")
    user = db_session.query(User).filter_by(email="owner@example.com").first()
    user.created_at = datetime.now(timezone.utc) - timedelta(days=8)
    db_session.commit()
    token = db_session.query(EmailVerificationToken).filter_by(user_id=user.id).first()

    client.post("/auth/verify-email", json={"token": token.token})

    response = client.post(
        "/auth/login", data={"username": "owner@example.com", "password": "secret123"}
    )
    assert response.status_code == 200


def test_password_reset_request_for_unknown_email_is_silent(client, mock_send_email):
    response = client.post("/auth/password-reset/request", json={"email": "nobody@example.com"})
    assert response.status_code == 204
    mock_send_email.assert_not_called()


def test_password_reset_request_sends_email_for_known_user(client, mock_send_email):
    register(client, "owner@example.com")
    mock_send_email.reset_mock()

    response = client.post("/auth/password-reset/request", json={"email": "owner@example.com"})
    assert response.status_code == 204
    mock_send_email.assert_called_once()


def test_password_reset_request_uses_requested_language_not_saved_language(client, mock_send_email):
    register(client, "owner@example.com")
    mock_send_email.reset_mock()

    response = client.post(
        "/auth/password-reset/request", json={"email": "owner@example.com", "language": "en"}
    )
    assert response.status_code == 204
    subject = mock_send_email.call_args.args[1]
    assert subject == "Reset your password on Prendete"


def test_password_reset_confirm_changes_password(client, db_session):
    register(client, "owner@example.com")
    user = db_session.query(User).filter_by(email="owner@example.com").first()
    client.post("/auth/password-reset/request", json={"email": "owner@example.com"})
    token = db_session.query(PasswordResetToken).filter_by(user_id=user.id).first()

    response = client.post(
        "/auth/password-reset/confirm", json={"token": token.token, "new_password": "newpassword123"}
    )
    assert response.status_code == 204

    old_login = client.post(
        "/auth/login", data={"username": "owner@example.com", "password": "secret123"}
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/auth/login", data={"username": "owner@example.com", "password": "newpassword123"}
    )
    assert new_login.status_code == 200


def test_password_reset_confirm_token_is_single_use(client, db_session):
    register(client, "owner@example.com")
    user = db_session.query(User).filter_by(email="owner@example.com").first()
    client.post("/auth/password-reset/request", json={"email": "owner@example.com"})
    token = db_session.query(PasswordResetToken).filter_by(user_id=user.id).first()

    first = client.post(
        "/auth/password-reset/confirm", json={"token": token.token, "new_password": "newpassword123"}
    )
    assert first.status_code == 204

    second = client.post(
        "/auth/password-reset/confirm", json={"token": token.token, "new_password": "anotherpass123"}
    )
    assert second.status_code == 400


def test_password_reset_confirm_with_invalid_token_rejected(client):
    response = client.post(
        "/auth/password-reset/confirm", json={"token": "does-not-exist", "new_password": "newpassword123"}
    )
    assert response.status_code == 400


def test_change_password_requires_auth(client):
    response = client.patch(
        "/users/me/password", json={"current_password": "secret123", "new_password": "newpassword123"}
    )
    assert response.status_code == 401


def test_change_password_success(client):
    token = register_and_login(client, "owner@example.com")
    response = client.patch(
        "/users/me/password",
        json={"current_password": "secret123", "new_password": "newpassword123"},
        headers=auth_headers(token),
    )
    assert response.status_code == 204

    old_login = client.post(
        "/auth/login", data={"username": "owner@example.com", "password": "secret123"}
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/auth/login", data={"username": "owner@example.com", "password": "newpassword123"}
    )
    assert new_login.status_code == 200


def test_change_password_wrong_current_password_rejected(client):
    token = register_and_login(client, "owner@example.com")
    response = client.patch(
        "/users/me/password",
        json={"current_password": "wrongpass", "new_password": "newpassword123"},
        headers=auth_headers(token),
    )
    assert response.status_code == 400

    still_works = client.post(
        "/auth/login", data={"username": "owner@example.com", "password": "secret123"}
    )
    assert still_works.status_code == 200


GOOGLE_INFO = {
    "email": "google.user@example.com",
    "email_verified": True,
    "given_name": "Gabi",
    "family_name": "Perez",
    "nonce": "abc123",
}


def _google_login(client, info=GOOGLE_INFO, nonce="abc123"):
    with patch("app.google_auth.id_token.verify_oauth2_token", return_value=info), patch(
        "app.google_auth.settings.google_client_id", "client-id"
    ):
        return client.post(
            "/auth/google", json={"credential": "fake", "nonce": nonce, "language": "en"}
        )


def test_google_login_creates_verified_passwordless_user(client, mock_send_email):
    response = _google_login(client)
    assert response.status_code == 200

    me = client.get("/users/me", headers=auth_headers(response.json()["access_token"])).json()
    assert me["email"] == "google.user@example.com"
    assert me["full_name"] == "Gabi Perez"
    assert me["language"] == "en"
    assert me["email_verified_at"] is not None
    assert me["has_password"] is False
    mock_send_email.assert_not_called()


def test_google_login_returns_existing_verified_user(client, db_session):
    register(client, "google.user@example.com", first_name="Existing", last_name="Account")
    user = db_session.query(User).filter_by(email="google.user@example.com").one()
    user.email_verified_at = datetime.now(timezone.utc)
    db_session.commit()

    response = _google_login(client)
    assert response.status_code == 200
    me = client.get("/users/me", headers=auth_headers(response.json()["access_token"])).json()
    assert me["full_name"] == "Existing Account"
    assert me["has_password"] is True


def test_google_login_drops_password_of_unverified_account(client):
    # Whoever pre-registered an email never proved they own it, so their
    # password must not survive the real owner signing in with Google.
    register(client, "google.user@example.com", password="attacker-pass")

    assert _google_login(client).status_code == 200

    login_response = client.post(
        "/auth/login", data={"username": "google.user@example.com", "password": "attacker-pass"}
    )
    assert login_response.status_code == 401


def test_google_login_rejects_nonce_mismatch(client):
    assert _google_login(client, nonce="other").status_code == 401


def test_google_login_rejects_unverified_google_email(client):
    info = {**GOOGLE_INFO, "email_verified": False}
    assert _google_login(client, info=info).status_code == 401


def test_google_login_rejects_invalid_token(client):
    with patch("app.google_auth.id_token.verify_oauth2_token", side_effect=ValueError("bad")), patch(
        "app.google_auth.settings.google_client_id", "client-id"
    ):
        response = client.post("/auth/google", json={"credential": "x", "nonce": "abc123"})
    assert response.status_code == 401


def test_google_login_unavailable_when_not_configured(client):
    with patch("app.google_auth.settings.google_client_id", ""):
        response = client.post("/auth/google", json={"credential": "x", "nonce": "abc123"})
    assert response.status_code == 503


def test_passwordless_account_cannot_log_in_with_password(client):
    _google_login(client)
    response = client.post(
        "/auth/login", data={"username": "google.user@example.com", "password": "anything"}
    )
    assert response.status_code == 401


def test_google_login_imports_profile_picture_for_new_user(client):
    info = {**GOOGLE_INFO, "picture": "https://lh3.googleusercontent.com/a/abc=s96-c"}
    with patch("app.google_auth.fetch_profile_picture", return_value=b"jpeg-bytes") as fetch:
        with patch("app.google_auth.id_token.verify_oauth2_token", return_value=info), patch(
            "app.google_auth.settings.google_client_id", "client-id"
        ):
            response = client.post("/auth/google", json={"credential": "fake", "nonce": "abc123"})
    assert response.status_code == 200
    fetch.assert_called_once_with(info["picture"])

    me = client.get("/users/me", headers=auth_headers(response.json()["access_token"])).json()
    assert me["avatar_url"] is not None


def test_fetch_profile_picture_rejects_non_google_hosts():
    from app.google_auth import fetch_profile_picture

    with patch("app.google_auth.requests.get") as get:
        assert fetch_profile_picture("https://evil.example.com/a.jpg") is None
        assert fetch_profile_picture("http://lh3.googleusercontent.com/a.jpg") is None
    get.assert_not_called()


def test_fetch_profile_picture_returns_normalized_jpeg_and_requests_larger_size():
    import io

    from PIL import Image

    from app.google_auth import fetch_profile_picture

    buffer = io.BytesIO()
    Image.new("RGB", (96, 96), (10, 120, 200)).save(buffer, format="PNG")
    with patch("app.google_auth.requests.get") as get:
        get.return_value.content = buffer.getvalue()
        result = fetch_profile_picture("https://lh3.googleusercontent.com/a/abc=s96-c")
    assert get.call_args.args[0].endswith("=s256-c")
    assert Image.open(io.BytesIO(result)).format == "JPEG"


def test_google_login_succeeds_when_profile_picture_download_fails(client):
    import requests

    info = {**GOOGLE_INFO, "picture": "https://lh3.googleusercontent.com/a/abc=s96-c"}
    with patch("app.google_auth.requests.get", side_effect=requests.ConnectionError("down")):
        with patch("app.google_auth.id_token.verify_oauth2_token", return_value=info), patch(
            "app.google_auth.settings.google_client_id", "client-id"
        ):
            response = client.post("/auth/google", json={"credential": "fake", "nonce": "abc123"})
    assert response.status_code == 200
    me = client.get("/users/me", headers=auth_headers(response.json()["access_token"])).json()
    assert me["avatar_url"] is None


def test_delete_me_requires_auth(client):
    assert client.delete("/users/me").status_code == 401


def test_delete_me_removes_account_and_everything_it_owns(client, db_session):
    from app.models.attendee import Attendee
    from app.models.event import Event
    from app.models.event_poll import EventPoll, EventPollVote
    from app.models.push_subscription import PushSubscription
    from tests.test_event_polls import create_poll, get_invite_token
    from tests.test_events import create_event
    from tests.test_push import SUBSCRIPTION_PAYLOAD

    leaver_token = register_and_login(client, "leaver@example.com")
    other_token = register_and_login(client, "other@example.com")

    # Owned by the leaver: an event the other user attends, a poll the other user voted on.
    owned_event = create_event(client, leaver_token).json()
    owned_event_token = client.get(
        f"/events/{owned_event['id']}/invite-link", headers=auth_headers(leaver_token)
    ).json()["invite_token"]
    client.post(f"/events/invite/{owned_event_token}/join", headers=auth_headers(other_token))
    owned_poll = create_poll(client, leaver_token).json()
    poll_token = get_invite_token(client, owned_poll["id"], leaver_token)
    client.post(
        f"/event-polls/invite/{poll_token}/vote",
        json={"option_ids": [owned_poll["date_options"][0]["id"]]},
        headers=auth_headers(other_token),
    )

    # Owned by the other user: an event and a poll the leaver joined / voted on.
    kept_event = create_event(client, other_token).json()
    kept_event_token = client.get(
        f"/events/{kept_event['id']}/invite-link", headers=auth_headers(other_token)
    ).json()["invite_token"]
    client.post(f"/events/invite/{kept_event_token}/join", headers=auth_headers(leaver_token))
    kept_poll = create_poll(client, other_token).json()
    kept_poll_token = get_invite_token(client, kept_poll["id"], other_token)
    client.post(
        f"/event-polls/invite/{kept_poll_token}/vote",
        json={"option_ids": [kept_poll["date_options"][0]["id"]]},
        headers=auth_headers(leaver_token),
    )
    client.post(
        "/users/me/push-subscriptions", json=SUBSCRIPTION_PAYLOAD, headers=auth_headers(leaver_token)
    )

    assert client.delete("/users/me", headers=auth_headers(leaver_token)).status_code == 204

    db_session.expire_all()
    assert db_session.query(User).filter_by(email="leaver@example.com").first() is None
    assert db_session.query(User).filter_by(email="other@example.com").first() is not None
    assert db_session.get(Event, owned_event["id"]) is None
    assert db_session.get(EventPoll, owned_poll["id"]) is None
    assert db_session.query(PushSubscription).count() == 0
    # The other user's own event and poll survive, minus the leaver's attendance and vote.
    assert db_session.get(Event, kept_event["id"]) is not None
    assert db_session.get(EventPoll, kept_poll["id"]) is not None
    assert db_session.query(Attendee).filter_by(event_id=kept_event["id"]).count() == 0
    assert db_session.query(EventPollVote).count() == 0
    # The deleted account's token no longer works.
    assert client.get("/users/me", headers=auth_headers(leaver_token)).status_code == 401
