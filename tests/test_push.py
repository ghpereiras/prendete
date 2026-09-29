from unittest.mock import MagicMock, patch

from pywebpush import WebPushException

from app.models.push_subscription import PushSubscription
from app.models.user import User
from app.push import send_push_to_user
from tests.conftest import auth_headers, register_and_login

SUBSCRIPTION_PAYLOAD = {
    "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint",
    "keys": {"p256dh": "test-p256dh", "auth": "test-auth"},
}


def test_create_push_subscription_requires_auth(client):
    response = client.post("/users/me/push-subscriptions", json=SUBSCRIPTION_PAYLOAD)
    assert response.status_code == 401


def test_create_push_subscription_success(client, db_session):
    token = register_and_login(client, "owner@example.com")
    response = client.post(
        "/users/me/push-subscriptions", json=SUBSCRIPTION_PAYLOAD, headers=auth_headers(token)
    )
    assert response.status_code == 204
    assert db_session.query(PushSubscription).count() == 1


def test_create_push_subscription_upserts_same_endpoint(client, db_session):
    token = register_and_login(client, "owner@example.com")
    client.post("/users/me/push-subscriptions", json=SUBSCRIPTION_PAYLOAD, headers=auth_headers(token))

    updated_payload = {**SUBSCRIPTION_PAYLOAD, "keys": {"p256dh": "new-p256dh", "auth": "new-auth"}}
    client.post("/users/me/push-subscriptions", json=updated_payload, headers=auth_headers(token))

    rows = db_session.query(PushSubscription).filter_by(endpoint=SUBSCRIPTION_PAYLOAD["endpoint"]).all()
    assert len(rows) == 1
    assert rows[0].p256dh == "new-p256dh"


def test_delete_push_subscription(client, db_session):
    token = register_and_login(client, "owner@example.com")
    client.post("/users/me/push-subscriptions", json=SUBSCRIPTION_PAYLOAD, headers=auth_headers(token))

    response = client.delete(
        "/users/me/push-subscriptions",
        params={"endpoint": SUBSCRIPTION_PAYLOAD["endpoint"]},
        headers=auth_headers(token),
    )
    assert response.status_code == 204
    assert db_session.query(PushSubscription).count() == 0


def test_delete_push_subscription_requires_auth(client):
    response = client.delete(
        "/users/me/push-subscriptions", params={"endpoint": SUBSCRIPTION_PAYLOAD["endpoint"]}
    )
    assert response.status_code == 401


def test_send_push_to_user_calls_webpush_for_each_subscription(client, db_session):
    register_and_login(client, "owner@example.com")
    user = db_session.query(User).filter_by(email="owner@example.com").first()
    db_session.add(PushSubscription(user_id=user.id, endpoint="https://example.com/ep1", p256dh="p", auth="a"))
    db_session.commit()

    with patch("app.push.webpush") as mock_webpush:
        send_push_to_user(db_session, user.id, {"title": "Hola", "body": "Mundo"})

    mock_webpush.assert_called_once()
    assert mock_webpush.call_args.kwargs["subscription_info"]["endpoint"] == "https://example.com/ep1"
    # A subscriber who's offline right now should still get it once they
    # reconnect — pywebpush defaults to ttl=0 (drop if not connected right
    # now), so this must be passed explicitly.
    assert mock_webpush.call_args.kwargs["ttl"] > 0


def test_send_push_to_user_removes_subscription_invalidated_by_push_service(client, db_session):
    register_and_login(client, "owner@example.com")
    user = db_session.query(User).filter_by(email="owner@example.com").first()
    db_session.add(
        PushSubscription(user_id=user.id, endpoint="https://example.com/ep-dead", p256dh="p", auth="a")
    )
    db_session.commit()

    gone_response = MagicMock(status_code=410)
    with patch("app.push.webpush", side_effect=WebPushException("gone", response=gone_response)):
        send_push_to_user(db_session, user.id, {"title": "Hola", "body": "Mundo"})

    assert db_session.query(PushSubscription).filter_by(endpoint="https://example.com/ep-dead").count() == 0


def test_send_push_to_user_keeps_subscription_on_transient_error(client, db_session):
    register_and_login(client, "owner@example.com")
    user = db_session.query(User).filter_by(email="owner@example.com").first()
    db_session.add(
        PushSubscription(user_id=user.id, endpoint="https://example.com/ep-flaky", p256dh="p", auth="a")
    )
    db_session.commit()

    server_error_response = MagicMock(status_code=500)
    with patch("app.push.webpush", side_effect=WebPushException("boom", response=server_error_response)):
        send_push_to_user(db_session, user.id, {"title": "Hola", "body": "Mundo"})

    assert db_session.query(PushSubscription).filter_by(endpoint="https://example.com/ep-flaky").count() == 1
