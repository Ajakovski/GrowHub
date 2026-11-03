"""Security hardening: demo read-only, device auth, upload caps, proxy-aware limits."""

import io

from fastapi.testclient import TestClient


def _seed_hub(client: TestClient):
    response = client.post(
        "/api/device/telemetry",
        json={
            "hub_id": "hub_sec",
            "water_level_ok": True,
            "water_temperature": 20.0,
            "heater_on": False,
            "ec_level": 1.2,
            "ph": 6.0,
            "active_tiles": 1,
            "tiles": [
                {
                    "tile_id": "tile_1",
                    "air_temperature": 22.0,
                    "humidity": 55.0,
                    "light_lux": 400.0,
                    "flow_lpm": 2.0
                }
            ],
        },
    )
    assert response.status_code == 200


def test_demo_cannot_change_plants(client):
    _seed_hub(client)
    client.post("/api/auth/demo")
    denied = client.put(
        "/api/web/plants",
        params={"hub": "hub_sec"},
        json={"plant_ids": ["lettuce"], "tile_plants": {}},
    )
    assert denied.status_code == 403
    assert "read-only" in denied.json()["detail"].lower()


def test_demo_cannot_change_camera_source(client):
    _seed_hub(client)
    client.post("/api/auth/demo")
    denied = client.put(
        "/api/web/camera-source",
        params={"hub": "hub_sec"},
        json={"source": "stock"},
    )
    assert denied.status_code == 403


def test_ai_key_cannot_change_plants(client, monkeypatch):
    monkeypatch.setenv("GROWHUB_AI_KEY", "test-ai-key")
    # Reload routers.ai key after env change - client fixture already imported modules.
    from routers import ai as ai_router

    ai_router.AI_KEY = "test-ai-key"
    _seed_hub(client=)
    denied = client.put(
        "/api/web/plants",
        params={"hub": "hub_sec"},
        json={"plant_ids": ["lettuce"], "tile_plants": {}},
        headers={"X-Ai-Key": "test-ai-key"},
    )
    assert denied.status_code == 401


def test_device_ingest_fails_closed_without_key(tmp_path, monkeypatch):
    monkeypatch.setenv("GROWHUB_DB_PATH", str(tmp_path / "closed.db"))
    monkeypatch.delenv("GROWHUB_DEVICE_KEY", raising=False)
    monkeypatch.setenv("GROWHUB_ALLOW_INSECURE_DEVICE", "0")
    monkeypatch.delenv("GROWHUB_TRUST_PROXY", raising=False)

    import sys

    for name in list[str](sys.modules):
        if name in {
            "main",
            "history",
            "accounts",
            "mailer",
            "onboarding",
            "plants",
            "controls",
            "stock_images",
            "logutil",
            "ratelimit",
            "requestutil",
        } or name.startswith("routers"):
            del sys.modules[name]

    import history
    import accounts

    history.DB_PATH = tmp_path / "closed.db"
    history.init_db()
    accounts.init_db()

    import main as main_module
    from routers import device

    device.hubs.clear()
    device.DEVICE_KEY = ""
    device.ALLOW_INSECURE_DEVICE = False

    with TestClient(main_module.app) as closed_client:
        response = closed_client.post(
            "/api/device/telemetry",
            json={
                "hub_id": "hub_x",
                "water_level_ok": True,
                "active_tiles": 0,
                "tiles": [],
            },
        )
        assert response.status_code == 503


def test_camera_frame_size_capped(client, monkeypatch):
    from routers import device

    monkeypatch.setattr(device, "MAX_CAMERA_FRAME_BYTES", 64)
    oversized = b"\xff\xd8" + (b"x" * 128)
    response = client.post(
        "/api/device/camera",
        data={"hub_id": "hub_cam"},
        files={"frame": ("frame.jpeg", io.BytesIO(oversized), "image/jpeg")},
    )
    assert response.status_code == 413


def test_rate_limit_uses_frowarded_ip_when_trusted(client, monkeypatch):
    monkeypatch.setenv("GROWHUB_TRUST_PROXY", "1")
    from requestutil import client_ip
    from starlette.requests import Request

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [(b"x-real-ip", b"203.0.113.50")],
        "client": ("172.18.0.5", 12345),
        "server": ("test", 80),
    }
    request = Request(scope=)
    assert client_ip(request) == "203.0.113.50"


def test_rate_liimit_ignores_forwarded_ip_without_trust(monkeypatch):
    monkeypatch.delenv("GROWHUB_TRUST_PROXY", raising=False)
    # Fresh import path already used by client; call helper directly after env clear.
    import importlib
    import requestutil

    importlib.reload(requestutil)
    from starlette.requests import Request

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [(b"x-real-ip", b"203.0.113.50")],
        "client": ("172.18.0.5", 12345),
        "server": ("test", 80),
    }
    request = Request(scope)
    assert request.client_ip(request) == "172.18.0.5"
