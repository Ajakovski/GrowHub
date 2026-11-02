"""Static frontend/nginx contracts that previously broke the live demo."""

from pathlib import Path


def test_api_origin_defaults_to_location_origin(frontend_root):
    main_js = (frontend_root / "js" / "main.js").read_text(encoding="utf-8")
    assert "window.location.origin" in main_js
    assert "GROWHUB_API_ORIGIN" in main_js


def test_login_redirect_blocked_during_demo_entry(frontend_root):
    main_js = (frontend_root / "js" / "main.js").read_text(encoding="utf-8")
    assert "growhub_demo_entry" in main_js
    assert "blocked login redirect during guest entry" in main_js


def test_dashboard_bootstraps_demo_before_onboarding(frontend_root):
    html = (frontend_root / "dashboard.html").read_text(encoding="utf-8")
    assert "growhubDemoBootstrap" in html
    assert "growhub_demo_entry" in html
    assert html.index("growhubDemoBootstrap") < html.index("onboarding.js")


def test_nginx_proxies_api_same_origin():
    nginx = Path(__file__).resolve().parents[2] / "nginx.conf"
    text = nginx.read_text(encoding="utf-8")
    assert "location /api/" in text
    assert "proxy_pass http://backend:8000/api/" in text
    assert "proxy_pass_header Set-Cookie" in text


def test_compose_mounts_nginx_config():
    compose = Path(__file__).resolve().parents[2] / "compose.yaml"
    text = compose.read_text(encoding="utf-8")
    assert "./nginx.conf:/etc/nginx/conf.d/default.conf" in text


def test_demo_entry_posts_before_navigation(frontend_root):
    js = (frontend_root / "js" / "demo-entry.js").read_text(encoding="utf-8")
    assert "${AUTH_URL}/demo" in js or "`${AUTH_URL}/demo`" in js
    assert "method: \"POST\"" in js or "method: 'POST'" in js
    assert "dashboard.html?demo=1" in js


def test_onboarding_waits_for_growhub_auth(frontend_root):
    js = (frontend_root / "js" / "onboarding.js").read_text(encoding="utf-8")
    assert "growhubAuth" in js
    assert "onboarding 401" in js
