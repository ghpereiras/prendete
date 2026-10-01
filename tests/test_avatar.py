import base64
import io

import pytest
from PIL import Image

from app.utils.avatar import AVATAR_SIZE, InvalidAvatarError, process_avatar
from tests.conftest import auth_headers, login, register


def _sample_image_base64(size: tuple[int, int] = (300, 200), color=(200, 50, 50)) -> str:
    image = Image.new("RGB", size, color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"


def test_process_avatar_rejects_invalid_base64():
    with pytest.raises(InvalidAvatarError):
        process_avatar("!!!not-base64!!!")


def test_process_avatar_rejects_non_image_data():
    with pytest.raises(InvalidAvatarError):
        process_avatar(base64.b64encode(b"hello world").decode())


def test_process_avatar_rejects_oversized_payload():
    huge = base64.b64encode(b"0" * (9 * 1024 * 1024)).decode()
    with pytest.raises(InvalidAvatarError):
        process_avatar(huge)


def test_process_avatar_normalizes_to_square_jpeg():
    result = process_avatar(_sample_image_base64(size=(800, 400)))
    image = Image.open(io.BytesIO(result))
    assert image.size == (AVATAR_SIZE, AVATAR_SIZE)
    assert image.format == "JPEG"


def test_register_without_avatar_has_no_avatar_url(client):
    response = register(client, "owner@example.com")
    assert response.status_code == 201
    assert response.json()["avatar_url"] is None


def test_register_with_avatar_stores_and_serves_it(client):
    response = client.post(
        "/users",
        json={
            "email": "owner@example.com",
            "first_name": "Owner",
            "last_name": "Test",
            "password": "secret123",
            "avatar_base64": _sample_image_base64(),
        },
    )
    assert response.status_code == 201
    body = response.json()
    user_id = body["id"]
    assert body["avatar_url"].startswith(f"/users/{user_id}/avatar?v=")

    token = login(client, "owner@example.com")
    avatar_response = client.get(f"/users/{user_id}/avatar", headers=auth_headers(token))
    assert avatar_response.status_code == 200
    assert avatar_response.headers["content-type"] == "image/jpeg"

    stored_image = Image.open(io.BytesIO(avatar_response.content))
    assert stored_image.size == (AVATAR_SIZE, AVATAR_SIZE)


def test_register_with_invalid_avatar_rejected(client):
    response = client.post(
        "/users",
        json={
            "email": "owner@example.com",
            "first_name": "Owner",
            "last_name": "Test",
            "password": "secret123",
            "avatar_base64": "!!!not-a-valid-image!!!",
        },
    )
    assert response.status_code == 422


def test_avatar_not_found_for_user_without_one(client):
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    me = client.get("/users/me", headers=auth_headers(token)).json()

    response = client.get(f"/users/{me['id']}/avatar", headers=auth_headers(token))
    assert response.status_code == 404


def test_update_me_requires_auth(client):
    response = client.patch("/users/me", json={"full_name": "New Name"})
    assert response.status_code == 401


def test_update_me_changes_full_name(client):
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")

    response = client.patch(
        "/users/me", json={"first_name": "New", "last_name": "Name"}, headers=auth_headers(token)
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "New Name"


def test_update_me_sets_avatar(client):
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")

    response = client.patch(
        "/users/me",
        json={"avatar_base64": _sample_image_base64()},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["avatar_url"].startswith(f"/users/{body['id']}/avatar?v=")

    avatar_response = client.get(body["avatar_url"], headers=auth_headers(token))
    stored_image = Image.open(io.BytesIO(avatar_response.content))
    assert stored_image.size == (AVATAR_SIZE, AVATAR_SIZE)


def test_update_me_replaces_existing_avatar(client):
    client.post(
        "/users",
        json={
            "email": "owner@example.com",
            "first_name": "Owner",
            "last_name": "Test",
            "password": "secret123",
            "avatar_base64": _sample_image_base64(color=(10, 10, 10)),
        },
    )
    token = login(client, "owner@example.com")

    response = client.patch(
        "/users/me",
        json={"avatar_base64": _sample_image_base64(color=(240, 240, 240))},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    avatar_response = client.get(response.json()["avatar_url"], headers=auth_headers(token))
    pixel = Image.open(io.BytesIO(avatar_response.content)).getpixel((128, 128))
    assert pixel[0] > 200  # replaced with the light image, not the dark original


def test_avatar_url_changes_when_avatar_content_changes(client):
    # The endpoint is cached for 24h client-side — if the URL stayed the same
    # after replacing the avatar, browsers would keep serving the old image
    # from cache instead of fetching the new one.
    register_response = client.post(
        "/users",
        json={
            "email": "owner@example.com",
            "first_name": "Owner",
            "last_name": "Test",
            "password": "secret123",
            "avatar_base64": _sample_image_base64(color=(10, 10, 10)),
        },
    )
    original_url = register_response.json()["avatar_url"]
    token = login(client, "owner@example.com")

    response = client.patch(
        "/users/me",
        json={"avatar_base64": _sample_image_base64(color=(240, 240, 240))},
        headers=auth_headers(token),
    )
    assert response.json()["avatar_url"] != original_url


def test_update_me_removes_avatar(client):
    client.post(
        "/users",
        json={
            "email": "owner@example.com",
            "first_name": "Owner",
            "last_name": "Test",
            "password": "secret123",
            "avatar_base64": _sample_image_base64(),
        },
    )
    token = login(client, "owner@example.com")

    response = client.patch(
        "/users/me", json={"remove_avatar": True}, headers=auth_headers(token)
    )
    assert response.status_code == 200
    assert response.json()["avatar_url"] is None


def test_update_me_with_invalid_avatar_rejected(client):
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")

    response = client.patch(
        "/users/me",
        json={"avatar_base64": "!!!not-a-valid-image!!!"},
        headers=auth_headers(token),
    )
    assert response.status_code == 422


def test_update_me_without_fields_leaves_user_unchanged(client):
    register(client, "owner@example.com", first_name="Original", last_name="Name")
    token = login(client, "owner@example.com")

    response = client.patch("/users/me", json={}, headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["full_name"] == "Original Name"
