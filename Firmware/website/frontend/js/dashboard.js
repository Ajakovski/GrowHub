const API_URL = "http://localhost:8000/api/web/plant-stats";
const HISTORY_LIMIT = 20;
const HISTORY_STORAGE_KEY = "growhub.dashboard.history";
const LAST_UPDATED_STORAGE_KEY = "growhub.dashboard.lastUpdatedAt";

let globalTelemetry = null;
let currentSelection = "hub";
let knownTileIds = null;
let lastUpdatedAt = null;
let hasLoadedOnce = false;
let historyByDevice = loadHistory();
lastUpdatedAt = loadLastUpdatedAt();

function loadHistory() {
    try {
        const raw = localStorage.getItem(HISTORY_STORAGE_KEY);
        if (!raw) return {};

        const parsed = JSON.parse(raw);
        if (!parsed || typeof parsed !== "object") return {};

        const cleaned = {};
        for (const [deviceId, series] of Object.entries(parsed)) {
            if (!Array.isArray(series)) continue;
            cleaned[deviceId] = series
                .filter(
                    (point) =>
                        point &&
                        typeof point.moisture === "number" &&
                        typeof point.temperature === "number"
                )
                .slice(-HISTORY_LIMIT);
        }
        return cleaned;
    } catch (error) {
        console.warn("failed to load sparkline history:", error);
        return {};
    }
}

function saveHistory() {
    try {
        localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(historyByDevice));
    } catch (error) {
        console.warn("failed to save sparkline history:", error);
    }
}

function getLatestHistoryTimestamp() {
    let latest = null;
    for (const series of Object.values(historyByDevice)) {
        if (!Array.isArray(series)) continue;
        for (const point of series) {
            if (typeof point.at === "number" && (latest === null || point.at > latest)) {
                latest = point.at;
            }
        }
    }
    return latest;
}

function loadLastUpdatedAt() {
    try {
        const raw = localStorage.getItem(LAST_UPDATED_STORAGE_KEY);
        const stored = Number(raw);
        if (Number.isFinite(stored) && stored > 0) return stored;
    } catch (error) {
        console.warn("failed to load last-updated timestamp:", error);
    }
    return getLatestHistoryTimestamp();
}

function markUpdated(timestamp = Date.now()) {
    if (!Number.isFinite(timestamp) || timestamp <= 0) return;
    lastUpdatedAt = timestamp;
    hasLoadedOnce = true;
    try {
        localStorage.setItem(LAST_UPDATED_STORAGE_KEY, String(timestamp));
    } catch (error) {
        console.warn("failed to save last-updated timestamp:", error);
    }
    updateLastUpdatedLabel();
}

function moistureStatusText(value) {
    if (value < 30) return "Action: irrigation required";
    if (value > 70) return "High moisture";
    return "Optimal moisture";
}

function tempStatusText(value) {
    if (value < 18) return "Too cool";
    if (value > 28) return "Too warm";
    return "Ambient climate";
}

function formatRelativeTime(timestamp) {
    if (!Number.isFinite(timestamp) || timestamp <= 0) return "Waiting for first update...";
    const seconds = Math.max(0, Math.floor((Date.now() - timestamp) / 1000));
    if (seconds < 2) return "Updated just now";
    if (seconds < 60) return `Updated ${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `Updated ${minutes}m ago`;
    return `Updated ${Math.floor(minutes / 60)}h ago`;
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

    const moistureStatus = document.getElementById("moisture-status");
    const tempStatus = document.getElementById("temp-status");
    if (moistureStatus) moistureStatus.textContent = "No telemetry";
    if (tempStatus) tempStatus.textContent = "No telemetry";

    const lastUpdated = getLastUpdatedElement();
    if (lastUpdated) {
        lastUpdated.textContent = hasLoadedOnce || lastUpdatedAt
            ? formatRelativeTime(lastUpdatedAt)
            : "Connection lost";
    }
}

function pushHistory(deviceId, moisture, temperature) {
    if (!historyByDevice[deviceId]) historyByDevice[deviceId] = [];
    const series = historyByDevice[deviceId];
    const last = series[series.length - 1];
    const now = Date.now();

    if (last && last.moisture === moisture && last.temperature === temperature) {
        last.at = now;
        saveHistory();
        return;
    }

    series.push({ moisture, temperature, at: now });
    if (series.length > HISTORY_LIMIT) series.shift();
    saveHistory();
}

function recordTelemetryHistory() {
    if (!globalTelemetry?.tiles?.length) return;

    const avgMoisture =
        globalTelemetry.tiles.reduce((sum, t) => sum + t.moisture_level, 0) / globalTelemetry.tiles.length;
    const avgTemp =
        globalTelemetry.tiles.reduce((sum, t) => sum + t.temperature, 0) / globalTelemetry.tiles.length;

    pushHistory("hub", Number(avgMoisture.toFixed(1)), Number(avgTemp.toFixed(1)));

    globalTelemetry.tiles.forEach((tile) => {
        pushHistory(tile.tile_id, tile.moisture_level, tile.temperature);
    });
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
    if (lastUpdated) lastUpdated.textContent = formatRelativeTime(lastUpdatedAt);
}

async function fetchPlantStats() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error(`http error! status: ${response.status}`);

        globalTelemetry = await response.json();

        if (!globalTelemetry.hub_id) {
            setOfflineState("Waiting for hub");
            setLoading(false);
            return;
        }

        markUpdated(Date.now());
        setLoading(false);
        recordTelemetryHistory();
        updateDeviceSelector();
        renderStats();
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

        let html = `<button type="button" class="pill ${currentSelection === "hub" ? "active" : ""}" data-id="hub">Main Hub</button>`;

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
    updateDeviceSelector();
    if (globalTelemetry) {
        renderStats();
    } else {
        renderHistorySparklines();
    }
}

function getCurrentReadings() {
    let moisture = 0;
    let temperature = 0;

    if (currentSelection === "hub") {
        if (globalTelemetry.tiles?.length) {
            moisture =
                globalTelemetry.tiles.reduce((sum, t) => sum + t.moisture_level, 0) /
                globalTelemetry.tiles.length;
            temperature =
                globalTelemetry.tiles.reduce((sum, t) => sum + t.temperature, 0) /
                globalTelemetry.tiles.length;
        }
        return {
            moisture,
            temperature,
            moistureLabel: "Avg Soil Moisture",
            tempLabel: "Avg Temperature",
            moistureDisplay: `${moisture.toFixed(1)}%`,
            tempDisplay: `${temperature.toFixed(1)}°C`,
        };
    }

    const tile = globalTelemetry.tiles?.find((t) => t.tile_id === currentSelection);
    if (!tile) return null;

    return {
        moisture: tile.moisture_level,
        temperature: tile.temperature,
        moistureLabel: "Tile Moisture",
        tempLabel: "Tile Temperature",
        moistureDisplay: `${tile.moisture_level}%`,
        tempDisplay: `${tile.temperature}°C`,
    };
}

function renderStats() {
    if (!globalTelemetry) return;

    const readings = getCurrentReadings();
    if (!readings) return;

    document.getElementById("card1-label").textContent = readings.moistureLabel;
    document.getElementById("moisture-val").textContent = readings.moistureDisplay;
    document.getElementById("card2-label").textContent = readings.tempLabel;
    document.getElementById("temp-val").textContent = readings.tempDisplay;

    document.getElementById("moisture-status").textContent = moistureStatusText(readings.moisture);
    document.getElementById("temp-status").textContent = tempStatusText(readings.temperature);

    document.getElementById("water-val").textContent = globalTelemetry.water_level_ok ? "OK" : "LOW";
    document.getElementById("water-val").style.color = globalTelemetry.water_level_ok
        ? "var(--green)"
        : "#e63946";
    document.getElementById("water-status").textContent = globalTelemetry.water_level_ok
        ? "Reservoir level healthy"
        : "Refill reservoir soon";

    document.getElementById("ai-status").textContent = globalTelemetry.ai_health_status || "Healthy";
    document.getElementById("ai-status-detail").textContent = "Local AI vision";

    renderHistorySparklines();

    const cameraFeed = document.getElementById("camera-feed");
    if (cameraFeed && globalTelemetry.camera_feed_url) {
        try {
            const nextSrc = new URL(globalTelemetry.camera_feed_url, window.location.href).href;
            if (cameraFeed.src !== nextSrc) {
                cameraFeed.src = globalTelemetry.camera_feed_url;
            }
            cameraFeed.alt = `Optical feed — ${globalTelemetry.hub_id || "hub"}`;
        } catch (error) {
            console.warn("invalid camera feed url:", globalTelemetry.camera_feed_url, error);
        }
    }

    const systemStatus = document.getElementById("system-status");
    if (systemStatus) {
        const activeLabel = currentSelection === "hub" ? globalTelemetry.hub_id : currentSelection;
        systemStatus.textContent = `Active: ${activeLabel}`;
        systemStatus.style.borderColor = "var(--green)";
    }

    updateLastUpdatedLabel();
}

function renderHistorySparklines() {
    const series = historyByDevice[currentSelection] || [];
    renderSparkline(
        "moisture-sparkline",
        series.map((point) => point.moisture)
    );
    renderSparkline(
        "temp-sparkline",
        series.map((point) => point.temperature)
    );
}

function initDashboard() {
    setLoading(true);
    updateLastUpdatedLabel();
    renderHistorySparklines();
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
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDashboard);
} else {
    initDashboard();
}
