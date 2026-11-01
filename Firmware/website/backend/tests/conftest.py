import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = BACKEND_ROOT.parent / "frontend"
# Allow `from main import app` when pytest is run from repo root or backend/.
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture()
def frontend_root() -> Path:
    return FRONTEND_ROOT


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Fresh app + sqlite DB per test so demo/auth cases don't share sessions."""
    db_path = tmp_path / "growhub-test.db"
    monkeypatch.setenv("GROWHUB_DB_PATH", str(db_path))
    monkeypatch.delenv("GROWHUB_DEVICE_KEY", raising=False)

    for name in list(sys.modules):
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
        } or name.startswith("routers"):
            del sys.modules[name]

    import history

    history.DB_PATH = db_path
    history.init_db()

    import accounts

    accounts.init_db()

    from fastapi.testclient import TestClient
    import main as main_module

    # Avoid leftover hubs from a previous import of routers.device.
    from routers import device

    device.hubs.clear()

    with TestClient(main_module.app) as test_client:
        yield test_client
