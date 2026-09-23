const API_URL = "http://localhost:8000/api/web/plant-stats"
let globalTelemetry = null;
let currentSelection = 'hub';

async function fetchPlantStats() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error('http error! status: ${response.status}');

        globalTelemetry = await response.json();

        if (!globalTelemetry.hub_id) return;
        
        updateDeviceSelector();
        renderStats();

    } catch (error) {
        console.error("failed to load plant telemetry:", error);
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

    if (currentSelection === 'hub') {
        let avgMoisture = 0;
        let avgTemp = 0;

        if (globalTelemetry.tiles && globalTelemetry.tiles.length > 0) {
            avgMoisture = globalTelemetry.tiles.reduce((sum, t) => sum + t.moisture_level, 0) / globalTelemetry.tiles.length;
            avgTemp = globalTelemetry.tiles.reduce((sum, t) => sum + t.temperature, 0) / globalTelemetry.tiles.length;
        }

        document.getElementById("card1-label").textContent = "Avg Soil Moisture";
        document.getElementById("moisture-val").textContent = `${avgMoisture.toFixed(1)}%`;

        document.getElementById("card2-label").textContent = "Avg temperature";
        document.getElementById("temp-val").textContent = `${avgTemp.toFixed(1)}°C`

    } else {
        const tile = globalTelemetry.tiles.find(t => t.tile_id === currentSelection);

        if (tile) {
            document.getElementById("card1-label").textContent = "Tile Moisture";
            document.getElementById("moisture-val").textContent = `${tile.moisture_level}%`;

            document.getElementById("card2-label").textContent = "Tile Temperature";
            document.getElementById("temp-val").textContent = `${tile.temperature}°C`;
        }
    }

    document.getElementById("water-val").textContent = globalTelemetry.water_level_ok ? "OK" : "LOW";
    document.getElementById("water-val").style.color = globalTelemetry.water_level_ok ? "var(--green)" : "#e63946";
    document.getElementById("ai-status").textContent = globalTelemetry.ai_health_status || "Healthy";

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