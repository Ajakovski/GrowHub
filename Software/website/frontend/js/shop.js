const CATALOG_URL = `${GROWHUB_API_ORIGIN}/api/web/tiles`;

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
}

function setCatalogStatus(message, isError = false) {
    const status = document.getElementById("catalog-status");
    if (!status) return;
    if (!message) {
        status.hidden = true;
        status.textContent = "";
        status.classList.remove("is-error");
        return;
    }
    status.hidden = false;
    status.textContent = message;
    status.classList.toggle("is-error", isError);
}

function renderSpecs(specs) {
    if (!Array.isArray(specs) || !specs.length) return "";
    return `
        <dl class="catalog-specs">
            ${specs.map((spec) => `
                <div>
                    <dt>${escapeHtml(spec.label)}</dt>
                    <dd>${escapeHtml(spec.value)}</dd>
                </div>
            `).join("")}
        </dl>
    `;
}

function renderFeatures(features) {
    if (!Array.isArray(features) || !features.length) return "";
    return `
        <ul class="feature-list catalog-features">
            ${features.map((feature) => `<li>${escapeHtml(feature)}</li>`).join("")}
        </ul>
    `;
}

function renderCatalogItem(item, index) {
    const image = item.image || "growhub.svg";
    const badge = item.badge
        ? `<span class="catalog-badge">${escapeHtml(item.badge)}</span>`
        : "";
    const category = escapeHtml(item.category_label || item.category || "");
    const price = item.price != null ? escapeHtml(item.price) : "Pricing on request";

    return `
        <article class="catalog-item" data-category="${escapeHtml(item.category || "")}" style="--reveal-delay: ${index * 60}ms">
            <figure class="catalog-item-media">
                <img
                    src="assets/img/${escapeHtml(image)}"
                    alt="${escapeHtml(item.name)}"
                    loading="lazy"
                    onerror="this.src='assets/img/growhub.svg'"
                />
                ${badge}
            </figure>
            <div class="catalog-item-copy">
                <span class="kicker">${category}</span>
                <h3>${escapeHtml(item.name)}</h3>
                ${item.tagline ? `<p class="catalog-tagline">${escapeHtml(item.tagline)}</p>` : ""}
                ${item.description ? `<p class="catalog-desc">${escapeHtml(item.description)}</p>` : ""}
                ${renderSpecs(item.specs)}
                ${renderFeatures(item.features)}
                <div class="catalog-item-actions">
                    <span class="catalog-price">${price}</span>
                    <a href="index.html#contact" class="btn btn-secondary">Inquire</a>
                </div>
            </div>
        </article>
    `;
}

function bindCatalogFilters() {
    const buttons = document.querySelectorAll("#showcase-filters .filter-btn");
    if (!buttons.length) return;

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            buttons.forEach((btn) => {
                btn.classList.remove("active");
                btn.setAttribute("aria-pressed", "false");
            });
            button.classList.add("active");
            button.setAttribute("aria-pressed", "true");

            const filterValue = button.getAttribute("data-filter");
            let visible = 0;
            document.querySelectorAll(".catalog-item").forEach((item) => {
                const match = filterValue === "all" || item.getAttribute("data-category") === filterValue;
                item.hidden = !match;
                if (match) visible += 1;
            });
            setCatalogStatus(visible ? "" : "Nothing in this category yet.");
        });
    });

    buttons.forEach((btn) => btn.setAttribute("aria-pressed", String(btn.classList.contains("active"))));
}

async function loadCatalogData() {
    const grid = document.getElementById("showcase-grid");
    if (!grid) return;

    setCatalogStatus("Loading hardware…");
    try {
        const response = await fetch(CATALOG_URL);
        if (!response.ok) throw new Error(`http error! status: ${response.status}`);
        const catalogData = await response.json();
        if (!Array.isArray(catalogData) || !catalogData.length) {
            grid.innerHTML = "";
            setCatalogStatus("Catalog is empty right now. Check back soon.", true);
            return;
        }
        grid.innerHTML = catalogData.map(renderCatalogItem).join("");
        setCatalogStatus("");
        requestAnimationFrame(() => {
            grid.querySelectorAll(".catalog-item").forEach((item) => item.classList.add("is-visible"));
        });
    } catch (error) {
        console.error("Failed to fetch catalog from backend:", error);
        grid.innerHTML = "";
        setCatalogStatus("Could not load the catalog. Is the GrowHub server running?", true);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    bindCatalogFilters();
    loadCatalogData();
});
