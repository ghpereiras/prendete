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
