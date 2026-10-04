from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from typing import Literal, Optional
import time

import history
from routers.device import Hub, get_hub, hubs

router = APIRouter()


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


@router.get("/hubs")
async def list_hubs():
    now = time.time()
    return [{"hub_id": hub.hub_id, **hub.status(now)} for hub in sorted(hubs.values(), key=lambda h: h.hub_id)]


@router.get("/plant-stats")
async def get_plant_stats(hub: Optional[str] = None):
    record = _resolve_hub(hub)
    if record is None:
        return {"hub_id": None, "hub_online": False, "last_telemetry_at": None, "tiles": [], "alerts": []}
    return record.snapshot(time.time())


@router.get("/history")
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


@router.get("/camera")
async def get_camera_still(hub: Optional[str] = None):
    record = _resolve_hub(hub)
    if record is None or not record.latest_frame:
        raise HTTPException(status_code=503, detail="No camera frame yet")

    return Response(
        content=record.latest_frame,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
            "X-Frame-Captured-At": str(record.latest_frame_at),
        },
    )


@router.get("/camera/stream")
async def get_camera_stream(hub: Optional[str] = None):
    record = _resolve_hub(hub)
    if record is None:
        raise HTTPException(status_code=503, detail="No camera frame yet")
        
    boundary = "frame"

    async def mjpeg_generator():
        last_sent_at = 0.0
        while True:
            frame, captured_at = await record.wait_for_frame_change(last_sent_at, timeout=1.0)
            if frame and captured_at > last_sent_at:
                last_sent_at = captured_at
                yield (
                    f"--{boundary}\r\n"
                    f"Content-Type: image/jpeg\r\n"
                    f"Content-Length: {len(frame)}\r\n\r\n"
                ).encode("utf-8") + frame + b"\r\n"

    return StreamingResponse(
        mjpeg_generator(),
        media_type=f"multipart/x-mixed-replace; boundary={boundary}",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )
