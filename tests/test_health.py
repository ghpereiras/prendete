def test_health_responds_to_get_and_head(client):
    get_response = client.get("/health")
    assert get_response.status_code == 200
    assert get_response.json() == {"status": "ok"}

    head_response = client.head("/health")
    assert head_response.status_code == 200
    assert head_response.content == b""
