from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Literal, Optional
import asyncio
import re
import time

import history
import mailer
import plants
import ratelimit
from logutil import get_logger
from requestutil import client_ip
from routers.auth import require_owner, require_viewer
from routers.device import CAMERA_SOURCE_STOCK, Hub, get_hub, hubs

router = APIRouter()
dashboard = [Depends(require_viewer)]
owner_only = [Depends(require_owner)]
_contact_limiter = ratelimit.RateLimiter(limit=5, window_seconds=600)
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
web_log = get_logger("web")


class CameraSourceUpdate(BaseModel):
    source: Literal["webcam", "stock"]


class HubPlantsUpdate(BaseModel):
    plant_ids: List[str] = Field(default_factory=list, max_length=20)
    tile_plants: Dict[str, List[str]] = Field(default_factory=dict)


class ContactMessage(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=120)
    topic: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=10, max_length=4000)
    # Honeypot — bots fill this; humans leave it empty.
    company: str = Field(default="", max_length=120)

    @field_validator("name", "topic", "message")
    @classmethod
    def strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field is required")
        return cleaned

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        cleaned = value.strip()
        if not _EMAIL_PATTERN.match(cleaned):
            raise ValueError("Enter a valid email address")
        return cleaned


def _resolve_hub(hub_id: Optional[str]) -> Optional[Hub]:
    hub = get_hub(hub_id)
    if hub is None and hub_id is not None:
        raise HTTPException(status_code=404, detail=f"Unknown hub '{hub_id}'")
    return hub


@router.post("/contact")
async def submit_contact(body: ContactMessage, request: Request):
    client = client_ip(request)
    if body.company.strip():
        # Pretend success so scrapers don't retry.
        web_log.info("contact honeypot tripped client=%s", client)
        return {"status": "sent"}

    if not _contact_limiter.allow(f"{client}:{body.email.lower()}"):
        web_log.warning("contact rate-limited client=%s email=%s", client, body.email)
        raise HTTPException(status_code=429, detail="Too many messages. Try again in a few minutes.")

    try:
        mailer.send_contact_email(
            name=body.name,
            email=body.email,
            topic=body.topic,
            message=body.message,
        )
    except mailer.EmailError as error:
        web_log.error("contact send failed client=%s email=%s error=%s", client, body.email, error)
        raise HTTPException(status_code=502, detail=str(error)) from error

    web_log.info("contact sent client=%s email=%s topic=%s", client, body.email, body.topic)
    return {"status": "sent"}


@router.get("/tiles")
async def get_hardware_catalog():
    return [
        {
            "id": "growhub_hub",
            "name": "GrowHub Hub",
            "tagline": "The base that runs everything",
            "category": "tech",
            "category_label": "Hub & electronics",
            "description": (
                "The central power and water unit. It runs continuous-loop circulation, nutrient and climate "
                "control, and feeds every planter tile daisy-chained to it."
            ),
            "price": "Under $300",
            "image": "growhub_render_v2.png",
            "badge": "Core",
            "specs": [
                {"label": "Reservoir", "value": "18 L"},
                {"label": "Footprint", "value": "40 × 70 cm"},
                {"label": "Role", "value": "Power, water, AI"},
            ],
            "features": [
                "Shared reservoir with water heater",
                "EC, pH, level and temp sensing",
                "Drives the continuous water loop",
                "Talks to the GrowHub dashboard and AI",
            ],
        },
        {
            "id": "planter_tile_40x70",
            "name": "40 × 70 cm DWC Planter Tile",
            "tagline": "One full grow floor",
            "category": "modules",
            "category_label": "Planter tiles",
            "description": (
                "A complete Deep Water Culture floor: 18 clay-pebble cups under a smart LED canopy. "
                "Stack or daisy-chain tiles to scale harvest without changing the footprint."
            ),
            "price": "$90",
            "image": "growhub_tile_render_v1.png",
            "badge": None,
            "specs": [
                {"label": "Cups", "value": "18 (3 × 6)"},
                {"label": "Footprint", "value": "40 × 70 cm"},
                {"label": "Canopy", "value": "Smart LED"},
            ],
            "features": [
                "Full DWC basin and planter grid",
                "Per-tile air, humidity, light and flow sensors",
                "Daisy-chains to the Hub for power and water",
                "Stacks vertically on the same footprint",
            ],
        },
        {
            "id": "growhub_stack",
            "name": "Stacked GrowHub tower",
            "tagline": "Grow up, not out",
            "category": "modules",
            "category_label": "Planter tiles",
            "description": (
                "Add floors on the same 40 × 70 cm pad. Each level keeps its own DWC grid and canopy while "
                "the Hub below still runs the shared water loop."
            ),
            "price": "From $90 / floor",
            "image": "growhub_stack_poster.jpg",
            "badge": "Scale",
            "specs": [
                {"label": "Per floor", "value": "1 tile"},
                {"label": "Max floors", "value": "Up to 3 / hub"},
                {"label": "Footprint", "value": "Still 40 × 70 cm"},
            ],
            "features": [
                "Triple growing area without more floor space",
                "Each floor stays a complete grow module",
                "Same dashboard for every level",
                "Expand one floor at a time",
            ],
        },
    ]


@router.get("/plant-catalog", dependencies=dashboard)
async def get_plant_catalog():
    return {"plants": plants.catalog()}


@router.get("/hubs", dependencies=dashboard)
async def list_hubs():
    now = time.time()
    return [{"hub_id": hub.hub_id, **hub.status(now)} for hub in sorted(hubs.values(), key=lambda h: h.hub_id)]


@router.get("/plant-stats", dependencies=owner_only)
async def get_plant_stats(hub: Optional[str] = None):
    record = _resolve_hub(hub)
    if record is None:
        web_log.info("plant-stats empty requested_hub=%s", hub)
        return {
            "hub_id": None,
            "hub_online": False,
            "last_telemetry_at": None,
            "tiles": [],
            "alerts": [],
            "crops": plants.plants_payload({}),
        }
    snapshot = record.snapshot(time.time())
    # Dashboard polls this every few seconds — keep the happy path quiet.
    web_log.debug(
        "plant-stats hub=%s online=%s last_telemetry_at=%s tiles=%s",
        snapshot.get("hub_id"),
        snapshot.get("hub_online"),
        snapshot.get("last_telemetry_at"),
        len(snapshot.get("tiles") or []),
    )
    return snapshot


@router.put("/plants", dependencies=dashboard)
async def set_hub_plants(update: HubPlantsUpdate, hub: Optional[str] = None):
    record = _resolve_hub(hub)
    if record is None:
        raise HTTPException(status_code=404, detail="No hub has reported yet")

    plant_ids = plants.normalise_plant_ids(update.plant_ids)
    if not plant_ids:
        raise HTTPException(status_code=400, detail="Pick at least one plant")

    known_tiles = {tile.get("tile_id") for tile in record.state.get("tiles", []) if tile.get("tile_id")}
    tile_plants = {}
    for tile_id, tile_ids in update.tile_plants.items():
        if known_tiles and tile_id not in known_tiles:
            continue
        cleaned = plants.normalise_plant_ids(tile_ids)
        if cleaned:
            tile_plants[tile_id] = cleaned

    # When the UI only picks hub-level plants, every known tile grows the same mix.
    if not tile_plants and known_tiles:
        tile_plants = {tile_id: list(plant_ids) for tile_id in sorted(known_tiles)}

    record.plants = {
        "configured": True,
        "plant_ids": plant_ids,
        "tile_plants": tile_plants,
    }
    history.save_hub_plants(record.hub_id, record.plants)
    return {"hub_id": record.hub_id, "crops": plants.plants_payload(record.plants)}


@router.get("/history", dependencies=dashboard)
async def get_history(
    hub: Optional[str] = None,
    device: str = "hub",
    range_key: Literal["1h", "24h", "7d"] = Query("1h", alias="range"),
):
    record = _resolve_hub(hub)
    return {
        "hub": record.hub_id if record else None,
        "device": device,
        "range": range_key,
        "points": history.get_history(record.hub_id, device, range_key, time.time()) if record else [],
    }


@router.put("/camera-source", dependencies=owner_only)
async def set_camera_source(update: CameraSourceUpdate, hub: Optional[str] = None):
    record = _resolve_hub(hub)
    if record is None:
        raise HTTPException(status_code=404, detail="No hub has reported yet")

    record.camera_source = update.source
    history.save_hub_camera_source(record.hub_id, update.source)
    return {"hub_id": record.hub_id, "camera_source": record.camera_source}


@router.get("/camera", dependencies=dashboard)
async def get_camera_still(hub: Optional[str] = None):
    record = _resolve_hub(hub)
    frame = record.current_frame(time.time()) if record else None
    if frame is None:
        raise HTTPException(status_code=503, detail="No camera frame yet")

    return Response(
        content=frame.data,
        media_type=frame.media_type,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
            "X-Frame-Captured-At": str(frame.captured_at),
        },
    )


@router.get("/camera/stream", dependencies=dashboard)
async def get_camera_stream(hub: Optional[str] = None):
    record = _resolve_hub(hub)
    if record is None:
        raise HTTPException(status_code=503, detail="No camera frame yet")

    boundary = "frame"

    async def mjpeg_generator():
        last_sent_at = 0.0
        while True:
            if record.camera_source == CAMERA_SOURCE_STOCK:
                await asyncio.sleep(1.0)
            else:
                await record.wait_for_frame_change(last_sent_at, timeout=1.0)
            frame = record.current_frame(time.time())
            if frame and frame.captured_at != last_sent_at:
                last_sent_at = frame.captured_at
                yield (
                    f"--{boundary}\r\n"
                    f"Content-Type: {frame.media_type}\r\n"
                    f"Content-Length: {len(frame.data)}\r\n\r\n"
                ).encode("utf-8") + frame.data + b"\r\n"

    return StreamingResponse(
        mjpeg_generator(),
        media_type=f"multipart/x-mixed-replace; boundary={boundary}",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )
