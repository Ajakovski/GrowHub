import os
from pathlib import Path
from typing import List, NamedTuple, Optional

STOCK_IMAGES_DIR = Path(os.environ.get(
    "GROWHUB_STOCK_IMAGES_DIR",
    Path(__file__).resolve().parent.parent / "stock_images",
))
ROTATE_SECONDS = float(os.environ.get("GROWHUB_STOCK_ROTATE_SECONDS", "30"))
MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


class StockFrame(NamedTuple):
    data: bytes
    captured_at: float
    media_type: str
    index: int
    total: int


def list_images() -> List[Path]:
    if not STOCK_IMAGES_DIR.is_dir():
        return []
    return sorted(
        path for path in STOCK_IMAGES_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in MEDIA_TYPES
    )


def current_frame(now: float) -> Optional[StockFrame]:
    images = list_images()
    if not images:
        return None

    slot = int(now // ROTATE_SECONDS)
    index = slot % len(images)
    path = images[index]
    try:
        data = path.read_bytes()
    except OSError:
        return None
    return StockFrame(data, slot * ROTATE_SECONDS, MEDIA_TYPES[path.suffix.lower()], index, len(images))
