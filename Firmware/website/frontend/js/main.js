// The backend runs on port 8000 of whatever host served this page; set window.GROWHUB_API_ORIGIN to override.
const GROWHUB_API_ORIGIN = window.GROWHUB_API_ORIGIN
    || `${window.location.protocol === "https:" ? "https:" : "http:"}//${window.location.hostname || "localhost"}:8000`;
const AUTH_URL = `${GROWHUB_API_ORIGIN}/api/auth`;

async function fetchCurrentUser() {
    const response = await fetch(`${AUTH_URL}/me`, { credentials: "include" });
    if (response.status === 401) return null;
    if (!response.ok) throw new Error(`http error! status: ${response.status}`);
    return response.json();
}

function redirectToLogin() {
    const page = window.location.pathname.split("/").pop() || "dashboard.html";
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
