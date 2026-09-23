const API_URL = "http://localhost:8000/api/web/plant-stats"
let globalTelemetry = null;
let currentSelection = 'hub';

function moistureStatusText(value) {
    if (value < 30) return "Action: irrigation required";
    if (value > 70) return "High moisture"
    return "Optimal moisture";
}

function tempStatusText(value) {
    if (value < 18) return "Too cool";
    if (value > 28) return "Too warm";
    return "Optimal temperature";
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
}

async function fetchPlantStats() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error(`http error! status: ${response.status}`);

        globalTelemetry = await response.json();

        if (!globalTelemetry.hub_id) {
            setOfflineState("waiting for hub");
            return;
        }
        
        updateDeviceSelector();
        renderStats();

    } catch (error) {
        console.error("failed to load plant telemetry:", error);
        setOfflineState();
    }
}

function updateDeviceSelector() {
    const selector = document.getElementById("device-selector");
    if (!selector || !globalTelemetry) return;

    let html = `<button type="button" class="pill ${currentSelection === 'hub' ? 'active' : ''}" data-id="hub">Main Hub</button>`

    if (globalTelemetry.tiles) {
        globalTelemetry.tiles.forEach(tile => {
            const isActive = currentSelection === tile.tile_id ? 'active' : '';
            html += `<button type="button" class="pill ${isActive}" data-id="${tile.tile_id}">${tile.tile_id.replace('_', ' ').toUpperCase()}</button>`
        });
    }

    selector.innerHTML = html;
}

function selectDevice(deviceId) {
    if (!deviceId) return;
    currentSelection = deviceId;
    updateDeviceSelector();
    renderStats();
}

function renderStats() {
    if (!globalTelemetry) return;

    let moisture = 0;
    let temperature = 0;

    if (currentSelection === 'hub') {

        if (globalTelemetry.tiles && globalTelemetry.tiles.length > 0) {
            moisture = globalTelemetry.tiles.reduce((sum, t) => sum + t.moisture_level, 0) / globalTelemetry.tiles.length;
            temperature = globalTelemetry.tiles.reduce((sum, t) => sum + t.temperature, 0) / globalTelemetry.tiles.length;
        }

        document.getElementById("card1-label").textContent = "Avg Soil Moisture";
        document.getElementById("moisture-val").textContent = `${moisture.toFixed(1)}%`;

        document.getElementById("card2-label").textContent = "Avg temperature";
        document.getElementById("temp-val").textContent = `${temperature.toFixed(1)}°C`;

    } else {
        const tile = globalTelemetry.tiles.find(t => t.tile_id === currentSelection);

        if (tile) {
            moisture = tile.moisture_level;
            temperature = tile.temperature;

            document.getElementById("card1-label").textContent = "Tile Moisture";
            document.getElementById("moisture-val").textContent = `${moisture}%`;

            document.getElementById("card2-label").textContent = "Tile Temperature";
            document.getElementById("temp-val").textContent = `${temperature}°C`;
        }
    }

    document.getElementById("moisture-status").textContent = moistureStatusText(moisture);
    document.getElementById("temp-status").textContent = tempStatusText(temperature);

    document.getElementById("water-val").textContent = globalTelemetry.water_level_ok ? "OK" : "LOW";
    document.getElementById("water-val").style.color = globalTelemetry.water_level_ok ? "var(--green)" : "#e63946";
    document.getElementById("water-status").textContent = globalTelemetry.water_level_ok
        ? "Reservoir level good"
        : "Refill reservoir soon"

    document.getElementById("ai-status").textContent = globalTelemetry.ai_health_status || "Healthy";
    document.getElementById("ai-status-detail").textContent = "Local AI vision";

    const cameraFeed = document.getElementById("camera-feed");
    if (cameraFeed && globalTelemetry.camera_feed_url) {
        cameraFeed.src = globalTelemetry.camera_feed_url;
        cameraFeed.alt = `Optical Feed - ${globalTelemetry.hub_id || "hub"}`;
    }

    const systemStatus = document.getElementById("system-status");
    const activeLabel = currentSelection === 'hub' ? globalTelemetry.hub_id : currentSelection;
    systemStatus.textContent = `Active: ${activeLabel}`;
    systemStatus.style.borderColor = "var(--green)";
}

document.addEventListener("DOMContentLoaded", () => {
    fetchPlantStats();
    setInterval(fetchPlantStats, 5000);

    const selectorContainer = document.getElementById("device-selector");
    if (selectorContainer) {
        selectorContainer.addEventListener("click", (event) => {
            const button = event.target.closest("button[data-id]")
            if (button) {
                selectDevice(button.getAttribute("data-id"));
            }
        });
    }
});