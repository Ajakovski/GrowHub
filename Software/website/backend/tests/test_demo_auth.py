"""Smoke tests for the public guest-demo path and create-account handoff."""

from routers.auth import SESSION_COOKIE


def test_demo_starts_guest_session(client):
    response = client.post("/api/auth/demo")
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "demo@growhub.local"
    assert body["is_demo"] is True
    assert SESSION_COOKIE in response.cookies


def test_demo_refresh_keeps_working(client):
    first = client.post("/api/auth/demo")
    assert first.status_code == 200
    second = client.post("/api/auth/demo")
    assert second.status_code == 200
    assert second.json()["is_demo"] is True


def test_me_reports_demo_flag(client):
    client.post("/api/auth/demo")
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json() == {"email": "demo@growhub.local", "is_demo": True}


def test_plant_stats_requires_session(client):
    denied = client.get("/api/web/plant-stats")
    assert denied.status_code == 401

    client.post("/api/auth/demo")
    ok = client.get("/api/web/plant-stats")
    assert ok.status_code == 200
    body = ok.json()
    assert "hub_online" in body
    assert "tiles" in body


def test_demo_onboarding_is_already_complete(client):
    client.post("/api/auth/demo")
    onboard = client.get("/api/auth/onboarding")
    assert onboard.status_code == 200
    assert onboard.json()["completed"] is True


def test_logout_clears_demo_session(client):
    client.post("/api/auth/demo")
    assert client.get("/api/auth/me").status_code == 200

    logged_out = client.post("/api/auth/logout")
    assert logged_out.status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/web/plant-stats").status_code == 401


def test_cannot_password_login_as_demo(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "demo@growhub.local", "password": "anything-long-enough"},
    )
    assert response.status_code == 401
