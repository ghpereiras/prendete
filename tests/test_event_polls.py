from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from tests.conftest import auth_headers, register_and_login
from tests.test_events import EVENT_PAYLOAD, create_event

POLL_PAYLOAD = {
    "title": "Asado de fin de año",
    "description": "Buscando fecha",
    "location": "Bosques de Palermo, Buenos Aires",
    "duration_minutes": 180,
    "date_options": ["2026-11-01T20:00:00Z", "2026-11-08T20:00:00Z", "2026-11-15T20:00:00Z"],
}


def create_poll(client, token, **overrides):
    payload = {**POLL_PAYLOAD, **overrides}
    return client.post("/event-polls", json=payload, headers=auth_headers(token))


def get_invite_token(client, poll_id, owner_token):
    response = client.get(f"/event-polls/{poll_id}/invite-link", headers=auth_headers(owner_token))
    return response.json()["invite_token"]


def test_create_poll_requires_auth(client):
    response = client.post("/event-polls", json=POLL_PAYLOAD)
    assert response.status_code == 401


def test_create_poll_success(client):
    token = register_and_login(client, "owner@example.com")
    response = create_poll(client, token)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Asado de fin de año"
    assert len(body["date_options"]) == 3
    assert all(option["voters"] == [] for option in body["date_options"])
    assert body["resulting_event_id"] is None


def test_date_options_are_sorted_chronologically(client):
    token = register_and_login(client, "owner@example.com")
    response = create_poll(
        client,
        token,
        date_options=["2026-11-15T20:00:00Z", "2026-11-01T20:00:00Z", "2026-11-08T20:00:00Z"],
    )
    assert response.status_code == 201
    starts = [option["starts_at"] for option in response.json()["date_options"]]
    assert starts == sorted(starts)


def test_invite_preview_date_options_are_sorted_chronologically(client):
    token = register_and_login(client, "owner@example.com")
    poll = create_poll(
        client,
        token,
        date_options=["2026-11-15T20:00:00Z", "2026-11-01T20:00:00Z", "2026-11-08T20:00:00Z"],
    ).json()
    invite_token = get_invite_token(client, poll["id"], token)

    response = client.get(f"/event-polls/invite/{invite_token}")
    assert response.status_code == 200
    starts = [option["starts_at"] for option in response.json()["date_options"]]
    assert starts == sorted(starts)


def test_create_poll_requires_at_least_two_dates(client):
    token = register_and_login(client, "owner@example.com")
    response = create_poll(client, token, date_options=["2026-11-01T20:00:00Z"])
    assert response.status_code == 422


def test_create_poll_rejects_past_dates(client):
    token = register_and_login(client, "owner@example.com")
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    response = create_poll(client, token, date_options=[past, "2026-11-08T20:00:00Z"])
    assert response.status_code == 422


def test_create_poll_rejects_duplicate_dates(client):
    token = register_and_login(client, "owner@example.com")
    response = create_poll(
        client, token, date_options=["2026-11-01T20:00:00Z", "2026-11-01T20:00:00Z"]
    )
    assert response.status_code == 422


def test_get_invite_link_requires_owner(client):
    owner_token = register_and_login(client, "owner@example.com")
    stranger_token = register_and_login(client, "stranger@example.com")
    poll_id = create_poll(client, owner_token).json()["id"]

    response = client.get(f"/event-polls/{poll_id}/invite-link", headers=auth_headers(stranger_token))
    assert response.status_code == 403


def test_regenerate_invite_link_invalidates_old_token(client):
    owner_token = register_and_login(client, "owner@example.com")
    poll_id = create_poll(client, owner_token).json()["id"]
    old_token = get_invite_token(client, poll_id, owner_token)

    response = client.post(
        f"/event-polls/{poll_id}/invite-link/regenerate", headers=auth_headers(owner_token)
    )
    assert response.status_code == 200
    new_token = response.json()["invite_token"]
    assert new_token != old_token
    assert client.get(f"/event-polls/invite/{old_token}").status_code == 404
    assert client.get(f"/event-polls/invite/{new_token}").status_code == 200


def test_preview_invite_hides_voter_names_from_anonymous_viewers(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    option_id = poll["date_options"][0]["id"]

    client.post(
        f"/event-polls/invite/{token}/vote",
        json={"option_ids": [option_id]},
        headers=auth_headers(friend_token),
    )

    response = client.get(f"/event-polls/invite/{token}")
    assert response.status_code == 200
    body = response.json()
    voted_option = next(o for o in body["date_options"] if o["id"] == option_id)
    assert voted_option["vote_count"] == 1
    assert voted_option["voters"] == []


def test_preview_invite_shows_voter_names_to_logged_in_users(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    viewer_token = register_and_login(client, "viewer@example.com")
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    option_id = poll["date_options"][0]["id"]

    client.post(
        f"/event-polls/invite/{token}/vote",
        json={"option_ids": [option_id]},
        headers=auth_headers(friend_token),
    )

    response = client.get(f"/event-polls/invite/{token}", headers=auth_headers(viewer_token))
    assert response.status_code == 200
    voted_option = next(o for o in response.json()["date_options"] if o["id"] == option_id)
    assert [v["full_name"] for v in voted_option["voters"]] == ["Test User"]


def test_vote_by_invite_token(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    option_ids = [poll["date_options"][0]["id"], poll["date_options"][1]["id"]]

    response = client.post(
        f"/event-polls/invite/{token}/vote",
        json={"option_ids": option_ids},
        headers=auth_headers(friend_token),
    )
    assert response.status_code == 200
    body = response.json()
    voted = {o["id"]: o["voted_by_me"] for o in body["date_options"]}
    assert voted[option_ids[0]] is True
    assert voted[option_ids[1]] is True
    assert voted[poll["date_options"][2]["id"]] is False


def test_vote_rejects_option_from_another_poll(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    poll = create_poll(client, owner_token).json()
    other_poll = create_poll(client, owner_token, title="Otro plan").json()
    token = get_invite_token(client, poll["id"], owner_token)

    response = client.post(
        f"/event-polls/invite/{token}/vote",
        json={"option_ids": [other_poll["date_options"][0]["id"]]},
        headers=auth_headers(friend_token),
    )
    assert response.status_code == 422


def test_update_votes_replaces_previous_selection(client):
    owner_token = register_and_login(client, "owner@example.com")
    friend_token = register_and_login(client, "friend@example.com")
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    first_option, second_option = poll["date_options"][0]["id"], poll["date_options"][1]["id"]

    client.post(
        f"/event-polls/invite/{token}/vote",
        json={"option_ids": [first_option]},
        headers=auth_headers(friend_token),
    )
    response = client.put(
        f"/event-polls/{poll['id']}/date-options/votes",
        json={"option_ids": [second_option]},
        headers=auth_headers(friend_token),
    )
    assert response.status_code == 200
    voted = {o["id"]: o["voted_by_me"] for o in response.json()["date_options"]}
    assert voted[first_option] is False
    assert voted[second_option] is True


def test_list_polls_shows_owned_and_voted_hides_others(client):
    owner_token = register_and_login(client, "owner@example.com")
    voter_token = register_and_login(client, "voter@example.com")
    stranger_token = register_and_login(client, "stranger@example.com")
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    client.post(
        f"/event-polls/invite/{token}/vote",
        json={"option_ids": [poll["date_options"][0]["id"]]},
        headers=auth_headers(voter_token),
    )

    assert len(client.get("/event-polls", headers=auth_headers(owner_token)).json()) == 1
    assert len(client.get("/event-polls", headers=auth_headers(voter_token)).json()) == 1
    assert len(client.get("/event-polls", headers=auth_headers(stranger_token)).json()) == 0


def test_get_poll_requires_view_access(client):
    owner_token = register_and_login(client, "owner@example.com")
    stranger_token = register_and_login(client, "stranger@example.com")
    poll_id = create_poll(client, owner_token).json()["id"]

    response = client.get(f"/event-polls/{poll_id}", headers=auth_headers(stranger_token))
    assert response.status_code == 404


def test_resolve_requires_owner(client):
    owner_token = register_and_login(client, "owner@example.com")
    stranger_token = register_and_login(client, "stranger@example.com")
    poll = create_poll(client, owner_token).json()
    event_id = create_event(client, owner_token).json()["id"]

    response = client.post(
        f"/event-polls/{poll['id']}/resolve",
        json={"resulting_event_id": event_id, "date_option_id": poll["date_options"][0]["id"]},
        headers=auth_headers(stranger_token),
    )
    assert response.status_code == 403


def test_resolve_rejects_event_not_owned_by_caller(client):
    owner_token = register_and_login(client, "owner@example.com")
    other_token = register_and_login(client, "other@example.com")
    poll = create_poll(client, owner_token).json()
    other_event_id = create_event(client, other_token).json()["id"]

    response = client.post(
        f"/event-polls/{poll['id']}/resolve",
        json={"resulting_event_id": other_event_id, "date_option_id": poll["date_options"][0]["id"]},
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 422


def test_resolve_rejects_date_option_from_another_poll(client):
    owner_token = register_and_login(client, "owner@example.com")
    poll = create_poll(client, owner_token).json()
    other_poll = create_poll(client, owner_token, title="Otro plan").json()
    event_id = create_event(client, owner_token).json()["id"]

    response = client.post(
        f"/event-polls/{poll['id']}/resolve",
        json={"resulting_event_id": event_id, "date_option_id": other_poll["date_options"][0]["id"]},
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 422


def test_resolve_success_hides_poll_from_pending_list(client):
    owner_token = register_and_login(client, "owner@example.com")
    voter_token = register_and_login(client, "voter@example.com")
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    chosen_option = poll["date_options"][0]["id"]
    client.post(
        f"/event-polls/invite/{token}/vote",
        json={"option_ids": [chosen_option]},
        headers=auth_headers(voter_token),
    )
    event_id = create_event(
        client, owner_token, starts_at=poll["date_options"][0]["starts_at"]
    ).json()["id"]

    response = client.post(
        f"/event-polls/{poll['id']}/resolve",
        json={"resulting_event_id": event_id, "date_option_id": chosen_option},
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 200
    assert response.json()["resulting_event_id"] == event_id

    assert client.get("/event-polls", headers=auth_headers(owner_token)).json() == []
    assert client.get("/event-polls", headers=auth_headers(voter_token)).json() == []


def test_resolve_adds_voters_of_chosen_option_as_attendees(client):
    owner_token = register_and_login(client, "owner@example.com")
    chosen_voter_token = register_and_login(client, "chosen-voter@example.com")
    other_voter_token = register_and_login(client, "other-voter@example.com")
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    chosen_option, other_option = poll["date_options"][0]["id"], poll["date_options"][1]["id"]

    client.post(
        f"/event-polls/invite/{token}/vote",
        json={"option_ids": [chosen_option]},
        headers=auth_headers(chosen_voter_token),
    )
    client.post(
        f"/event-polls/invite/{token}/vote",
        json={"option_ids": [other_option]},
        headers=auth_headers(other_voter_token),
    )
    chosen_voter_id = client.get("/users/me", headers=auth_headers(chosen_voter_token)).json()["id"]
    other_voter_id = client.get("/users/me", headers=auth_headers(other_voter_token)).json()["id"]

    event_id = create_event(
        client, owner_token, starts_at=poll["date_options"][0]["starts_at"]
    ).json()["id"]
    resolve_response = client.post(
        f"/event-polls/{poll['id']}/resolve",
        json={"resulting_event_id": event_id, "date_option_id": chosen_option},
        headers=auth_headers(owner_token),
    )
    assert resolve_response.status_code == 200

    attendees = client.get(f"/events/{event_id}/attendees", headers=auth_headers(owner_token)).json()
    attendee_ids = {a["user_id"] for a in attendees if not a["is_owner"]}
    assert chosen_voter_id in attendee_ids
    assert other_voter_id not in attendee_ids


def test_resolve_notifies_all_voters_regardless_of_chosen_option(client):
    owner_token = register_and_login(client, "owner@example.com")
    chosen_voter_token = register_and_login(client, "chosen-voter@example.com")
    other_voter_token = register_and_login(client, "other-voter@example.com")
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    chosen_option, other_option = poll["date_options"][0]["id"], poll["date_options"][1]["id"]

    client.post(
        f"/event-polls/invite/{token}/vote",
        json={"option_ids": [chosen_option]},
        headers=auth_headers(chosen_voter_token),
    )
    client.post(
        f"/event-polls/invite/{token}/vote",
        json={"option_ids": [other_option]},
        headers=auth_headers(other_voter_token),
    )
    chosen_voter_id = client.get("/users/me", headers=auth_headers(chosen_voter_token)).json()["id"]
    other_voter_id = client.get("/users/me", headers=auth_headers(other_voter_token)).json()["id"]

    event_id = create_event(
        client, owner_token, starts_at=poll["date_options"][0]["starts_at"]
    ).json()["id"]

    with patch("app.routers.event_polls.push.send_push_to_user") as mock_send:
        response = client.post(
            f"/event-polls/{poll['id']}/resolve",
            json={"resulting_event_id": event_id, "date_option_id": chosen_option},
            headers=auth_headers(owner_token),
        )
    assert response.status_code == 200
    notified_user_ids = {call.args[1] for call in mock_send.call_args_list}
    assert notified_user_ids == {chosen_voter_id, other_voter_id}
    for call in mock_send.call_args_list:
        payload = call.args[2]
        assert EVENT_PAYLOAD["title"] in payload["body"]
        assert payload["url"] == f"/events/{event_id}"


def test_resolve_push_localized_per_recipient_language(client):
    owner_token = register_and_login(client, "owner@example.com")
    es_voter_token = register_and_login(client, "es-voter@example.com")
    en_voter_token = register_and_login(client, "en-voter@example.com")
    client.patch("/users/me", json={"language": "en"}, headers=auth_headers(en_voter_token))
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    chosen_option = poll["date_options"][0]["id"]

    for voter_token in (es_voter_token, en_voter_token):
        client.post(
            f"/event-polls/invite/{token}/vote",
            json={"option_ids": [chosen_option]},
            headers=auth_headers(voter_token),
        )
    es_voter_id = client.get("/users/me", headers=auth_headers(es_voter_token)).json()["id"]
    en_voter_id = client.get("/users/me", headers=auth_headers(en_voter_token)).json()["id"]

    event_id = create_event(
        client, owner_token, starts_at=poll["date_options"][0]["starts_at"]
    ).json()["id"]

    with patch("app.routers.event_polls.push.send_push_to_user") as mock_send:
        client.post(
            f"/event-polls/{poll['id']}/resolve",
            json={"resulting_event_id": event_id, "date_option_id": chosen_option},
            headers=auth_headers(owner_token),
        )

    payloads_by_user = {call.args[1]: call.args[2] for call in mock_send.call_args_list}
    assert payloads_by_user[es_voter_id]["title"] == "Se confirmó la fecha"
    assert payloads_by_user[en_voter_id]["title"] == "Date confirmed"
    assert "is confirmed for" in payloads_by_user[en_voter_id]["body"]


def test_resolve_twice_rejected(client):
    owner_token = register_and_login(client, "owner@example.com")
    poll = create_poll(client, owner_token).json()
    event_id = create_event(client, owner_token).json()["id"]
    body = {"resulting_event_id": event_id, "date_option_id": poll["date_options"][0]["id"]}

    first = client.post(
        f"/event-polls/{poll['id']}/resolve", json=body, headers=auth_headers(owner_token)
    )
    assert first.status_code == 200

    second = client.post(
        f"/event-polls/{poll['id']}/resolve", json=body, headers=auth_headers(owner_token)
    )
    assert second.status_code == 409


def test_vote_after_resolve_rejected(client):
    owner_token = register_and_login(client, "owner@example.com")
    voter_token = register_and_login(client, "voter@example.com")
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    option_id = poll["date_options"][0]["id"]
    client.post(
        f"/event-polls/invite/{token}/vote",
        json={"option_ids": [option_id]},
        headers=auth_headers(voter_token),
    )
    event_id = create_event(client, owner_token).json()["id"]
    client.post(
        f"/event-polls/{poll['id']}/resolve",
        json={"resulting_event_id": event_id, "date_option_id": option_id},
        headers=auth_headers(owner_token),
    )

    response = client.put(
        f"/event-polls/{poll['id']}/date-options/votes",
        json={"option_ids": [poll["date_options"][1]["id"]]},
        headers=auth_headers(voter_token),
    )
    assert response.status_code == 409


def vote(client, token, voter_token, option_ids):
    return client.post(
        f"/event-polls/invite/{token}/vote",
        json={"option_ids": option_ids},
        headers=auth_headers(voter_token),
    )


def update_poll(client, poll_id, token, **overrides):
    payload = {**POLL_PAYLOAD, **overrides}
    return client.patch(f"/event-polls/{poll_id}", json=payload, headers=auth_headers(token))


def test_update_poll_requires_owner(client):
    owner_token = register_and_login(client, "owner@example.com")
    other_token = register_and_login(client, "other@example.com")
    poll = create_poll(client, owner_token).json()
    response = update_poll(client, poll["id"], other_token, title="Hackeado")
    assert response.status_code == 403
    assert client.get(f"/event-polls/{poll['id']}", headers=auth_headers(owner_token)).json()["title"] == (
        POLL_PAYLOAD["title"]
    )


def test_update_poll_not_found(client):
    token = register_and_login(client, "owner@example.com")
    assert update_poll(client, 9999, token).status_code == 404


def test_update_poll_changes_fields(client):
    token = register_and_login(client, "owner@example.com")
    poll = create_poll(client, token).json()
    response = update_poll(
        client,
        poll["id"],
        token,
        title="Cumple",
        description=None,
        location="Casa",
        duration_minutes=60,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Cumple"
    assert body["description"] is None
    assert body["location"] == "Casa"
    assert body["duration_minutes"] == 60


def test_update_poll_keeps_votes_on_kept_dates_and_drops_votes_on_removed_ones(client):
    owner_token = register_and_login(client, "owner@example.com")
    voter_token = register_and_login(client, "voter@example.com")
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    kept, removed = poll["date_options"][0], poll["date_options"][1]
    vote(client, token, voter_token, [kept["id"], removed["id"]])

    response = update_poll(
        client,
        poll["id"],
        owner_token,
        date_options=[kept["starts_at"], "2026-12-01T20:00:00Z"],
    )
    assert response.status_code == 200
    options = response.json()["date_options"]
    assert len(options) == 2

    by_start = {o["starts_at"]: o for o in options}
    assert by_start[kept["starts_at"]]["id"] == kept["id"]
    assert len(by_start[kept["starts_at"]]["voters"]) == 1
    new_option = next(o for o in options if o["id"] != kept["id"])
    assert new_option["voters"] == []

    # The voter still sees only the vote on the kept date.
    voter_view = client.get(f"/event-polls/{poll['id']}", headers=auth_headers(voter_token)).json()
    assert [o["id"] for o in voter_view["date_options"] if o["voted_by_me"]] == [kept["id"]]


def test_update_poll_keeps_invite_link(client):
    token = register_and_login(client, "owner@example.com")
    poll = create_poll(client, token).json()
    invite_before = get_invite_token(client, poll["id"], token)
    update_poll(client, poll["id"], token, title="Nuevo nombre")
    assert get_invite_token(client, poll["id"], token) == invite_before


def test_update_poll_validates_dates(client):
    token = register_and_login(client, "owner@example.com")
    poll = create_poll(client, token).json()
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    assert update_poll(client, poll["id"], token, date_options=["2026-12-01T20:00:00Z"]).status_code == 422
    assert update_poll(
        client, poll["id"], token, date_options=["2026-12-01T20:00:00Z", past]
    ).status_code == 422
    assert update_poll(
        client, poll["id"], token, date_options=["2026-12-01T20:00:00Z", "2026-12-01T20:00:00Z"]
    ).status_code == 422
    assert len(client.get(f"/event-polls/{poll['id']}", headers=auth_headers(token)).json()["date_options"]) == 3


def test_update_resolved_poll_rejected(client):
    owner_token = register_and_login(client, "owner@example.com")
    poll = create_poll(client, owner_token).json()
    event_id = create_event(client, owner_token).json()["id"]
    client.post(
        f"/event-polls/{poll['id']}/resolve",
        json={"resulting_event_id": event_id, "date_option_id": poll["date_options"][0]["id"]},
        headers=auth_headers(owner_token),
    )
    assert update_poll(client, poll["id"], owner_token, title="Tarde").status_code == 409


def test_update_poll_notifies_voters_not_owner_via_invite_link(client):
    owner_token = register_and_login(client, "owner@example.com")
    voter_token = register_and_login(client, "voter@example.com")
    register_and_login(client, "silent@example.com")  # never votes, so must not be notified
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    vote(client, token, voter_token, [poll["date_options"][0]["id"]])
    voter_id = client.get("/users/me", headers=auth_headers(voter_token)).json()["id"]

    with patch("app.routers.event_polls.push.send_push_to_user") as mock_send:
        response = update_poll(client, poll["id"], owner_token, title="Cumple")
    assert response.status_code == 200
    assert [call.args[1] for call in mock_send.call_args_list] == [voter_id]
    payload = mock_send.call_args_list[0].args[2]
    assert "Cumple" in payload["body"]
    assert payload["url"] == f"/polls/invite/{token}"


def test_update_poll_notifies_voter_whose_only_date_was_removed(client):
    owner_token = register_and_login(client, "owner@example.com")
    voter_token = register_and_login(client, "voter@example.com")
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    dropped = poll["date_options"][1]
    vote(client, token, voter_token, [dropped["id"]])
    voter_id = client.get("/users/me", headers=auth_headers(voter_token)).json()["id"]

    with patch("app.routers.event_polls.push.send_push_to_user") as mock_send:
        update_poll(
            client,
            poll["id"],
            owner_token,
            date_options=[poll["date_options"][0]["starts_at"], poll["date_options"][2]["starts_at"]],
        )
    assert [call.args[1] for call in mock_send.call_args_list] == [voter_id]
    # With no votes left the voter can't open the poll page anymore, but the invite link still works.
    assert client.get(f"/event-polls/{poll['id']}", headers=auth_headers(voter_token)).status_code == 404
    assert client.get(f"/event-polls/invite/{token}", headers=auth_headers(voter_token)).status_code == 200


def test_update_poll_notify_voters_false_skips_push(client):
    owner_token = register_and_login(client, "owner@example.com")
    voter_token = register_and_login(client, "voter@example.com")
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    vote(client, token, voter_token, [poll["date_options"][0]["id"]])

    with patch("app.routers.event_polls.push.send_push_to_user") as mock_send:
        response = update_poll(client, poll["id"], owner_token, title="Cumple", notify_voters=False)
    assert response.status_code == 200
    mock_send.assert_not_called()


def test_delete_poll_requires_owner(client):
    owner_token = register_and_login(client, "owner@example.com")
    other_token = register_and_login(client, "other@example.com")
    poll = create_poll(client, owner_token).json()
    response = client.delete(f"/event-polls/{poll['id']}", headers=auth_headers(other_token))
    assert response.status_code == 403
    assert client.get(f"/event-polls/{poll['id']}", headers=auth_headers(owner_token)).status_code == 200


def test_delete_poll_not_found(client):
    token = register_and_login(client, "owner@example.com")
    assert client.delete("/event-polls/9999", headers=auth_headers(token)).status_code == 404


def test_delete_poll_removes_it_votes_and_invite_link(client):
    owner_token = register_and_login(client, "owner@example.com")
    voter_token = register_and_login(client, "voter@example.com")
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    vote(client, token, voter_token, [poll["date_options"][0]["id"]])

    response = client.delete(f"/event-polls/{poll['id']}", headers=auth_headers(owner_token))
    assert response.status_code == 204

    assert client.get(f"/event-polls/{poll['id']}", headers=auth_headers(owner_token)).status_code == 404
    assert client.get(f"/event-polls/invite/{token}").status_code == 404
    assert client.get("/event-polls", headers=auth_headers(owner_token)).json() == []
    assert client.get("/event-polls", headers=auth_headers(voter_token)).json() == []


def test_delete_poll_notifies_voters_not_owner(client):
    owner_token = register_and_login(client, "owner@example.com")
    voter_token = register_and_login(client, "voter@example.com")
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    vote(client, token, voter_token, [poll["date_options"][0]["id"], poll["date_options"][1]["id"]])
    voter_id = client.get("/users/me", headers=auth_headers(voter_token)).json()["id"]

    with patch("app.routers.event_polls.push.send_push_to_user") as mock_send:
        response = client.delete(f"/event-polls/{poll['id']}", headers=auth_headers(owner_token))
    assert response.status_code == 204
    # One voter on two dates is notified once.
    assert [call.args[1] for call in mock_send.call_args_list] == [voter_id]
    payload = mock_send.call_args_list[0].args[2]
    assert POLL_PAYLOAD["title"] in payload["body"]
    assert payload["url"] == "/events"


def test_delete_resolved_poll_keeps_event_and_skips_push(client):
    owner_token = register_and_login(client, "owner@example.com")
    voter_token = register_and_login(client, "voter@example.com")
    poll = create_poll(client, owner_token).json()
    token = get_invite_token(client, poll["id"], owner_token)
    option_id = poll["date_options"][0]["id"]
    vote(client, token, voter_token, [option_id])
    event_id = create_event(client, owner_token).json()["id"]
    client.post(
        f"/event-polls/{poll['id']}/resolve",
        json={"resulting_event_id": event_id, "date_option_id": option_id},
        headers=auth_headers(owner_token),
    )

    with patch("app.routers.event_polls.push.send_push_to_user") as mock_send:
        response = client.delete(f"/event-polls/{poll['id']}", headers=auth_headers(owner_token))
    assert response.status_code == 204
    mock_send.assert_not_called()
    assert client.get(f"/events/{event_id}", headers=auth_headers(owner_token)).status_code == 200
