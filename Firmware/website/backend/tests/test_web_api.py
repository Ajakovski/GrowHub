"""Dashboard/web endpoint smoke tests."""


def test_catalog_tiles_are_public(client):
    response = client.get("/api/web/tiles")
    assert response.status_code == 200
    tiles = response.json()
    assert isinstance(tiles, list)
    assert any(tile.get("id") == "growhub_hub" for tile in tiles)


def test_history_requires_session(client):
    assert client.get("/api/web/history").status_code == 401
    client.post("/api/auth/demo")
    ok = client.get("/api/web/history", params={"range": "1h"})
    assert ok.status_code == 200


def test_plant_catalog_requires_session(client):
    assert client.get("/api/web/plant-catalog").status_code == 401
    client.post("/api/auth/demo")
    ok = client.get("/api/web/plant-catalog")
    assert ok.status_code == 200
    assert "plants" in ok.json()


def test_plant_stats_unknown_hub_is_404(client):
    client.post("/api/auth/demo")
    response = client.get("/api/web/plant-stats", params={"hub": "hub_does_not_exist"})
    assert response.status_code == 404


def test_contact_honeypot_looks_successful(client):
    response = client.post(
        "/api/web/contact",
        json={
            "name": "Bot",
            "email": "bot@example.com",
            "topic": "Spam",
            "message": "Buy followers now please",
            "company": "Acme SEO",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "sent"


def test_contact_sends_without_resend_key(client, monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    response = client.post(
        "/api/web/contact",
        json={
            "name": "Andrej",
            "email": "andrej@example.com",
            "topic": "Pilot",
            "message": "Interested in a greenhouse pilot next quarter.",
            "company": "",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "sent"


def test_contact_rejects_short_message(client):
    response = client.post(
        "/api/web/contact",
        json={
            "name": "Andrej",
            "email": "andrej@example.com",
            "topic": "Hi",
            "message": "too short",
            "company": "",
        },
    )
    assert response.status_code == 422
