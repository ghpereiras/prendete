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
