from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from routers.device import (
    current_state,
    get_latest_frame,
    get_latest_frame_at,
    wait_for_frame_change,
)

router = APIRouter()


@router.get("/tiles")
async def get_hardware_catalog():
    return [
        {
            "id": "module_15x15",
            "name": "15x15 Hydroponic Base Tile",
            "category": "modules",
            "price": 39.99,
        },
        {
            "id": "hub_ai",
            "name": "Central Control Hub",
            "category": "tech",
            "price": 59.99,
        },
    ]


@router.get("/plant-stats")
async def get_plant_stress():
    return current_state


@router.get("/camera")
async def get_camera_still():
    frame = get_latest_frame()
    if not frame:
        raise HTTPException(status_code=503, detail="No camera frame yet")

    return Response(
        content=frame,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
            "X-Frame-Captured-At": str(get_latest_frame_at()),
        },
    )


@router.get("/camera/stream")
async def get_camera_stream():
    boundary = "frame"

    async def mjpeg_generator():
        last_sent_at = 0.0
        while True:
            frame, captured_at = await wait_for_frame_change(last_sent_at, timeout=1.0)
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