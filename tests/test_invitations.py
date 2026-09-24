from datetime import datetime, timedelta, timezone

from app.models.event import Event
from tests.conftest import auth_headers, register_and_login
from tests.test_events import EVENT_PAYLOAD, create_event


def get_invite_token(client, event_id, owner_token):
    response = client.get(f"/events/{event_id}/invite-link", headers=auth_headers(owner_token))
    return response.json()["invite_token"]


def test_get_invite_link_requires_owner(client):
    owner_token = register_and_login(client, "owner@example.com")
    stranger_token = register_and_login(client, "stranger@example.com")
    create_event(client, owner_token)

    response = client.get("/events/1/invite-link", headers=auth_headers(stranger_token))
    assert response.status_code == 403

    response = client.get("/events/1/invite-link", headers=auth_headers(owner_token))
    assert response.status_code == 200
    assert response.json()["invite_token"]


def test_preview_invite_is_public(client):
    owner_token = register_and_login(client, "owner@example.com")
    create_event(client, owner_token)
    token = get_invite_token(client, 1, owner_token)

    response = client.get(f"/events/invite/{token}")
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == EVENT_PAYLOAD["title"]
    assert body["spots_left"] == EVENT_PAYLOAD["max_attendees"]
    assert body["owner_id"] == 1


def test_preview_invite_includes_location_fields(client):
    owner_token = register_and_login(client, "owner@example.com")
    create_event(
        client,
        owner_token,
        location_details="Piso 4, depto B",
        maps_link="https://www.google.com/maps/embed?pb=abc123",
    )
    token = get_invite_token(client, 1, owner_token)

    body = client.get(f"/events/invite/{token}").json()
    assert body["location_details"] == "Piso 4, depto B"
    assert body["maps_link"] == "https://www.google.com/maps/embed?pb=abc123"


def test_preview_invite_registration_open_by_default(client):
    owner_token = register_and_login(client, "owner@example.com")
    create_event(client, owner_token)
    token = get_invite_token(client, 1, owner_token)

    body = client.get(f"/events/invite/{token}").json()
    assert body["registration_open"] is True


def test_registration_closes_at_event_start_by_default(client, db_session):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    soon = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    # no registration_deadline_minutes_before at all: should still default to closing at starts_at
    create_event(client, owner_token, starts_at=soon)

    # Creating an already-started event is blocked, so simulate time having
    # passed since a valid creation by backdating starts_at directly.
    event = db_session.get(Event, 1)
    event.starts_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    db_session.commit()

    token = get_invite_token(client, 1, owner_token)

    preview = client.get(f"/events/invite/{token}").json()
    assert preview["registration_open"] is False

    response = client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))
    assert response.status_code == 409


def test_registration_open_before_event_start_by_default(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    not_started_yet = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    create_event(client, owner_token, starts_at=not_started_yet)
    token = get_invite_token(client, 1, owner_token)

    preview = client.get(f"/events/invite/{token}").json()
    assert preview["registration_open"] is True

    response = client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))
    assert response.status_code == 201


def test_join_event_rejected_after_registration_deadline(client, db_session):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    far_future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    create_event(
        client,
        owner_token,
        starts_at=far_future,
        registration_deadline_minutes_before=60,
    )

    # Creating an event whose deadline has already passed is blocked, so
    # simulate time having passed since a valid creation by moving starts_at
    # closer: with a 60-minute deadline, starting in 10 minutes means the
    # registration window already closed 50 minutes ago.
    event = db_session.get(Event, 1)
    event.starts_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db_session.commit()

    token = get_invite_token(client, 1, owner_token)

    preview = client.get(f"/events/invite/{token}").json()
    assert preview["registration_open"] is False

    response = client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))
    assert response.status_code == 409


def test_join_event_allowed_before_registration_deadline(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    far_future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    create_event(
        client,
        owner_token,
        starts_at=far_future,
        registration_deadline_minutes_before=60,
    )
    token = get_invite_token(client, 1, owner_token)

    response = client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))
    assert response.status_code == 201


def test_preview_invite_invalid_token_404(client):
    response = client.get("/events/invite/does-not-exist")
    assert response.status_code == 404


def test_join_event_success(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    create_event(client, owner_token)
    token = get_invite_token(client, 1, owner_token)

    response = client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "accepted"
    assert body["event_id"] == 1
    assert body["comment"] is None


def test_join_event_with_comment(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    create_event(client, owner_token)
    token = get_invite_token(client, 1, owner_token)

    response = client.post(
        f"/events/invite/{token}/join",
        json={"comment": "Voy con mi pareja"},
        headers=auth_headers(friend_token),
    )
    assert response.status_code == 201
    assert response.json()["comment"] == "Voy con mi pareja"

    attendees = client.get("/events/1/attendees", headers=auth_headers(owner_token)).json()
    friend_entry = next(a for a in attendees if not a["is_owner"])
    assert friend_entry["comment"] == "Voy con mi pareja"


def test_attendee_comments_hidden_from_other_participants(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    other_token = register_and_login(client, "other@example.com")
    create_event(client, owner_token, max_attendees=5)
    token = get_invite_token(client, 1, owner_token)

    client.post(
        f"/events/invite/{token}/join",
        json={"comment": "Voy con mi pareja"},
        headers=auth_headers(friend_token),
    )
    client.post(f"/events/invite/{token}/join", headers=auth_headers(other_token))

    # another participant sees the friend's name but not their comment
    attendees_for_other = client.get("/events/1/attendees", headers=auth_headers(other_token)).json()
    friend_entry = next(a for a in attendees_for_other if a["email"] == "friend@example.com")
    assert friend_entry["comment"] is None

    # the friend can still see their own comment
    attendees_for_friend = client.get("/events/1/attendees", headers=auth_headers(friend_token)).json()
    own_entry = next(a for a in attendees_for_friend if a["email"] == "friend@example.com")
    assert own_entry["comment"] == "Voy con mi pareja"

    # the owner sees everyone's comment
    attendees_for_owner = client.get("/events/1/attendees", headers=auth_headers(owner_token)).json()
    friend_entry_for_owner = next(a for a in attendees_for_owner if a["email"] == "friend@example.com")
    assert friend_entry_for_owner["comment"] == "Voy con mi pareja"


def test_owner_cannot_join_own_event(client):
    owner_token = register_and_login(client, "owner@example.com")
    create_event(client, owner_token, max_attendees=1)
    token = get_invite_token(client, 1, owner_token)

    response = client.post(f"/events/invite/{token}/join", headers=auth_headers(owner_token))
    assert response.status_code == 409

    # the owner's attempt must not have consumed the only spot
    preview = client.get(f"/events/invite/{token}").json()
    assert preview["spots_left"] == 1


def test_join_event_updates_spots_left(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    create_event(client, owner_token)
    token = get_invite_token(client, 1, owner_token)

    client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))
    preview = client.get(f"/events/invite/{token}").json()
    assert preview["spots_left"] == EVENT_PAYLOAD["max_attendees"] - 1


def test_join_event_full_capacity_rejected(client):
    owner_token = register_and_login(client, "owner@example.com")
    create_event(client, owner_token, max_attendees=2)
    token = get_invite_token(client, 1, owner_token)

    for i in range(2):
        friend_token = register_and_login(client, f"friend{i}@example.com")
        response = client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))
        assert response.status_code == 201

    late_token = register_and_login(client, "late@example.com")
    response = client.post(f"/events/invite/{token}/join", headers=auth_headers(late_token))
    assert response.status_code == 409


def test_join_event_twice_rejected(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    create_event(client, owner_token)
    token = get_invite_token(client, 1, owner_token)

    client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))
    response = client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))
    assert response.status_code == 409


def test_join_event_invalid_token_404(client):
    friend_token = register_and_login(client, "friend@example.com")
    response = client.post("/events/invite/does-not-exist/join", headers=auth_headers(friend_token))
    assert response.status_code == 404


def test_leave_event_frees_capacity_and_allows_rejoin(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    create_event(client, owner_token, max_attendees=1)
    token = get_invite_token(client, 1, owner_token)

    client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))

    other_token = register_and_login(client, "other@example.com")
    full_response = client.post(f"/events/invite/{token}/join", headers=auth_headers(other_token))
    assert full_response.status_code == 409

    leave_response = client.patch(
        "/invitations/1", json={"status": "declined"}, headers=auth_headers(friend_token)
    )
    assert leave_response.status_code == 200
    assert leave_response.json()["status"] == "declined"

    preview = client.get(f"/events/invite/{token}").json()
    assert preview["spots_left"] == 1

    rejoin_response = client.post(f"/events/invite/{token}/join", headers=auth_headers(other_token))
    assert rejoin_response.status_code == 201


def test_update_invitation_can_set_comment(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    create_event(client, owner_token)
    token = get_invite_token(client, 1, owner_token)
    client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))

    response = client.patch(
        "/invitations/1",
        json={"status": "accepted", "comment": "Llego un poco tarde"},
        headers=auth_headers(friend_token),
    )
    assert response.status_code == 200
    assert response.json()["comment"] == "Llego un poco tarde"


def test_update_invitation_requires_being_the_invitee(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    stranger_token = register_and_login(client, "stranger@example.com")
    create_event(client, owner_token)
    token = get_invite_token(client, 1, owner_token)
    client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))

    response = client.patch(
        "/invitations/1", json={"status": "declined"}, headers=auth_headers(stranger_token)
    )
    assert response.status_code == 403


def test_list_invitations_requires_owner(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    create_event(client, owner_token)
    token = get_invite_token(client, 1, owner_token)
    client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))

    response = client.get("/events/1/invitations", headers=auth_headers(friend_token))
    assert response.status_code == 403

    response = client.get("/events/1/invitations", headers=auth_headers(owner_token))
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_regenerate_invite_link_invalidates_old_token(client):
    owner_token = register_and_login(client, "owner@example.com")
    create_event(client, owner_token)
    old_token = get_invite_token(client, 1, owner_token)

    response = client.post(
        "/events/1/invite-link/regenerate", headers=auth_headers(owner_token)
    )
    assert response.status_code == 200
    new_token = response.json()["invite_token"]
    assert new_token != old_token

    assert client.get(f"/events/invite/{old_token}").status_code == 404
    assert client.get(f"/events/invite/{new_token}").status_code == 200


def test_list_attendees_shows_owner_first_then_accepted(client):
    owner_token = register_and_login(client, "owner@example.com", full_name="Owner Person")
    friend_token = register_and_login(client, "friend@example.com", full_name="Friend Person")
    create_event(client, owner_token)
    token = get_invite_token(client, 1, owner_token)
    client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))

    response = client.get("/events/1/attendees", headers=auth_headers(owner_token))
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["full_name"] == "Owner Person"
    assert body[0]["is_owner"] is True
    assert body[1]["full_name"] == "Friend Person"
    assert body[1]["is_owner"] is False


def test_list_attendees_excludes_declined(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    create_event(client, owner_token)
    token = get_invite_token(client, 1, owner_token)
    client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))
    client.patch("/invitations/1", json={"status": "declined"}, headers=auth_headers(friend_token))

    response = client.get("/events/1/attendees", headers=auth_headers(owner_token))
    assert len(response.json()) == 1
    assert response.json()[0]["is_owner"] is True


def test_list_attendees_visible_to_participants_not_strangers(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    stranger_token = register_and_login(client, "stranger@example.com")
    create_event(client, owner_token)
    token = get_invite_token(client, 1, owner_token)
    client.post(f"/events/invite/{token}/join", headers=auth_headers(friend_token))

    assert client.get("/events/1/attendees", headers=auth_headers(friend_token)).status_code == 200
    assert client.get("/events/1/attendees", headers=auth_headers(stranger_token)).status_code == 404


def test_regenerate_invite_link_requires_owner(client):
    owner_token = register_and_login(client, "owner@example.com")
    stranger_token = register_and_login(client, "stranger@example.com")
    create_event(client, owner_token)

    response = client.post(
        "/events/1/invite-link/regenerate", headers=auth_headers(stranger_token)
    )
    assert response.status_code == 403
