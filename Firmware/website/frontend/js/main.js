const GROWHUB_API_ORIGIN = window.GROWHUB_API_ORIGIN
    || `${window.location.protocol === "https:" ? "https:" : "http:"}//${window.location.hostname || "localhost"}:8000`;

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

const filterButtons = document.querySelectorAll(".filter-btn");

if (filterButtons.length > 0) {
    filterButtons.forEach(button => {
        button.addEventListener("click", () => {
            filterButtons.forEach(btn => btn.classList.remove("active"));
            button.classList.add("active");

            const filterValue = button.getAttribute("data-filter");

            document.querySelectorAll(".showcase-card").forEach(card => {
                if (filterValue === "all" || card.getAttribute("data-category") === filterValue) {
                    card.classList.remove("hidden");
                } else {
                    card.classList.add('hidden');
                }
            });
        });
    });
}

async function loadCatalogData() {
    try {
        const response = await fetch(`${GROWHUB_API_ORIGIN}/api/web/tiles`);
        if (!response.ok) throw new Error(`http error! status: ${response.status}`);

        const catalogData = await response.json();
        const grid = document.getElementById("showcase-grid");

        if (!grid) return;

        grid.innerHTML = "";

        catalogData.forEach(item => {
            const card = document.createElement("article");
            card.className = "showcase-card";
            card.setAttribute("data-category", item.category);

            card.innerHTML = `
                <div class="card-img-wrap">
                    <img src="assets/img/${item.id}.png" alt="${item.name}" onerror="this.src='assets/img/growhub.svg'" />
                    ${item.category === 'tech' ? '<span class="card-badge">Core</span>' : ''}
                </div>
                <div class="card-info">
                    <h3>${item.name}</h3>
                    ${item.description ? `<p>${item.description}</p>` : ''}
                    <p>${item.price != null ? `Price: ${item.price}` : 'Pricing on request'}</p>
                    <a href="index.html#contact" class="text-link">Inquire about specs &rarr;</a>
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (error) {
        console.error("Failed to fetch catalog from backend:", error);
    }
}

document.addEventListener("DOMContentLoaded", loadCatalogData);