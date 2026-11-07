// Hit same-origin /api (nginx → backend). Override with GROWHUB_API_ORIGIN for :8000.
const GROWHUB_API_ORIGIN = window.GROWHUB_API_ORIGIN != null
    ? window.GROWHUB_API_ORIGIN
    : window.location.origin;
const AUTH_URL = `${GROWHUB_API_ORIGIN}/api/auth`;

// Resolves once the dashboard finishes auth (including guest demo).
const growhubAuth = (() => {
    let settledUser = undefined;
    let resolveReady;
    const ready = new Promise((resolve) => {
        resolveReady = resolve;
    });
    return {
        ready,
        get user() {
            return settledUser;
        },
        settle(user) {
            if (settledUser !== undefined) return;
            settledUser = user || null;
            resolveReady(settledUser);
        },
    };
})();
window.growhubAuth = growhubAuth;

async function fetchCurrentUser() {
    const response = await fetch(`${AUTH_URL}/me`, { credentials: "include" });
    if (response.status === 401) return null;
    if (!response.ok) throw new Error(`http error! status: ${response.status}`);
    return response.json();
}

function redirectToLogin() {
    // Guest demo entry handles its own failure UI.
    try {
        if (sessionStorage.getItem("growhub_demo_entry") === "1") {
            console.warn("[growhub:demo] blocked login redirect during guest entry");
            return;
        }
    } catch (error) {}
    const page = window.location.pathname.split("/").pop() || "dashboard.html";
    console.info("[growhub] redirect to login", { next: page });
    window.location.replace(`login.html?next=${encodeURIComponent(page)}`);
}

const navToggle = document.querySelector("[data-nav-toggle]");
const navMenu = document.querySelector("[data-nav-menu]");

if (navToggle && navMenu) {
    navToggle.addEventListener("click", () => {
        const isOpen = navMenu.classList.toggle("open");
        navToggle.setAttribute("aria-expanded", String(isOpen));
    });

    document.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;
        if (!navMenu.contains(target) && !navToggle.contains(target)) {
            navMenu.classList.remove("open");
            navToggle.setAttribute("aria-expanded", "false");
        }
    });

    navMenu.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => {
            navMenu.classList.remove("open");
            navToggle.setAttribute("aria-expanded", "false");
        });
    });
}

const yearElement = document.querySelector("[data-year]");

if (yearElement) {
    yearElement.textContent = String(new Date().getFullYear());
}

if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    document.querySelectorAll("[data-autoplay-video]").forEach(video => {
        video.removeAttribute("autoplay");
        video.pause();
        video.controls = true;
    });
}
