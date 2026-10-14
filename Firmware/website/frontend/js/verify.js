const VERIFY_REDIRECT_DELAY_MS = 1500;

function showVerifyResult(title, message, action) {
    document.getElementById("verify-title").textContent = title;
    document.getElementById("verify-message").textContent = message;
    const button = document.getElementById("verify-action");
    if (action) {
        button.textContent = action.label;
        button.href = action.href;
        button.hidden = false;
    }
}

async function verifyEmail() {
    const token = new URLSearchParams(window.location.search).get("token");
    window.history.replaceState(null, "", window.location.pathname);

    if (!token) {
        showVerifyResult("Link incomplete", "This verification link is missing its code. Open the link from the email again.", {
            label: "Go to log in",
            href: "login.html",
        });
        return;
    }

    try {
        const response = await fetch(`${AUTH_URL}/verify`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token }),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(typeof data.detail === "string" ? data.detail : `Verification failed (${response.status}).`);
        }
        showVerifyResult("Email verified", "Your account is ready. Taking you to your dashboard...", {
            label: "Open dashboard",
            href: "dashboard.html",
        });
        setTimeout(() => window.location.replace("dashboard.html"), VERIFY_REDIRECT_DELAY_MS);
    } catch (error) {
        if (await fetchCurrentUser().catch(() => null)) {
            showVerifyResult("Already verified", "Your email is already verified. Taking you to your dashboard...", {
                label: "Open dashboard",
                href: "dashboard.html",
            });
            setTimeout(() => window.location.replace("dashboard.html"), VERIFY_REDIRECT_DELAY_MS);
            return;
        }
        showVerifyResult(
            "Couldn't verify your email",
            error instanceof TypeError
                ? "Could not reach the GrowHub server. Try opening the link again in a moment."
                : `${error.message} Log in to get a new link.`,
            { label: "Go to log in", href: "login.html" }
        );
    }
}

verifyEmail();
