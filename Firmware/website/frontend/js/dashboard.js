const API_URL = "http://localhost:8000/api/web/plant-stats"

async function fetchPlantStats() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error('http error! status: ${response.status}');

        const data = await response.json();

        document.getElementById("moisture-val").textContent = `${data.moisture_level}%`;
        document.getElementById("moisture-status").textContent = data.moisture_level < 30 ? "action: irrigation required" : "Optimal moisture";

        document.getElementById("temp-val").textContent = `${data.temperature}°C`;
        document.getElementById("temp-status").textContent = "Ambient climate";

        document.getElementById("water-val").textContent = data.water_level_ok ? "OK" : "LOW";
        document.getElementById("water-val").style.color = data.water_level_ok ? "var(--green)" : "#e63946";
        
        document.getElementById("ai-status").textContent = data.ai_health_score > 70 ? "Healthy" : "needs attention";

        const systemStatus = document.getElementById("system-status");
        systemStatus.textContent = `Active: ${data.plant_name}`;
        systemStatus.style.borderColor = "var(--green)";

        if (data.camera_feed_url) {
            document.getElementById("camera-feed").src = data.camera_feed_url;
        }
    } catch (error) {
        console.error("failed to load plant telemetry:", error);
        const systemStatus = document.getElementById("system-status");
        if (systemStatus) {
            systemStatus.textContent = "Offline / Connection Error";
            systemStatus.style.borderColor = "#e63946";
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    fetchPlantStats();
    setInterval(fetchPlantStats, 5000);
})