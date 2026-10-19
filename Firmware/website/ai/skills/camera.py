import base64
import time
from typing import Optional

from backend_client import BackendError, get_bytes
from skills.registry import SkillResult, skill

STALE_PHOTO_SECONDS = 120


def fetch_latest_frame(hub_id: Optional[str]) -> tuple[bytes, float, str]:
    params = {"hub": hub_id} if hub_id else {}
    frame, headers = get_bytes("/api/web/camera", params)
    captured_at = float(headers.get("X-Frame-Captured-At") or 0)
    media_type = headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
    return frame, captured_at, media_type


@skill(
    "get_latest_photo",
    "Look at the most recent photo from a hub's camera to visually check the plants, for example leaf "
    "colour, wilting, spots or growth.",
    {
        "hub_id": {
            "type": "string",
            "description": "Hub whose camera to use. Omit to use the hub that reported most recently.",
        }
    },
)
def get_latest_photo(hub_id: Optional[str] = None):
    try:
        frame, captured_at, media_type = fetch_latest_frame(hub_id)
    except BackendError as error:
        if error.status_code == 503:
            return {"error": "This hub has not sent a camera photo yet."}
        raise

    age_seconds = int(time.time() - captured_at) if captured_at else None
    encoded = base64.b64encode(frame).decode("ascii")
    return SkillResult(
        data={
            "photo": "attached in the next message",
            "age_seconds": age_seconds,
            "stale": age_seconds is not None and age_seconds > STALE_PHOTO_SECONDS,
        },
        image_data_url=f"data:{media_type};base64,{encoded}",
    )
