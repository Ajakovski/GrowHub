from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

current_state = {
    "plant_name": "Hub Beta 001",
    "temperature_c": 0.0,
    "soil_moisture_percent": 0.0,
    "water_level_ok": True,
    "ai_health_status": "Waiting for ESP32...",
    "camera_feed_url": "assets/img/optical-node.png"
}


class TileData(BaseModel):
    tile_id: str
    moisture_level: float
    temperature: float
    ec_level: Optional[float] = None

class TelemetryPayload(BaseModel):
    hub_id: str
    water_level_ok: bool
    active_tiles: int
    tiles: List[TileData]


@router.post("/telemetry")
async def receive_telemetry(data: TelemetryPayload):
    global current_state

    if len(data.tiles) > 0:
        first_tile = data.tiles[0]
        current_state["soil_moisture_percent"] = first_tile.moisture_level
        current_state["temperature_c"] = first_tile.temperature
        
    current_state["water_level_ok"] = data.water_level_ok
    current_state["ai_health_status"] = "Live (simulator)"
    
    print(f"hub {data.hub_id} reported {data.active_tiles} active tiles.")
    for tile in data.tiles:
        print(f" - {tile.tile_id}: moisture {tile.moisture_level}% | temp {tile.temperature}°C")
    
    return {
        "status": "success",
        "action": "sleep",
        "next_wake_minutes": 15
    }