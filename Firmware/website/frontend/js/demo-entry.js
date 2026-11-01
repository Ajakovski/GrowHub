// POST /demo here first — navigating cold was losing the cookie.
function demoLog(message, detail) {
    if (detail !== undefined) console.info(`[growhub:demo] ${message}`, detail);
    else console.info(`[growhub:demo] ${message}`);
}

async function startLiveDemoEntry(event) {
    if (event) event.preventDefault();
    try {
        sessionStorage.setItem("growhub_demo_entry", "1");
    } catch (error) {}

    const status = document.getElementById("demo-entry-status");
    if (status) {
        status.hidden = false;
        status.textContent = "Opening live demo…";
    }

    demoLog("starting guest session");
    try {
        const response = await fetch(`${AUTH_URL}/demo`, {
            method: "POST",
            credentials: "include",
            cache: "no-store",
        });
        const body = await response.json().catch(() => ({}));
        if (!response.ok) {
            const detail = typeof body.detail === "string"
                ? body.detail
                : `Could not start demo (${response.status})`;
            demoLog("guest session failed", { status: response.status, detail });
            throw new Error(detail);
        }
        demoLog("guest session ok, opening dashboard");
        window.location.assign(`dashboard.html?demo=1&t=${Date.now()}`);
    } catch (error) {
        demoLog("guest session error", error);
        if (status) {
            status.textContent = error instanceof TypeError
                ? "Could not reach the GrowHub server."
                : error.message || "Could not start the demo.";
        } else {
            window.alert(error instanceof TypeError
                ? "Could not reach the GrowHub server."
                : error.message || "Could not start the demo.");
        }
    }
}

function bindLiveDemoEntryLinks() {
    document.querySelectorAll("[data-demo-entry]").forEach((link) => {
        link.addEventListener("click", startLiveDemoEntry);
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindLiveDemoEntryLinks);
} else {
    bindLiveDemoEntryLinks();
}
