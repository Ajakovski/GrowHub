"""Static checks for the guest-demo UI contracts (no browser needed)."""


def test_demo_page_is_guest_prompt_not_auto_redirect(frontend_root):
    html = (frontend_root / "demo.html").read_text(encoding="utf-8")
    assert 'http-equiv="refresh"' not in html
    assert "Continue as guest" in html
    assert 'data-demo-entry' in html
    assert 'href="login.html?mode=register"' in html
    assert "js/demo-entry.js" in html


def test_demo_js_does_not_auto_navigate(frontend_root):
    js = (frontend_root / "js" / "demo.js").read_text(encoding="utf-8")
    assert "window.location.replace" not in js
    assert "window.location.assign" not in js


def test_dashboard_create_account_leaves_guest_session(frontend_root):
    html = (frontend_root / "dashboard.html").read_text(encoding="utf-8")
    assert 'id="demo-create-account"' in html
    assert 'href="login.html?mode=register"' in html

    dashboard_js = (frontend_root / "js" / "dashboard.js").read_text(encoding="utf-8")
    assert "function leaveDemoForAccount" in dashboard_js
    assert "demo-create-account" in dashboard_js


def test_auth_page_does_not_bounce_demo_users(frontend_root):
    auth_js = (frontend_root / "js" / "auth.js").read_text(encoding="utf-8")
    assert "user?.is_demo" in auth_js
    assert "staying on auth page for guest session" in auth_js


def test_marketing_live_demo_links_go_to_interstitial(frontend_root):
    for name in ("index.html", "how-it-works.html", "login.html", "shop.html", "verify.html"):
        html = (frontend_root / name).read_text(encoding="utf-8")
        assert 'href="demo.html"' in html, f"{name} should link to the guest prompt"
        # Direct auto-entry from marketing pages was skipping the prompt.
        assert 'data-demo-entry' not in html, f"{name} should not auto-start the guest session"
