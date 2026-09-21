from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class TelemetryPayload(BaseModel):
    device_id: str
    active_tiles: int
    moisture_level: float
    temperature: float
    water_level_ok: bool


@router.post("/telemetry")
async def recieve_telemetry(data: TelemetryPayload):
    print(f"recieved data from {data.device_id}: moisture is {data.moisture_level}%")

    return {
        "status": "success",
        "action": "sleep",
        "next_wake_minutes": 15
    }