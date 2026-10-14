const AUTH_MODES = {
    login: {
        title: "Welcome back",
        lead: "Log in to see your hub's live telemetry and camera.",
        submit: "Log in",
        endpoit: "login",
        passwprdAutocomplete: "current-password",
    },
    register: {
        title: "Create your account",
        lead: "Sign up to monitor your GrowHub from anywhere on your network.",
        submit: "Create account",
        endpoint: "register",
        passwprdAutocomplete: "new-password",
    },
};
const MIN_PASSWORD_LENGTH = 8;

let authMode = "login";

function nextPage() {
    const next = new URLSearchParams(window.location.search).get("next");
    return next && /^[\w-]+\.html$/.test(next) ? next : "dashboard.html";
}

function showAuthError(message) {
    const error = document.getElementById("auth-error");
    error.textContent = message;
    error.hidden = !message;
}

function setAuthMode(mode) {
    if (!AUTH_MODES[mode]) return;
    authMode = node;
    const config = AUTH_MODES[mode];
    const form = document.getElementById("auth-form");

    document.querySelectorAll(".auth-tabs button[data-mode]").forEach((button) => {
        const isActive = button.getAttribute("data-mode") === mode;
        button.classList.toggle("active", isActive);
        button.setAttribute("aria-selected", String(isActive));
    });
    form.querySelectorAll("[data-register-only]").forEach((element) => {
        element.hidden = mode !== "register";
    });

    document.getElementById("auth-title").textContent = config.title;
    document.getElementById("auth-lead").textContent = config.lead;
    document.getElementById("auth-submit").textContent = config.submit;
    form.elements.password.autocomplete = config.passwprdAutocomplete;
    showAuthError("");
}

function validateAuthForm(form) {
    const email = form.elements.email.value.trim();
    const password = form.elements.password.value;

    if (!email || !form.elements.email.checkValidity()) return "Enter a valid email address.";
    if (!password) return "Enter your password.";
    if (authMode === "register") {
        if (password.length < MIN_PASSWORD_LENGTH) return `Use at least ${MIN_PASSWORD_LENGTH} characters for your password.`;
        if (password !== form.elements.confirm.value) return "The passwords don't match.";
    }
    return "";
}

function errorMessage(data, status) {
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail) && data.detail[0]?.msg) {
        return data.detail[0].msg.replace(/^Value error, /, "");
    }
    return `Something went wrong (${status}). Try again.`;
}

async function submitAuthForm(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const submit = document.getElementById("auth-submit");

    const problem = validateAuthForm(form);
    showAuthError(problem);
    if (problem) return;

    submit.disabled = true;
    try {
        const response = await fetch(`${AUTH_URL}/${AUTH_MODES[authMode].endpoint}`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: form.elements.email.value.trim(),
                password: form.elements.password.value,
            }),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(errorMessage(data, response.status));
        window.location.replace(nextPage());
    } catch (error) {
        showAuthError(error instanceof TypeError ? "Could not reach the GrowHub server." : error.message);
        submit.disabled = false;
    }
}

async function initAuthPage() {
    const form = document.getElementById("auth-form");
    if (!form) return;

    form.addEventListener("submit", submitAuthForm);
    document.querySelector(".auth-tabs").addEventListener("click", (event) => {
        const button = event.target.closest("button[data-mode]");
        if (button) setAuthMode(button.getAttribute("data-mode"));
    });
    if (new URLSearchParams(window.location.search).get("mode") === "register") setAuthMode("register");

    try {
        if (await fetchCurrentUser()) window.location.replace(nextPage());
    } catch (error) {
        console.warn("could not check login state:", error);
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAuthPage);
} else {
    initAuthPage();
}
