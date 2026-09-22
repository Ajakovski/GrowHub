from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class TileData(BaseModel):
    tile_id: str
    moisture_level: float
    temperature: float

class TelemetryPayload(BaseModel):
    hub_id: str
    water_level_ok: bool
    active_tiles: int
    tiles: List[TileData]


@router.post("/telemetry")
async def recieve_telemetry(data: TelemetryPayload):
    print(f"hub {data.hub_id} reported {data.active_tiles} active tiles.")
    
    for tile in data.tiles:
        print(f" - {tile.tile_id}: moisture {tile.moisture_level}% | temp {tile.temperature}C")

    return {
        "status": "success",
        "action": "sleep",
        "next_wake_minutes": 15
    }