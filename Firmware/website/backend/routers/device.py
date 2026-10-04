from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Tuple
import asyncio
import time

import history

router = APIRouter()

CAMERA_STREAM_URL = "http://localhost:8000/api/web/camera/stream"
CAMERA_STILL_URL = "http://localhost:8000/api/web/camera"

NEXT_WAKE_MINUTES = 15
MIN_OFFLINE_SECONDS = 30
MISSED_REPORTS_BEFORE_OFFLINE = 3
DRY_MOISTURE_PERCENT = 30.0
SUSTAINED_READINGS = 3

_latest_frame: Optional[bytes] = None
_latest_frame_at: float = 0.0
_frame_event = asyncio.Event()

_last_telemetry_at: Optional[float] = None
_telemetry_interval: Optional[float] = None
_low_water_streak = 0

current_state = {
    "hub_id": "Offline Hub",
    "water_level_ok": True,
    "ai_health_status": "Waiting for hardware...",
    "camera_feed_url": CAMERA_STILL_URL,
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


async def wait_for_frame_change(since: float, timeout: float = 1.0) -> Tuple[Optional[bytes], float]:
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


def get_hub_status(now: float) -> dict:
    if _last_telemetry_at is None:
        return {"hub_online": False, "last_telemetry_at": None}

    # Until a second report arrives, assume the hub follows the sleep schedule we hand it.
    interval = _telemetry_interval or NEXT_WAKE_MINUTES * 60
    offline_after = max(MIN_OFFLINE_SECONDS, MISSED_REPORTS_BEFORE_OFFLINE * interval)
    return {
        "hub_online": now - _last_telemetry_at <= offline_after,
        "last_telemetry_at": int(_last_telemetry_at * 1000),
    }


def _tile_label(tile_id: str) -> str:
    return tile_id.replace("_", " ").title()


def get_alerts() -> List[dict]:
    alerts = []

    for tile in current_state.get("tiles", []):
        tile_id = tile["tile_id"]
        recent = history.get_recent_moisture(tile_id, SUSTAINED_READINGS)
        if len(recent) == SUSTAINED_READINGS and all(m < DRY_MOISTURE_PERCENT for m in recent):
            alerts.append({
                "kind": "dry_tile",
                "device": tile_id,
                "message": f"{_tile_label(tile_id)} has been below {DRY_MOISTURE_PERCENT:.0f}% moisture "
                           f"for the last {SUSTAINED_READINGS} readings.",
            })

    if _low_water_streak >= SUSTAINED_READINGS:
        alerts.append({
            "kind": "reservoir_low",
            "device": "hub",
            "message": f"Reservoir has been low for the last {_low_water_streak} readings. Refill it.",
        })

    return alerts


@router.post("/telemetry")
async def receive_telemetry(data: TelemetryPayload):
    global _last_telemetry_at, _telemetry_interval, _low_water_streak

    now = time.time()
    if _last_telemetry_at is not None:
        _telemetry_interval = now - _last_telemetry_at
    _last_telemetry_at = now
    _low_water_streak = 0 if data.water_level_ok else _low_water_streak + 1

    preserved = {
        "camera_feed_url": current_state.get("camera_feed_url", CAMERA_STILL_URL),
        "camera_online": current_state.get("camera_online", False),
        "ai_health_status": current_state.get("ai_health_status", "Waiting for hardware..."),
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

    if data.tiles:
        rows = [(tile.tile_id, tile.moisture_level, tile.temperature) for tile in data.tiles]
        avg_moisture = sum(tile.moisture_level for tile in data.tiles) / len(data.tiles)
        avg_temp = sum(tile.temperature for tile in data.tiles) / len(data.tiles)
        rows.append(("hub", avg_moisture, avg_temp))
        history.record_readings(now, rows)

    print(f"hub {data.hub_id} reported {data.active_tiles} active tiles.")
    for tile in data.tiles:
        print(f" - {tile.tile_id}: moisture {tile.moisture_level}% | temp {tile.temperature}°C")

    return {
        "status": "success",
        "action": "sleep",
        "next_wake_minutes": NEXT_WAKE_MINUTES,
    }


@router.post("/camera")
async def receive_camera_frame(frame: UploadFile = File(...)):
    if not frame.content_type or not frame.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Expected an image upload")

    frame_bytes = await frame.read()
    if not frame_bytes:
        raise HTTPException(status_code=400, detail="Empty frame")

    _set_latest_frame(frame_bytes)
    return {
        "status": "success",
        "bytes": len(frame_bytes),
        "camera_feed_url": CAMERA_STILL_URL,
    }
