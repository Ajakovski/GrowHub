"""Register / login / verify smoke tests."""


def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "live" in response.json()["status"].lower()


def test_me_requires_login(client):
    assert client.get("/api/auth/me").status_code == 401


def test_register_then_unverified_login_blocked(client):
    created = client.post(
        "/api/auth/register",
        json={"email": "grower@example.com", "password": "password123"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["email"] == "grower@example.com"
    assert "email_sent" in body

    login = client.post(
        "/api/auth/login",
        json={"email": "grower@example.com", "password": "password123"},
    )
    assert login.status_code == 403


def test_register_rejects_duplicate_email(client):
    payload = {"email": "twice@example.com", "password": "password123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    again = client.post("/api/auth/register", json=payload)
    assert again.status_code == 409


def test_register_rejects_demo_email(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "demo@growhub.local", "password": "password123"},
    )
    assert response.status_code == 409


def test_login_rejects_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"email": "wrongpass@example.com", "password": "password123"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "wrongpass@example.com", "password": "not-the-password"},
    )
    assert response.status_code == 401


def test_verify_rejects_bogus_token(client):
    response = client.post("/api/auth/verify", json={"token": "not-a-real-token"})
    assert response.status_code == 400


def test_logout_without_session_is_ok(client):
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json()["status"] == "logged out"
