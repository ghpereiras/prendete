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


def test_create_event_extracts_maps_url_from_pasted_iframe(client):
    token = register_and_login(client, "owner@example.com")
    iframe_snippet = (
        '<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3284"'
        ' width="600" height="450" style="border:0;" allowfullscreen=""'
        ' loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>'
    )
    response = create_event(client, token, maps_link=iframe_snippet)
    assert response.status_code == 201
    assert response.json()["maps_link"] == "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3284"


def test_create_event_maps_link_plain_url_unchanged(client):
    token = register_and_login(client, "owner@example.com")
    response = create_event(client, token, maps_link="https://maps.app.goo.gl/AbCdEf")
    assert response.json()["maps_link"] == "https://maps.app.goo.gl/AbCdEf"


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
