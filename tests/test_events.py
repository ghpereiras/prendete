from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.models.event import Event
from tests.conftest import auth_headers, register_and_login

EVENT_PAYLOAD = {
    "title": "Asado",
    "description": "Juntada",
    "location": "Casa",
    "starts_at": "2026-11-01T20:00:00Z",
    "duration_minutes": 360,
    "max_attendees": 2,
}


def create_event(client, token, **overrides):
    payload = {**EVENT_PAYLOAD, **overrides}
    return client.post("/events", json=payload, headers=auth_headers(token))


def test_create_event_requires_auth(client):
    response = client.post("/events", json=EVENT_PAYLOAD)
    assert response.status_code == 401


def test_create_event_success(client):
    token = register_and_login(client, "owner@example.com")
    response = create_event(client, token)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Asado"
    assert body["max_attendees"] == 2
    assert "invite_token" not in body


def test_create_event_with_location_details_and_maps_link(client):
    token = register_and_login(client, "owner@example.com")
    response = create_event(
        client,
        token,
        location_details="Piso 4, depto B",
        maps_link="https://www.google.com/maps/embed?pb=abc123",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["location_details"] == "Piso 4, depto B"
    assert body["maps_link"] == "https://www.google.com/maps/embed?pb=abc123"


def test_create_event_maps_link_stored_as_given(client):
    token = register_and_login(client, "owner@example.com")
    response = create_event(
        client, token, maps_link="https://www.google.com/maps/embed/v1/place?key=abc&q=place_id:xyz"
    )
    assert response.json()["maps_link"] == "https://www.google.com/maps/embed/v1/place?key=abc&q=place_id:xyz"


def test_create_event_location_fields_are_optional(client):
    token = register_and_login(client, "owner@example.com")
    response = create_event(client, token)
    body = response.json()
    assert body["location_details"] is None
    assert body["maps_link"] is None


def test_create_event_max_attendees_zero_rejected(client):
    token = register_and_login(client, "owner@example.com")
    response = create_event(client, token, max_attendees=0)
    assert response.status_code == 422


def test_create_event_duration_zero_rejected(client):
    token = register_and_login(client, "owner@example.com")
    response = create_event(client, token, duration_minutes=0)
    assert response.status_code == 422


def test_create_event_registration_deadline_is_optional(client):
    token = register_and_login(client, "owner@example.com")
    response = create_event(client, token)
    assert response.json()["registration_deadline_minutes_before"] is None


def test_create_event_registration_deadline_zero_rejected(client):
    token = register_and_login(client, "owner@example.com")
    response = create_event(client, token, registration_deadline_minutes_before=0)
    assert response.status_code == 422


def test_create_event_starts_at_in_the_past_rejected(client):
    token = register_and_login(client, "owner@example.com")
    past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    response = create_event(client, token, starts_at=past)
    assert response.status_code == 422


def test_create_event_starts_at_right_now_rejected(client):
    token = register_and_login(client, "owner@example.com")
    response = create_event(client, token, starts_at=datetime.now(timezone.utc).isoformat())
    assert response.status_code == 422


def test_create_event_registration_already_closed_at_creation_rejected(client):
    token = register_and_login(client, "owner@example.com")
    soon = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    # closes 1 hour before start: with the event starting in 10 minutes, that
    # deadline already passed the moment this request is made.
    response = create_event(
        client, token, starts_at=soon, registration_deadline_minutes_before=60
    )
    assert response.status_code == 422


def test_create_event_registration_window_still_open_accepted(client):
    token = register_and_login(client, "owner@example.com")
    soon = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    response = create_event(
        client, token, starts_at=soon, registration_deadline_minutes_before=60
    )
    assert response.status_code == 201


def test_create_event_registration_deadline_accepted(client):
    token = register_and_login(client, "owner@example.com")
    response = create_event(client, token, registration_deadline_minutes_before=120)
    assert response.json()["registration_deadline_minutes_before"] == 120


def test_list_events_scoped_to_owner_and_participants(client):
    owner_token = register_and_login(client, "owner@example.com")
    participant_token = register_and_login(client, "friend@example.com")
    stranger_token = register_and_login(client, "stranger@example.com")

    create_event(client, owner_token)
    invite_token = client.get(
        "/events/1/invite-link", headers=auth_headers(owner_token)
    ).json()["invite_token"]
    client.post(f"/events/invite/{invite_token}/join", headers=auth_headers(participant_token))

    owner_events = client.get("/events", headers=auth_headers(owner_token)).json()
    participant_events = client.get("/events", headers=auth_headers(participant_token)).json()
    stranger_events = client.get("/events", headers=auth_headers(stranger_token)).json()

    assert len(owner_events) == 1
    assert len(participant_events) == 1
    assert len(stranger_events) == 0


def test_list_events_includes_owner_name(client):
    token = register_and_login(client, "owner@example.com", full_name="Owner Person")
    create_event(client, token)

    events = client.get("/events", headers=auth_headers(token)).json()
    assert events[0]["owner_name"] == "Owner Person"


def test_list_events_sorted_by_soonest_start(client):
    token = register_and_login(client, "owner@example.com")
    create_event(client, token, title="Later", starts_at="2026-12-01T20:00:00Z")
    create_event(client, token, title="Sooner", starts_at="2026-11-01T20:00:00Z")
    create_event(client, token, title="Middle", starts_at="2026-11-15T20:00:00Z")

    events = client.get("/events", headers=auth_headers(token)).json()
    assert [e["title"] for e in events] == ["Sooner", "Middle", "Later"]


def test_get_event_owner_can_view(client):
    token = register_and_login(client, "owner@example.com")
    create_event(client, token)
    response = client.get("/events/1", headers=auth_headers(token))
    assert response.status_code == 200


def test_get_event_stranger_gets_404(client):
    owner_token = register_and_login(client, "owner@example.com")
    stranger_token = register_and_login(client, "stranger@example.com")
    create_event(client, owner_token)
    response = client.get("/events/1", headers=auth_headers(stranger_token))
    assert response.status_code == 404


def test_get_event_participant_can_view(client):
    owner_token = register_and_login(client, "owner@example.com")
    participant_token = register_and_login(client, "friend@example.com")
    create_event(client, owner_token)
    invite_token = client.get(
        "/events/1/invite-link", headers=auth_headers(owner_token)
    ).json()["invite_token"]
    client.post(f"/events/invite/{invite_token}/join", headers=auth_headers(participant_token))

    response = client.get("/events/1", headers=auth_headers(participant_token))
    assert response.status_code == 200


def test_update_event_success(client):
    token = register_and_login(client, "owner@example.com")
    create_event(client, token)
    response = client.patch(
        "/events/1", json={**EVENT_PAYLOAD, "title": "Asado actualizado"}, headers=auth_headers(token)
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Asado actualizado"


def test_update_event_requires_owner(client):
    owner_token = register_and_login(client, "owner@example.com")
    stranger_token = register_and_login(client, "stranger@example.com")
    create_event(client, owner_token)

    response = client.patch("/events/1", json=EVENT_PAYLOAD, headers=auth_headers(stranger_token))
    assert response.status_code == 403


def test_update_nonexistent_event_404(client):
    token = register_and_login(client, "owner@example.com")
    response = client.patch("/events/999", json=EVENT_PAYLOAD, headers=auth_headers(token))
    assert response.status_code == 404


def test_update_event_max_attendees_below_accepted_rejected(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend1_token = register_and_login(client, "friend1@example.com")
    friend2_token = register_and_login(client, "friend2@example.com")
    create_event(client, owner_token, max_attendees=5)
    invite_token = client.get(
        "/events/1/invite-link", headers=auth_headers(owner_token)
    ).json()["invite_token"]
    client.post(f"/events/invite/{invite_token}/join", headers=auth_headers(friend1_token))
    client.post(f"/events/invite/{invite_token}/join", headers=auth_headers(friend2_token))

    response = client.patch(
        "/events/1", json={**EVENT_PAYLOAD, "max_attendees": 1}, headers=auth_headers(owner_token)
    )
    assert response.status_code == 422


def test_update_event_already_started_rejected(client, db_session):
    token = register_and_login(client, "owner@example.com")
    create_event(client, token)
    event = db_session.get(Event, 1)
    event.starts_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    db_session.commit()

    response = client.patch("/events/1", json=EVENT_PAYLOAD, headers=auth_headers(token))
    assert response.status_code == 403


def test_delete_event_already_started_rejected(client, db_session):
    token = register_and_login(client, "owner@example.com")
    create_event(client, token)
    event = db_session.get(Event, 1)
    event.starts_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    db_session.commit()

    response = client.delete("/events/1", headers=auth_headers(token))
    assert response.status_code == 403


def test_update_event_sends_push_to_attendees_not_owner(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    create_event(client, owner_token)
    invite_token = client.get(
        "/events/1/invite-link", headers=auth_headers(owner_token)
    ).json()["invite_token"]
    client.post(f"/events/invite/{invite_token}/join", headers=auth_headers(friend_token))
    friend_id = client.get("/users/me", headers=auth_headers(friend_token)).json()["id"]

    with patch("app.routers.events.push.send_push_to_user") as mock_send:
        response = client.patch(
            "/events/1",
            json={**EVENT_PAYLOAD, "title": "Asado actualizado"},
            headers=auth_headers(owner_token),
        )
    assert response.status_code == 200
    mock_send.assert_called_once()
    _, user_id, payload = mock_send.call_args.args
    assert user_id == friend_id
    assert "Asado actualizado" in payload["body"]


def test_update_event_notify_attendees_false_skips_push(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    create_event(client, owner_token)
    invite_token = client.get(
        "/events/1/invite-link", headers=auth_headers(owner_token)
    ).json()["invite_token"]
    client.post(f"/events/invite/{invite_token}/join", headers=auth_headers(friend_token))

    with patch("app.routers.events.push.send_push_to_user") as mock_send:
        response = client.patch(
            "/events/1",
            json={**EVENT_PAYLOAD, "title": "Asado actualizado", "notify_attendees": False},
            headers=auth_headers(owner_token),
        )
    assert response.status_code == 200
    mock_send.assert_not_called()


def test_delete_event_sends_push_to_attendees(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    create_event(client, owner_token)
    invite_token = client.get(
        "/events/1/invite-link", headers=auth_headers(owner_token)
    ).json()["invite_token"]
    client.post(f"/events/invite/{invite_token}/join", headers=auth_headers(friend_token))
    friend_id = client.get("/users/me", headers=auth_headers(friend_token)).json()["id"]

    with patch("app.routers.events.push.send_push_to_user") as mock_send:
        response = client.delete("/events/1", headers=auth_headers(owner_token))
    assert response.status_code == 204
    mock_send.assert_called_once()
    _, user_id, _ = mock_send.call_args.args
    assert user_id == friend_id


def test_delete_event_requires_owner(client):
    owner_token = register_and_login(client, "owner@example.com")
    stranger_token = register_and_login(client, "stranger@example.com")
    create_event(client, owner_token)

    response = client.delete("/events/1", headers=auth_headers(stranger_token))
    assert response.status_code == 403

    response = client.delete("/events/1", headers=auth_headers(owner_token))
    assert response.status_code == 204


def test_delete_nonexistent_event_404(client):
    token = register_and_login(client, "owner@example.com")
    response = client.delete("/events/999", headers=auth_headers(token))
    assert response.status_code == 404
