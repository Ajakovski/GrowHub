const API_BASE = `${GROWHUB_API_ORIGIN}/api/web`;
const API_URL = `${API_BASE}/plant-stats`;
const HISTORY_URL = `${API_BASE}/history`;
const CAMERA_SOURCE_URL = `${API_BASE}/camera-source`;
const CAMERA_PLACEHOLDER = "assets/img/growhub_tile_render_v1.png";
const SPARKLINE_RANGE = "1h";
const LEGACY_STORAGE_KEYS = ["growhub.dashboard.history", "growhub.dashboard.lastUpdatedAt"];
const AI_STATUS_COLORS = {
    "Healthy": "var(--green-dark)",
    "Watch": "#b7791f",
    "Action needed": "#e63946",
};
const LOW_FLOW_LPM = 1.0;
const EMPTY_SERIES = { sparkline: [], detail: [] };

let globalTelemetry = null;
let currentHubId = null;
let currentSelection = "hub";
let knownTileIds = null;
let lastUpdatedAt = null;
let hubOnline = false;
let detailRange = SPARKLINE_RANGE;
let historySeries = { hub: EMPTY_SERIES, tile: EMPTY_SERIES };
let historyRequestId = 0;
let cameraSourcePending = false;

async function dashboardFetch(url, options = {}) {
    const response = await fetch(url, { ...options, credentials: "include" });
    if (response.status === 401) {
        redirectToLogin();
        throw new Error("session expired")
    }
    return response;
}

async function logout() {
    try {
        await fetch(`${AUTH_URL}/logout`, { method: "POST", credentials: "include" });
    } finally {
        window.location.replace("login.html");
    }
}

function clearLegacyStorage() {
    try {
        LEGACY_STORAGE_KEYS.forEach((key) => localStorage.removeItem(key));
    } catch (error) {
        console.warn("failed to clear legacy dashboard storage:", error);
    }
}

function tileLabel(tileId) {
    return tileId.replace("_", "").replace(/^\w/, (letter) => letter.toUpperCase());
}

function waterTempStatusText(value) {
    if (value == null) return "No water temperature reading";
    if (value < 16) return "Too cold for roots";
    if (value > 24) return "Too warm: low oxygen risk";
    return "Ideal DWC water temperature";
}

function headerStatusText() {
    const heaterOn = globalTelemetry?.heater_on;
    if (typeof heaterOn !== "boolean") return "";
    return heaterOn ? "heater on" : "heater off";
}

function ecStatusText(value) {
    if (value == null) return "No EC sensor reading";
    if (value < 0.8) return "Low nutrients: dose reservoir";
    if (value > 2.5) return "High nutrients: dilute reservoir";
    return "Nutrients in range";
}

function phStatusText(value) {
    if (value == null) return "No pH sensor reading";
    if (value < 5.5) return "Too acidic: add pH up";
    if (value > 6.5) return "Too alkaline: add pH down";
    return "pH in range";
}

function airTempStatusText(value) {
    if (value == null) return "No air temperature reading";
    if (value < 15) return "Too cold for growth";
    if (value > 30) return "Too hot: heat stress risk";
    return "Comfortable for plants";
}

function humidityStatusText(value) {
    if (value == null) return "No humidity reading";
    if (value < 40) return "Dry air: leaves may stress";
    if (value > 80) return "Very humid: mould risk, add airflow";
    return "Humidity in range";
}

function lightStatusText(value) {
    if (value == null) return "No light sensor reading";
    if (value >= 5000) return "LED canopy on";
    if (value >= 50) return "Ambient light only";
    return "Dark: lights off";
}

function flowStatusText(value, tiles) {
    if (value == null) return "No flow sensor reading";
    const lowTiles = tiles.filter((tile) => Number.isFinite(tile.flow_lpm) && tile.flow_lpm < LOW_FLOW_LPM);
    if (tiles.length > 1 && lowTiles.length && lowTiles.length < tiles.length) {
        return `Low flow in ${lowTiles.map((tile) => tileLabel(tile.tile_id)).join(", ")}: possible clog`;
    }
    if (value < 0.2) return "No flow: check pump and piping";
    if (value < LOW_FLOW_LPM) return "Low flow: possible clog";
    return "Flowing normally";
}

function formatLux(value) {
    return value >= 1000 ? `${(value / 1000).toFixed(1)}k lux` : `${Math.round(value)} lux`
}

const METRICS = [
    {
        key: "water_temp", scope: "hub", field: "water_temperature", label: "Water Temp", unit: "°C", decimals: 1,
        status: (value) => [waterTempStatusText(value), headerStatusText()].filter(Boolean).join(" · "),
    },
    { key: "ec", scope: "hub", field: "ec_level", label: "EC (Nutrients)", unit: " mS/cm", decimals: 2, status: ecStatusText },
    { key: "ph", scope: "hub", field: "ph", label: "pH", unit: "", decimals: 2, stats: phStatusText },
    { key: "air_temp", scope: "tile", field: "air_temperature", label: "Air Temp", unit: "°C", decimals: 1, status: airTempStatusText },
    { key: "humidity", scope: "tile", field: "humidity", label: "Humidity", unit: "%", decimals: 0, status: humidityStatusText },
    { key: "light", scope: "tile", field: "light_lux", label: "Light", unit: " lux", decimals: 0, status: lightStatusText },
    { key: "flow", scope: "tile", field: "flow_lpm", label: "Water Flow", unit: " L/min", decimals: 2, status: flowStatusText },
];

function formatMetric(metric, value) {
    if (value == null) return "--";
    return metric.format ? metric.format(value) : `${value.toFixed(metric.decimals)}${metric.unit}`;
}

function metricCardHtml(metric) {
    return `
        <article class="metric-card metric-card-expandable" data-metric="${metric.key}">
            <div class="metric-card-main">
                <div class="metric-card-heading">
                    <span class="kicker" id="${metric.key}-label">${metric.label}</span>
                    <button type="button" class="metric-expand-btn" aria-expanded="false" aria-controls="${metric.key}-detail" aria-label="Show ${metric.label} history">
                        <svg viewBox="0 0 20 20" aria-hidden="true">
                            <path d="M5 7.5 L10 12.5 L15 7.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path>
                        </svg>
                    </button>
                </div>
                <strong id="${metric.key}-val">--</strong>
                <svg class="sparkline" id="${metric.key}-sparkline" viewBox="0 0 120 36" aria-hidden="true"></svg>
                <span id="${metric.key}-status">Fetching data...</span>
            </div>
            <div class="metric-card-detail" id="${metric.key}-detail" hidden>
                <div class="detail-chart-header">
                    <div class="detail-chart-stats" id="${metric.key}-detail-stats"></div>
                    <div class="detail-range" role="group" aria-label="${metric.label} history range">
                        <button type="button" class="pill ${detailRange === "1h" ? "active" : ""}" data-range="1h">1h</button>
                        <button type="button" class="pill ${detailRange === "24h" ? "active" : ""}" data-range="24h">24h</button>
                        <button type="button" class="pill ${detailRange === "7d" ? "active" : ""}" data-range="7d">7d</button>
                    </div>
                </div>
                <svg class="detail-chart" id="${metric.key}-detail-chart" viewBox="0 0 560 220" preserveAspectRatio="none" role="img" aria-label="${metric.label} history chart"></svg>
            </div>
        </article>
    `;
}

function buildMetricCards() {
    const containers = {
        hub: document.getElementById("hub-metrics"),
        tile: document.getElementById("tile-metrics"),
    };
    METRICS.forEach((metric) => {
        containers[metric.scope]?.insertAdjacentHTML("beforeend", metricCardHtml(metric));
    })
}

function average(values) {
    return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
}

function formatRelativeTime(timestamp, prefix = "Updated") {
    if (!Number.isFinite(timestamp) || timestamp <= 0) return "Waiting for first update...";
    const seconds = Math.max(0, Math.floor((Date.now() - timestamp) / 1000));
    if (seconds < 2) return `${prefix} just now`;
    if (seconds < 60) return `${prefix} ${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${prefix} ${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 48) return `${prefix} ${hours}h ago`;
    return `${prefix} ${Math.floor(hours / 24)}d ago`;
}

function getLastUpdatedElement() {
    return document.getElementById("last-updated") || document.querySelector(".last-updated");
}

function setLoading(isLoading) {
    const grid = document.getElementById("metric-grid");
    if (grid) grid.classList.toggle("is-loading", isLoading);
}

function setOfflineState(message = "Offline / Connection Error") {
    const systemStatus = document.getElementById("system-status");
    if (systemStatus) {
        systemStatus.textContent = message;
        systemStatus.style.borderColor = "#e63946";
    }

    METRICS.forEach((metric) => {
        const element = document.getElementById(`${metric.key}-status`);
        if (element) element.textContent = "No telemetry";
    });

    const lastUpdated = getLastUpdatedElement();
    if (lastUpdated) {
        lastUpdated.textContent = lastUpdatedAt
            ? formatRelativeTime(lastUpdatedAt, "Last report")
            : "Connection lost";
    }
}

function renderAlerts() {
    const alerts = Array.isArray(globalTelemetry?.alerts) ? globalTelemetry.alerts : [];

    const list = document.getElementById("alert-list");
    if (list) {
        list.replaceChildren(
            ...alerts.map((alert) => {
                const item = document.createElement("div");
                item.className = "alert-item";
                item.setAttribute("role", "status");
                item.textContent = alert.message;
                return item;
            })
        );
        list.hidden = alerts.length === 0;
    }

    const devicesWithAlerts = new Set(alerts.map((alert) => alert.device));
    document.querySelectorAll("#device-selector button[data-id]").forEach((button) => {
        button.classList.toggle("has-alert", devicesWithAlerts.has(button.getAttribute("data-id")));
    });
}

async function fetchHistorySeries(deviceId, range) {
    const url = new URL(HISTORY_URL);
    if (currentHubId) url.searchParams.set("hub", currentHubId);
    url.searchParams.set("device", deviceId);
    url.searchParams.set("range", range);

    const response = await fetch(url);
    if (!response.ok) throw new Error(`http error! status: ${response.status}`);

    const data = await response.json();
    return Array.isArray(data.points) ? data.points : [];
}

async function loadSeries(deviceId, range) {
    const sparkline = fetchHistorySeries(deviceId, SPARKLINE_RANGE);
    const detail = range === SPARKLINE_RANGE ? sparkline : await fetchHistorySeries(deviceId, range);
    return { sparkline, detail };
}

async function refreshHistory() {
    const requestId = ++historyRequestId;
    const deviceId = currentSelection;
    const range = detailRange;

    try {
        const hub = await loadSeries("hub", range);
        const tile = deviceId === "hub" ? hub : await loadSeries(deviceId, range);

        if (requestId !== historyRequestId) return;

        historySeries = { hub, tile };
        renderHistory();
    } catch (error) {
        console.warn("failed to load history:", error);
    }
}

function buildSparklinePath(values, width, height) {
    if (values.length < 2) return "";

    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;

    return values
        .map((value, index) => {
            const x = (index / (values.length - 1)) * width;
            const y = height - ((value - min) / range) * (height - 6) - 3;
            return `${index === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
        })
        .join(" ");
}

function renderSparkline(svgId, values) {
    const svg = document.getElementById(svgId);
    if (!svg) return;

    const width = 120;
    const height = 36;
    const path = buildSparklinePath(values, width, height);

    if (!path) {
        svg.innerHTML = `<text x="0" y="22" class="sparkline-empty">Collecting trend...</text>`;
        return;
    }

    svg.innerHTML = `
        <path d="${path}" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
    `;
}

function updateLastUpdatedLabel() {
    const lastUpdated = getLastUpdatedElement();
    if (!lastUpdated) return;
    lastUpdated.textContent = lastUpdatedAt
        ? formatRelativeTime(lastUpdatedAt, hubOnline ? "Updated" : "Last report")
        : "Waiting for first update...";
}

async function fetchPlantStats() {
    try {
        const url = new URL(API_URL);
        if (currentHubId) url.searchParams.set("hub", currentHubId);

        const response = await fetch(url);
        if (response.status === 404 && currentHubId) {
            currentHubId = null;
            return fetchPlantStats();
        }
        if (!response.ok) throw new Error(`http error! status: ${response.status}`);

        globalTelemetry = await response.json();
        currentHubId = globalTelemetry.hub_id ?? null;
        lastUpdatedAt = globalTelemetry.last_telemetry_at ?? null;
        hubOnline = Boolean(globalTelemetry.hub_online);
        setLoading(false);

        if (!lastUpdatedAt) {
            setOfflineState("Waiting for hub");
            renderAlerts();
            return;
        }

        updateDeviceSelector();
        renderStats();
        renderAlerts();
        refreshHistory();
    } catch (error) {
        console.error("failed to load plant telemetry:", error);
        setLoading(false);
        setOfflineState();
    }
}

function updateDeviceSelector() {
    const selector = document.getElementById("device-selector");
    if (!selector || !globalTelemetry) return;

    const tileIds = (globalTelemetry.tiles || []).map((tile) => tile.tile_id).join(",");

    if (knownTileIds !== tileIds) {
        knownTileIds = tileIds;

        let html = `<button type="button" class="pill ${currentSelection === "hub" ? "active" : ""}" data-id="hub">All tiles</button>`;

        if (globalTelemetry.tiles) {
            globalTelemetry.tiles.forEach((tile) => {
                const isActive = currentSelection === tile.tile_id ? "active" : "";
                const label = tile.tile_id.replace("_", " ").toUpperCase();
                html += `<button type="button" class="pill ${isActive}" data-id="${tile.tile_id}">${label}</button>`;
            });
        }

        selector.innerHTML = html;
        return;
    }

    selector.querySelectorAll("button[data-id]").forEach((button) => {
        button.classList.toggle("active", button.getAttribute("data-id") === currentSelection);
    });
}

function selectDevice(deviceId) {
    if (!deviceId || deviceId === currentSelection) return;
    currentSelection = deviceId;
    historySeries = { ...historySeries, tile: EMPTY_SERIES };
    updateDeviceSelector();
    if (globalTelemetry) {
        renderStats();
    } else {
        renderHistory();
    }
    refreshHistory();
}

function selectedTiles() {
    const tiles = globalTelemetry?.tiles || [];
    return currentSelection === "hub" ? tiles.filter((tile) => tile.tile_id === currentSelection);
}

function metricValue(metric) {
    if (metric.scope === "hub") {
        const value = globa.globalTelemetry[metric.field];
        retrun Number.isFinite(value) ? value : null;
    }
    return average(selectedTiles().map((tile) => tile[metric.field]).filter(Number.isFinite));
}

function renderMetrics() {
    const tiles = selectedTiles();
    const showingAverage = currentSelection === "hub";

    METRICS.forEach((metric) => {
        const value = metricValue(metric);
        const label = metric.scope === "tile" && showingAverage ? `Avg ${metric.label}` : metric.label;
        document.getElementById(`${metric.key}-label`).textContent = label;
        document.getElementById(`${metric.key}-val`).textContent = formatMetric(metric, value);
        document.getElementById(`${metric.key}-status`).textContent = metric.status(value, tiles);
    });

    const scope = document.getElementById("tile-scope");
    if (scope) scope.textContent = showingAverage ? "Average across all tiles" : tileLabel(currentSelection);
}

function renderStats() {
    if (!globalTelemetry) return;

    renderMetrics();

    document.getElementById("water-val").textContent = globalTelemetry.water_level_ok ? "OK" : "LOW";
    document.getElementById("water-val").style.color = globalTelemetry.water_level_ok
        ? "var(--green)"
        : "#e63946";
    document.getElementById("water-status").textContent = globalTelemetry.water_level_ok
        ? "18 L reservoir level healthy"
        : "Top up the 18 L reservoir";

    renderAiCard();

    renderHistory();

    renderCamera();

    const systemStatus = document.getElementById("system-status");
    if (systemStatus) {
        systemStatus.textContent = hubOnline ? `Active: ${globalTelemetry.hub_id}` : "Hub offline";
        systemStatus.style.borderColor = hubOnline ? "var(--green)" : "#e63946";
    }

    document.getElementById("metric-grid")?.classList.toggle("is-stale", !hubOnline);

    updateLastUpdatedLabel();
}

function renderAiCard() {
    const status = globalTelemetry.ai_health_status || "Not analysed yet";
    const statusElement = document.getElementById("ai-status");
    statusElement.textContent = status;
    statusElement.style.color = AI_STATUS_COLORS[status] || "";

    const detail = document.getElementById("ai-status-detail");
    detail.textContent = globalTelemetry.ai_summary
        ? `${globalTelemetry.ai_summary} · ${formatRelativeTime(globalTelemetry.ai_updated_at, "Reviewed")}`
        : "Waiting for the first AI review";
}

function cameraStatusText() {
    if (globalTelemetry.camera_source === "stock") {
        const count = globalTelemetry.stock_image_count || 0;
        if (!count) return "No stock images affed";
        return `Stock images ${count} ${count === 1 ? "photo" : "photos"}`;
    }
    if (globalTelemetry.camera_online) return "Live webcam";
    return globalTelemetry.camera_feed_url ? "Webcam offline last frame" : "No webcam frames yet";
}

function renderCamera() {
    const source = globalTelemetry.camera_source || "webcam";
    if (!cameraSourcePending) {
        document.querySelectorAll("#camera-source button[data-source]").forEach((button) => {
            button.classList.toggle("active", button.getAttribute("data-source") === source);
        });
    }

    const pill = document.getElementById("camera-node-pill");
    if (pill) pill.textContent = cameraStatusText();

    updateCameraFeed(globalTelemetry.camera_feed_url, globalTelemetry.hubId);
}

async function selectCameraSource(source) {
    if (!source || !currentHubId || cameraSourcePending) return;
    if (source === globalTelemetry?.camera_source) return;

    const buttons = document.querySelectorAll("#camera-source button[data-source]");
    cameraSourcePending = true;
    buttons.forEach((button) => {
        button.disabled = true;
        button.classList.toggle("active", button.getAttribute("data-source") === source);
    });

    try {
        const url = new URL(CAMERA_SOURCE_URL);
        url.searchParams.set("hub", currentHubId);
        const response = await fetch(url, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ source }),
        });
        if (!response.ok) throw new Error(`http error! status: ${response.status}`);
    } catch (error) {
        console.error("failed to switch camera source:", error);
    } finally {
        cameraSourcePending = false;
        button.forEach((button) => {
            button.disabled = false;
        });
        await fetchPlantStats();
    }
}

function updateCameraFeed(cameraFeedUrl, hubId) {
    const cameraFeed = document.getElementById("camera-feed");
    if (!cameraFeed) return;
    if (!cameraFeedUrl) {
        if (!cameraFeed.src.endsWith(CAMERA_PLACEHOLDER)) cameraFeed.src = CAMERA_PLACEHOLDER;
        cameraFeed.alt = "No camera image available";
        return;
    }

    try {
        const nextUrl = new URL(cameraFeedUrl, GROWHUB_API_ORIGIN);
        const isStream = nextUrl.pathname.includes("/camera/stream");

        if (isStream) {
            const currentUrl = new URL(cameraFeed.src || cameraFeedUrl, GROWHUB_API_ORIGIN);
            if (currentUrl.origin + currentUrl.pathname !== nextUrl.origin + nextUrl.pathname) {
                cameraFeed.src = nextUrl.href;
            }
        } else {
            nextUrl.searchParams.set("t", String(Date.now()));
            cameraFeed.src = nextUrl.href;
        }

        cameraFeed.alt = `Optical feed — ${hubId || "hub"}`;
    } catch (error) {
        console.warn("invalid camera feed url:", cameraFeedUrl, error);
    }
}

function formatAxisTime(timestamp, range) {
    if (!Number.isFinite(timestamp)) return "--:--";
    const date = new Date(timestamp);
    if (range === "7d") {
        return date.toLocaleDateString([], { weekday: "short", day: "numeric" });
    }
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function renderDetailChart(svgId, statsId, allPoints, unit, range, decimals = 1) {
    const svg = document.getElementById(svgId);
    const stats = document.getElementById(statsId);
    if (!svg) return;

    const points = allPoints.filter((point) => Number.isFinite(point.value));
    const values = points.map((point) => point.value);
    if (values.length < 2) {
        svg.innerHTML = `<text x="24" y="112" class="detail-chart-empty">Collecting history for a detailed chart...</text>`;
        if (stats) stats.innerHTML = "";
        return;
    }

    const width = 560;
    const height = 220;
    const pad = { top: 18, right: 18, bottom: 36, left: 44 };
    const plotW = width - pad.left - pad.right;
    const plotH = height - pad.top - pad.bottom;

    const min = Math.min(...values);
    const max = Math.max(...values);
    const avg = values.reduce((sum, value) => sum + value, 0) / values.length;
    const spread = max - min || 1;
    const yMin = min - spread * 0.08;
    const yMax = max + spread * 0.08;
    const yRange = yMax - yMin || 1;

    const coords = values.map((value, index) => {
        const x = pad.left + (index / (values.length - 1)) * plotW;
        const y = pad.top + (1 - (value - yMin) / yRange) * plotH;
        return { x, y, value, at: points[index].at };
    });

    const linePath = coords
        .map((point, index) => `${index === 0 ? "M" : "L"}${point.x.toFixed(1)} ${point.y.toFixed(1)}`)
        .join(" ");
    const areaPath = `${linePath} L${coords[coords.length - 1].x.toFixed(1)} ${(pad.top + plotH).toFixed(1)} L${coords[0].x.toFixed(1)} ${(pad.top + plotH).toFixed(1)} Z`;

    const gridLines = [0, 0.25, 0.5, 0.75, 1]
        .map((ratio) => {
            const y = pad.top + plotH * ratio;
            const label = yMax - yRange * ratio;
            return `
                <line class="detail-chart-grid" x1="${pad.left}" y1="${y.toFixed(1)}" x2="${width - pad.right}" y2="${y.toFixed(1)}"></line>
                <text class="detail-chart-axis" x="${pad.left - 8}" y="${(y + 4).toFixed(1)}" text-anchor="end">${label.toFixed(decimals)}</text>
            `;
        })
        .join("");

    const xLabels = [0, Math.floor((coords.length - 1) / 2), coords.length - 1]
        .filter((index, i, arr) => arr.indexOf(index) === i)
        .map((index) => {
            const point = coords[index];
            return `<text class="detail-chart-axis" x="${point.x.toFixed(1)}" y="${height - 12}" text-anchor="middle">${formatAxisTime(point.at, range)}</text>`;
        })
        .join("");

    const dots = coords.length > 40
        ? ""
        : coords
            .map(
                (point) =>
                    `<circle class="detail-chart-dot" cx="${point.x.toFixed(1)}" cy="${point.y.toFixed(1)}" r="3.2"></circle>`
            )
            .join("");

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.innerHTML = `
        ${gridLines}
        <path class="detail-chart-area" d="${areaPath}"></path>
        <path class="detail-chart-line" d="${linePath}"></path>
        ${dots}
        ${xLabels}
    `;

    if (stats) {
        stats.innerHTML = `
            <div class="detail-stat"><span>Min</span><strong>${min.toFixed(decimals)}${unit}</strong></div>
            <div class="detail-stat"><span>Avg</span><strong>${avg.toFixed(decimals)}${unit}</strong></div>
            <div class="detail-stat"><span>Max</span><strong>${max.toFixed(decimals)}${unit}</strong></div>
            <div class="detail-stat"><span>Points</span><strong>${values.length}</strong></div>
        `;
    }
}

function renderHistory() {
    METRICS.forEach((metric) => {
        const series = historySeries[metric.scope];
        renderSparkline(
            `${metric.key}-sparkline`,
            series.sparkline.map((point) => point[metric.key]).filter(Number.isFinite)
        );
    });
    renderDetailCharts();
}

function renderDetailCharts() {
    METRICS.forEach((metric) => {
        renderDetailChart(
            `${metric.key}-detail-chart`,
            `${metric.key}-detail-stats`,
            historySeries[metric.scope].detail.map((point) => ({ value: point[metric.key], at: point.at })),
            metric.unit,
            detailRange,
            metric.decimals
        );
    });
}

function setDetailRange(range) {
    if (!range || range === detailRange) return;
    detailRange = range;

    document.querySelectorAll(".detail-range button[data-range]").forEach((button) => {
        button.classList.toggle("active", button.getAttribute("data-range") === detailRange);
    });

    refreshHistory();
}

function toggleMetricCard(card) {
    if (!card) return;
    const willExpand = !card.classList.contains("is-expanded");
    const button = card.querySelector(".metric-expand-btn");
    const detail = card.querySelector(".metric-card-detail");

    document.querySelectorAll(".metric-card-expandable.is-expanded").forEach((openCard) => {
        if (openCard === card) return;
        openCard.classList.remove("is-expanded");
        const openBtn = openCard.querySelector(".metric-expand-btn");
        const openDetail = openCard.querySelector(".metric-card-detail");
        if (openBtn) openBtn.setAttribute("aria-expanded", "false");
        if (openDetail) openDetail.hidden = true;
    });

    card.classList.toggle("is-expanded", willExpand);
    if (button) button.setAttribute("aria-expanded", String(willExpand));
    if (detail) detail.hidden = !willExpand;
    if (willExpand) renderDetailCharts();
}

async function initDashboard() {
    let user = null;
    try {
        user = await fetchCurrentUser();
    } catch (error) {
        console.error("could not check login state:", error);
    }
    if (!user) {
        redirectToLogin();
        return;
    }
    document.getElementById("account-email").textContent = user.email;
    document.getElementById("logout-button").addEventListener("click", logout);
    document.body.classList.remove("auth-pending");
    
    clearLegacyStorage();
    buildMetricCards();
    setLoading(true);
    updateLastUpdatedLabel();
    renderHistory();
    refreshHistory();
    fetchPlantStats();
    setInterval(fetchPlantStats, 5000);
    setInterval(updateLastUpdatedLabel, 1000);

    const selectorContainer = document.getElementById("device-selector");
    if (selectorContainer) {
        selectorContainer.addEventListener("click", (event) => {
            const button = event.target.closest("button[data-id]");
            if (button) selectDevice(button.getAttribute("data-id"));
        });
    }

    document.getElementById("camera-source")?.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-source]");
        if (button) selectCameraSource(button.getAttribute("data-source"));
    });

    document.querySelectorAll(".metric-card-expandable").forEach((card) => {
        const button = card.querySelector(".metric-expand-btn");
        if (!button) return;
        button.addEventListener("click", () => toggleMetricCard(card));
    });

    document.querySelectorAll(".detail-range").forEach((group) => {
        group.addEventListener("click", (event) => {
            const button = event.target.closest("button[data-range]");
            if (button) setDetailRange(button.getAttribute("data-range"));
        });
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDashboard);
} else {
    initDashboard();
}
