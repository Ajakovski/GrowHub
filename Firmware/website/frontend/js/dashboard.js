const API_URL = "http://localhost:8000/api/web/plant-stats";
const HISTORY_LIMIT = 20;

let globalTelemetry = null;
let currentSelection = "hub";
let knownTileIds = null;
let lastUpdatedAt = null;
let hasLoadedOnce = null;
const historyByDevice = {};

function moistureStatusText(value) {
    if (value < 30) return "Action: irrigation required";
    if (value > 70) return "High moisture";
    return "Optimal moisture";
}

function tempStatusText(value) {
    if (value < 18) return "Too cool";
    if (value > 28) return "Too warm";
    return "Optimal temperature";
}

function formatRelativeTime(timestamp) {
    if (!timestamp) return "Waiting for first update...";
    const seconds = Math.max(0, Math.floor((Date.now() - timestamp) / 1000));
    if (seconds < 2) return "Updated just now";
    if (seconds < 60) return `Updated ${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `Updated ${minutes} ago`;
    return `Updated ${Math.floor(minutes / 60)}h ago`;
}

function setLoading(isLoading) {
    const grid = document.getElementById("metric-grid");
    if (grid) grid.classList.toggle("is-loading", isLoading);
}

function setOfflineState(message = "Offline / Connection error") {
    const systemStatus = document.getElementById("system-status");

    if (systemStatus) {
        systemStatus.textContent = message;
        systemStatus.style.borderColor = "#e63946";
    }

    const moistureStatus = document.getElementById("moisture-status");
    const tempStatus = document.getElementById("temp-status");
    if (moistureStatus) moistureStatus.textContent = "No telemetry";
    if (tempStatus) tempStatus.textContent = "No telemetry";

    const lastUpdated = document.getElementById("last-updated");
    if (lastUpdated)
        lastUpdated.textContent = hasLoadedOnce
            ? formatRelativeTime(lastUpdatedAt)
            : "Connection lost";
}

function pushHistory(deviceId, moisture, temperature) {
    if (!historyByDevice[deviceId]) historyByDevice[deviceId] = [];
    const series = historyByDevice[deviceId];
    const last = series[series.length - 1];

    if (
        last &&
        last.moisture === moisture &&
        last.temperature === temperature
    ) {
        last.at = Date.now();
        return;
    }

    series.push({ moisture, temperature, at: Date.now() });
    if (series.length > HISTORY_LIMIT) series.shift();
}

function recordTelemetryHistory() {
    if (!globalTelemetry?.tiles?.length) return;

    const avgMoisture =
        globalTelemetry.tiles.reduce((sum, t) => sum + t.moisture_level, 0) /
        globalTelemetry.tiles.length;
    const avgTemp =
        globalTelemetry.tiles.reduce((sum, t) => sum + t.temperature, 0) /
        globalTelemetry.tiles.length;

    pushHistory(
        "hub",
        Number(avgMoisture.toFixed(1)),
        Number(avgTemp.toFixed(1)),
    );

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

function renderSparkLine(svgId, values) {
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
    const lastUpdated = document.getElementById("last-updated");
    if (!lastUpdated)
        lastUpdated.textContent = formatRelativeTime(lastUpdatedAt);
}

async function fetchPlantStats() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok)
            throw new Error(`http error! status: ${response.status}`);

        globalTelemetry = await response.json();

        if (!globalTelemetry.hub_id) {
            setOfflineState("Waiting for hub");
            setLoading(false);
            return;
        }

        lastUpdatedAt = Date.now();
        hasLoadedOnce = true;
        setLoading(false);
        recordTelemetryHistory();
        updateDeviceSelector();
        renderStats();
        updateLastUpdatedLabel();
    } catch (error) {
        console.error("failed to load plant telemetry:", error);
        setLoading(false);
        setOfflineState();
    }
}

function updateDeviceSelector() {
    const selector = document.getElementById("device-selector");
    if (!selector || !globalTelemetry) return;

    const tileIds = (globalTelemetry.tiles || [])
        .map((tile) => tile.tile_id)
        .join(",");

    if (knownTileIds !== tileIds) {
        knownTileIds = tileIds;

        let html = `<button type="button" class="pill ${currentSelection === "hub" ? "active" : ""}" data-id="hub">Main Hub</button>`;

        if (globalTelemetry.tiles) {
            globalTelemetry.tiles.forEach((tile) => {
                const isActive =
                    currentSelection === tile.tile_id ? "active" : "";
                html += `<button type="button" class="pill ${isActive}" data-id="${tile.tile_id}">${tile.tile_id.replace("_", " ").toUpperCase()}</button>`;
            });
        }

        selector.innerHTML = html;
        return;
    }

    selector.querySelectorAll("button[data-id]").forEach((button) => {
        button.classList.toggle(
            "active",
            button.getAttribute("data-id") === currentSelection,
        );
    });
}

function selectDevice(deviceId) {
    if (!deviceId || deviceId === currentSelection) return;
    currentSelection = deviceId;
    updateDeviceSelector();
    renderStats();
}

function getCurrentReadings() {
    let moisture = 0;
    let temperature = 0;

    if (currentSelection === "hub") {
        if (globalTelemetry.tiles?.length) {
            moisture =
                globalTelemetry.tiles.reduce(
                    (sum, t) => sum + t.moisture_level,
                    0,
                ) / globalTelemetry.tiles.length;
            temperature =
                globalTelemetry.tiles.reduce(
                    (sum, t) => sum + t.temperature,
                    0,
                ) / globalTelemetry.tiles.length;
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

    const tile = globalTelemetry.tiles?.find(
        (t) => t.tile_id === currentSelection,
    );
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
    document.getElementById("moisture-val").textContent =
        readings.moistureDisplay;
    document.getElementById("card2-label").textContent = readings.tempLabel;
    document.getElementById("temp-val").textContent = readings.tempDisplay;

    document.getElementById("moisture-status").textContent = moistureStatusText(
        readings.moisture,
    );
    document.getElementById("temp-status").textContent = tempStatusText(
        readings.temperature,
    );

    document.getElementById("water-val").textContent =
        globalTelemetry.water_level_ok ? "OK" : "LOW";
    document.getElementById("water-val").style.color =
        globalTelemetry.water_level_ok ? "var(--green)" : "#e63946";
    document.getElementById("water-status").textContent =
        globalTelemetry.water_level_ok
            ? "Reservoir level good"
            : "Refill reservoir soon";

    document.getElementById("ai-status").textContent =
        globalTelemetry.ai_health_status || "Healthy";
    document.getElementById("ai-status-detail").textContent = "Local AI vision";

    const series = historyByDevice[currentSelection] || [];
    renderSparkLine(
        "moisture-sparkline",
        series.map((point) => point.moisture),
    );
    renderSparkLine(
        "temp-sparkline",
        series.map((point) => point.temperature),
    );

    const cameraFeed = document.getElementById("camera-feed");
    if (
        cameraFeed &&
        globalTelemetry.camera_feed_url &&
        cameraFeed.src !==
            new URL(globalTelemetry.camera_feed_url, window.location.href).href
    ) {
        cameraFeed.src = globalTelemetry.camera_feed_url;
        cameraFeed.alt = `Optical Feed - ${globalTelemetry.hub_id || "hub"}`;
    }

    const systemStatus = document.getElementById("system-status");
    const activeLabel =
        currentSelection === "hub" ? globalTelemetry.hub_id : currentSelection;
    systemStatus.textContent = `Active: ${activeLabel}`;
    systemStatus.style.borderColor = "var(--green)";
}

document.addEventListener("DOMContentLoaded", () => {
    setLoading(true);
    fetchPlantStats();
    setInterval(fetchPlantStats, 5000);
    setInterval(updateLastUpdatedLabel, 1000);

    const selectorContainer = document.getElementById("device-selector");
    if (selectorContainer) {
        selectorContainer.addEventListener("click", (event) => {
            const button = event.target.closest("button[data-id]");
            if (button) {
                selectDevice(button.getAttribute("data-id"));
            }
        });
    }
});
