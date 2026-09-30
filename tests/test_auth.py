from datetime import datetime, timedelta, timezone

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
