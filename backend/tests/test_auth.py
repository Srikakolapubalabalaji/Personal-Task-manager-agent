def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "password": "password123", "full_name": "New User"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@example.com"


def test_login_user(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_get_me(client, auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "testuser@example.com"


def test_google_oauth_url(client):
    response = client.get("/api/v1/auth/google/url")
    assert response.status_code == 200
    assert "auth_url" in response.json()


def test_google_mock_auth(client):
    response = client.post("/api/v1/auth/google/mock")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "google" in data["user"]["email"].lower()

