from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel
from dataclasses import dataclass, field
from typing import Dict, List, NamedTuple, Optional, Tuple
from urllib.parse import quote
import asyncio
import os
import secrets
import time

import history
import stock_images

NEXT_WAKE_MINUTES = 15
MIN_OFFLINE_SECONDS = 30
MISSED_REPORTS_BEFORE_OFFLINE = 3
CAMERA_OFFLINE_SECONDS = 60
DRY_MOISTURE_PERCENT = 30.0
SUSTAINED_READINGS = 3
NO_AI_ANALYSIS = "Not analysed yet"
CAMERA_SOURCE_WEBCAM = "webcam"
CAMERA_SOURCE_STOCK = "stock"
CAMERA_SOURCES = (CAMERA_SOURCE_WEBCAM, CAMERA_SOURCE_STOCK)

DEVICE_KEY = os.environ.get("GROWHUB_DEVICE_KEY")
if not DEVICE_KEY:
    print("WARNING: GROWHUB_DEVICE_KEY is not set, device endpoints accept unauthenticated requests.")


def require_device_key(x_device_key: Optional[str] = Header(default=None)) -> None:
    if not DEVICE_KEY:
        return
    if x_device_key is None or not secrets.compare_digest(x_device_key.encode(), DEVICE_KEY.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing device key")


router = APIRouter(dependencies=[Depends(require_device_key)])


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


def _tile_label(tile_id: str) -> str:
    return tile_id.replace("_", " ").title()


class CameraFrame(NamedTuple):
    data: bytes
    captured_at: float
    media_type: str


@dataclass
class Hub:
    hub_id: str
    state: dict = field(default_factory=dict)
    last_telemetry_at: Optional[float] = None
    telemetry_interval: Optional[float] = None
    low_water_streak: int = 0
    ai_health_status: str = NO_AI_ANALYSIS
    ai_summary: Optional[str] = None
    ai_updated_at: Optional[float] = None
    camera_source: str = CAMERA_SOURCE_WEBCAM
    latest_frame: Optional[bytes] = None
    latest_frame_at: float = 0.0
    frame_event: asyncio.Event = field(default_factory=asyncio.Event)

    def status(self, now: float) -> dict:
        if self.last_telemetry_at is None:
            return {"hub_online": False, "last_telemetry_at": None}

        interval = self.telemetry_interval or NEXT_WAKE_MINUTES * 60
        offline_after = max(MIN_OFFLINE_SECONDS, MISSED_REPORTS_BEFORE_OFFLINE * interval)
        return {
            "hub_online": now - self.last_telemetry_at <= offline_after,
            "last_telemetry_at": int(self.last_telemetry_at * 1000),
        }

    def alerts(self) -> List[dict]:
        alerts = []

        for tile in self.state.get("tiles", []):
            tile_id = tile["tile_id"]
            recent = history.get_recent_moisture(self.hub_id, tile_id, SUSTAINED_READINGS)
            if len(recent) == SUSTAINED_READINGS and all(m < DRY_MOISTURE_PERCENT for m in recent):
                alerts.append({
                    "kind": "dry_tile",
                    "device": tile_id,
                    "message": f"{_tile_label(tile_id)} has been below {DRY_MOISTURE_PERCENT:.0f}% moisture "
                               f"for the last {SUSTAINED_READINGS} readings.",
                })

        if self.low_water_streak >= SUSTAINED_READINGS:
            alerts.append({
                "kind": "reservoir_low",
                "device": "hub",
                "message": f"Reservoir has been low for the last {self.low_water_streak} readings. Refill it.",
            })

        return alerts

    def current_frame(self, now: float) -> Optional[CameraFrame]:
        if self.camera_source == CAMERA_SOURCE_STOCK:
            stock = stock_images.current_frame(now)
            return CameraFrame(stock.data, stock.captured_at, stock.media_type) if stock else None
        if self.latest_frame is None:
            return None
        return CameraFrame(self.latest_frame, self.latest_frame_at, "image/jpeg")

    def snapshot(self, now: float) -> dict:
        stock_image_count = len(stock_images.list_images())
        if self.camera_source == CAMERA_SOURCE_STOCK:
            has_frame = camera_online = stock_image_count > 0
        else:
            has_frame = self.latest_frame is not None
            camera_online = has_frame and now - self.latest_frame_at <= CAMERA_OFFLINE_SECONDS
        return {
            **self.state,
            "hub_id": self.hub_id,
            "ai_health_status": self.ai_health_status,
            "ai_summary": self.ai_summary,
            "ai_updated_at": int(self.ai_updated_at * 1000) if self.ai_updated_at else None,
            "camera_source": self.camera_source,
            "stock_image_count": stock_image_count,
            "camera_online": camera_online,
            "camera_feed_url": f"/api/web/camera?hub={quote(self.hub_id)}" if has_frame else None,
            **self.status(now),
            "alerts": self.alerts(),
        }

    def set_latest_frame(self, frame_bytes: bytes) -> None:
        self.latest_frame = frame_bytes
        self.latest_frame_at = time.time()
        self.frame_event.set()

    async def wait_for_frame_change(self, since: float, timeout: float = 1.0) -> Tuple[Optional[bytes], float]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.latest_frame is not None and self.latest_frame_at > since:
                return self.latest_frame, self.latest_frame_at
            try:
                await asyncio.wait_for(self.frame_event.wait(), timeout=0.2)
            except asyncio.TimeoutError:
                continue
            finally:
                self.frame_event.clear()
        return self.latest_frame, self.latest_frame_at


hubs: Dict[str, Hub] = {}


def load_hubs() -> None:
    for row in history.load_hubs():
        hubs[row["hub_id"]] = Hub(
            hub_id=row["hub_id"],
            state=row["state"],
            last_telemetry_at=row["last_telemetry_at"],
            telemetry_interval=row["telemetry_interval"],
            low_water_streak=row["low_water_streak"],
            ai_health_status=row["ai_status"] or NO_AI_ANALYSIS,
            ai_summary=row["ai_summary"],
            ai_updated_at=row["ai_updated_at"],
            camera_source=row["camera_source"] if row["camera_source"] in CAMERA_SOURCES else CAMERA_SOURCE_WEBCAM,
        )


def get_hub(hub_id: Optional[str] = None) -> Optional[Hub]:
    if hub_id is not None:
        return hubs.get(hub_id)
    reporting = [hub for hub in hubs.values() if hub.last_telemetry_at is not None]
    return max(reporting, key=lambda hub: hub.last_telemetry_at, default=None)


def _get_or_create_hub(hub_id: str) -> Hub:
    if hub_id not in hubs:
        hubs[hub_id] = Hub(hub_id=hub_id)
    return hubs[hub_id]


def _average(values: List[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


@router.post("/telemetry")
async def receive_telemetry(data: TelemetryPayload):
    now = time.time()
    hub = _get_or_create_hub(data.hub_id)

    if hub.last_telemetry_at is not None:
        hub.telemetry_interval = min(now - hub.last_telemetry_at, NEXT_WAKE_MINUTES * 60)
    hub.last_telemetry_at = now
    hub.low_water_streak = 0 if data.water_level_ok else hub.low_water_streak + 1
    hub.state = data.model_dump()

    if data.tiles:
        rows = [(tile.tile_id, tile.moisture_level, tile.temperature, tile.ec_level) for tile in data.tiles]
        rows.append((
            "hub",
            _average([tile.moisture_level for tile in data.tiles]),
            _average([tile.temperature for tile in data.tiles]),
            _average([tile.ec_level for tile in data.tiles if tile.ec_level is not None]),
        ))
        history.record_readings(hub.hub_id, now, rows)

    history.save_hub(hub.hub_id, hub.state, hub.last_telemetry_at, hub.telemetry_interval, hub.low_water_streak)

    print(f"hub {data.hub_id} reported {data.active_tiles} active tiles.")
    for tile in data.tiles:
        print(f" - {tile.tile_id}: moisture {tile.moisture_level}% | temp {tile.temperature}°C | ec {tile.ec_level}")

    return {
        "status": "success",
        "action": "sleep",
        "next_wake_minutes": NEXT_WAKE_MINUTES,
    }


@router.post("/camera")
async def receive_camera_frame(hub_id: str = Form(...), frame: UploadFile = File(...)):
    if not frame.content_type or not frame.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Expected an image upload")

    frame_bytes = await frame.read()
    if not frame_bytes:
        raise HTTPException(status_code=400, detail="Empty frame")

    _get_or_create_hub(hub_id).set_latest_frame(frame_bytes)
    return {
        "status": "success",
        "bytes": len(frame_bytes),
    }
