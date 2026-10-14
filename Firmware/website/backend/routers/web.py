from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from typing import Literal, Optional
import asyncio
import time

import history
from routers.auth import require_viewer
from routers.device import CAMERA_SOURCE_STOCK, Hub, get_hub, hubs

router = APIRouter()
dashboard = [Depends(require_viewer)]


class CameraSourceUpdate(BaseModel):
    source: Literal["webcam", "stock"]


def _resolve_hub(hub_id: Optional[str]) -> Optional[Hub]:
    hub = get_hub(hub_id)
    if hub is None and hub_id is not None:
        raise HTTPException(status_code=404, detail=f"Unknown hub '{hub_id}'")
    return hub


@router.get("/tiles")
async def get_hardware_catalog():
    return [
        {
            "id": "growhub_hub",
            "name": "GrowHub Hub",
            "category": "tech",
            "description": "The central power and water unit. Runs the continuous loop water circulation and smart "
                           "controllers for every 40x70 cm tile daisy-chained to it.",
            "price": "Under $300",
        },
        {
            "id": "planter_tile_40x70",
            "name": "40x70 cm DWC Planter Tile",
            "category": "modules",
            "description": "A full Deep Water Culture (DWC) floor with 18 clay-pebble planter cups (3x6) under a "
                           "smart LED canopy. Daisy-chains to the Hub for power and water.",
            "price": "$90",
        },
    ]


@router.get("/hubs", dependencies=dashboard)
async def list_hubs():
    now = time.time()
    return [{"hub_id": hub.hub_id, **hub.status(now)} for hub in sorted(hubs.values(), key=lambda h: h.hub_id)]


@router.get("/plant-stats", dependencies=dashboard)
async def get_plant_stats(hub: Optional[str] = None):
    record = _resolve_hub(hub)
    if record is None:
        return {"hub_id": None, "hub_online": False, "last_telemetry_at": None, "tiles": [], "alerts": []}
    return record.snapshot(time.time())


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


@router.put("/camera-source", dependencies=dashboard)
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
