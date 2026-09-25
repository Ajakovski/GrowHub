import asyncio
import time
from typing import List, Optional, Tuple

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

router = APIRouter()


CAMERA_STREAM_URL = "http://localhost:8000/api/web/camera/stream"
CAMERA_STILL_URL = "http://localhost:8000/api/web/camera"

_latest_frame: Optional[bytes] = None
_latest_frame_at: float = 0.0
_frame_event = asyncio.Event()

current_state = {
    "hub_id": "Offline Hub",
    "water_level_ok": True,
    "ai_health_status": "Waiting for hardware...",
    "camera_feed_url": "CAMERA_STILL_URL",
    "camera_online": False,
    "active_tiles": 2,
    "tiles": [
        {"tile_id": "tile_1", "moisture_level": 0.0, "temperature": 0.0},
        {"tile_id": "tile_2", "moisture_level": 0.0, "temperature": 0.0},
    ],
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


def get_latest_frame() -> Optional[bytes]:
    return _latest_frame


def get_latest_frame_at() -> float:
    return _latest_frame_at


def _set_latest_frame(frame_bytes: bytes) -> None:
    global _latest_frame, _latest_frame_at
    _latest_frame = frame_bytes
    _latest_frame_at = time.time()
    current_state["camera_feed_url"] = CAMERA_STILL_URL
    current_state["camera_online"] = True
    _frame_event.set()


async def wait_for_frame_change(
    since: float, timeout: float = 1.0
) -> Tuple[Optional[bytes], float]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _latest_frame is not None and _latest_frame_at > since:
            return _latest_frame, _latest_frame_at
        try:
            await asyncio.wait_for(_frame_event.wait(), timeout=0.2)
        except asyncio.TimeoutError:
            continue
        finally:
            _frame_event.clear()
    return _latest_frame, _latest_frame_at


@router.post("/telemetry")
async def receive_telemetry(data: TelemetryPayload):
    preserved = {
        "camera_feed_url": current_state.get("camera_feed_url", CAMERA_STILL_URL),
        "camera_online": current_state.get("camera_online", False),
        "ai_health_status": current_state.get(
            "ai_health_status", "Waiting for hardware..."
        ),
    }

    current_state.clear()
    current_state.update(preserved)
    current_state.update(data.model_dump())

    if len(data.tiles) > 0:
        first_tile = data.tiles[0]
        current_state["soil_moisture_percent"] = first_tile.moisture_level
        current_state["temperature_c"] = first_tile.temperature

    current_state["water_level_ok"] = data.water_level_ok
    current_state["ai_health_status"] = "Live (simulator)"

    print(f"hub {data.hub_id} reported {data.active_tiles} active tiles.")
    for tile in data.tiles:
        print(
            f" - {tile.tile_id}: moisture {tile.moisture_level}% | temp {tile.temperature}°C"
        )

    return {
        "status": "success",
        "action": "sleep",
        "next_wake_minutes": 15,
    }


@router.post("/camera")
async def recieve_camera_frame(frame: UploadFile = File(...)):
    if not frame.content_type or not frame.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Expected a image upload")

    frame_bytes = await frame.read()
    if not frame_bytes:
        raise HTTPException(status_code=400, detail="Empty frame")

    _set_latest_frame(frame_bytes)
    return {
        "status": "success",
        "bytes": len(frame_bytes),
        "camera_feed_url": CAMERA_STILL_URL,
    }
