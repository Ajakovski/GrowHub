import time
from typing import List, Optional

from backend_client import get_json
from skills.registry import skill

HUB_ID_PROPERTY = {
    "hub_id": {
        "type": "string",
        "description": "Hub to query. Omit to use the hub that reported most recently.",
    }
}


def _ago(timestamp_ms: Optional[int]) -> Optional[str]:
    if not timestamp_ms:
        return None
    seconds = max(0, int(time.time() - timestamp_ms / 1000))
    if seconds < 90:
        return f"{seconds}s ago"
    if seconds < 90 * 60:
        return f"{seconds // 60}m ago"
    if seconds < 48 * 3600:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


HISTORY_METRICS = (
    ("water_temp", "water_temperature_c", 1),
    ("ec", "ec_ms_cm", 2),
    ("ph", "ph", 2),
    ("air_temp", "air_temperature_c", 1),
    ("humidity", "humidity_percent", 0),
    ("light", "light_lux", 0),
    ("flow", "water_flow_l_min", 2),
)


def _round(value: Optional[float], decimals: int) -> Optional[float]:
    return round(value, decimals) if value is not None else None


def _hub_params(hub_id: Optional[str]) -> dict:
    return {"hub": hub_id} if hub_id else {}


@skill(
    "list_hubs",
    "List every GrowHub hub known to the server with its online status and when it last reported.",
)
def list_hubs():
    return [
        {
            "hub_id": hub["hub_id"],
            "online": hub["hub_online"],
            "last_report": _ago(hub["last_telemetry_at"]),
        }
        for hub in get_json("/api/web/hubs")
    ]


@skill(
    "get_hub_status",
    "Get the latest readings for a hub: the shared reservoir's level, water temperature, heater state, EC "
    "and pH, each tile's air temperature, humidity, light level and water flow, active alerts, camera status "
    "and the last AI review.",
    HUB_ID_PROPERTY,
)
def get_hub_status(hub_id: Optional[str] = None):
    stats = get_json("/api/web/plant-stats", _hub_params(hub_id))
    if not stats.get("hub_id"):
        return {"error": "No hub has reported yet."}

    crops = stats.get("crops") or {}
    tile_plants = crops.get("tile_plants") or {}
    return {
        "hub_id": stats["hub_id"],
        "online": stats.get("hub_online", False),
        "last_report": _ago(stats.get("last_telemetry_at")),
        "crops": {
            "configured": bool(crops.get("configured")),
            "plants": [plant.get("name") for plant in crops.get("plants") or []],
            "plant_ids": crops.get("plant_ids") or [],
            "ec_range": crops.get("ec_range"),
            "ec_conflict": bool(crops.get("ec_conflict")),
        },
        "reservoir": {
            "level_ok": stats.get("water_level_ok"),
            "water_temperature_c": _round(stats.get("water_temperature"), 1),
            "heater_on": stats.get("heater_on"),
            "ec_ms_cm": _round(stats.get("ec_level"), 2),
            "ph": _round(stats.get("ph"), 2),
        },
        "tiles": [
            {
                "tile_id": tile["tile_id"],
                "plants": tile_plants.get(tile["tile_id"]) or crops.get("plant_ids") or [],
                "air_temperature_c": _round(tile.get("air_temperature"), 1),
                "humidity_percent": _round(tile.get("humidity"), 0),
                "light_lux": _round(tile.get("light_lux"), 0),
                "water_flow_l_min": _round(tile.get("flow_lpm"), 2),
            }
            for tile in stats.get("tiles", [])
        ],
        "alerts": [alert["message"] for alert in stats.get("alerts", [])],
        "camera_online": stats.get("camera_online", False),
        "last_ai_review": {
            "status": stats.get("ai_health_status"),
            "summary": stats.get("ai_summary"),
            "when": _ago(stats.get("ai_updated_at")),
        },
    }


def _summarise(values: List[float], decimals: int) -> Optional[dict]:
    if not values:
        return None

    low, high = min(values), max(values)
    change = values[-1] - values[0]
    threshold = max((high - low) * 0.1, 10 ** -decimals)
    trend = "steady" if abs(change) < threshold else ("rising" if change > 0 else "falling")

    return {
        "min": round(low, decimals),
        "avg": round(sum(values) / len(values), decimals),
        "max": round(high, decimals),
        "first": round(values[0], decimals),
        "latest": round(values[-1], decimals),
        "trend": trend,
    }


@skill(
    "get_history_summary",
    "Summarise historical readings (min, average, max, first, latest and trend) over a time range. Device "
    "'hub' covers the reservoir (water temperature, EC, pH) plus the average of all tiles' air temperature, "
    "humidity, light and water flow; a tile id covers just that tile's air temperature, humidity, light and flow",
    {
        **HUB_ID_PROPERTY,
        "device": {
            "type": "string",
            "description": "'hub' for the reservoir and tile averages, or a tile id such as 'tile_1'",
        },
        "range": {
            "type": "string",
            "enum": ["1h", "24h", "7d"],
            "description": "Time range to summarise.",
        },
    },
)
def get_history_summary(hub_id: Optional[str] = None, device: str = "hub", range: str = "24h"):
    params = {**_hub_params(hub_id), "device": device, "range": range}
    history = get_json("/api/web/history", params)
    points = history.get("points", [])
    if not points:
        return {"hub_id": history.get("hub"), "device": device, "range": range, "error": "No readings in this range."}

    summary {
        "hub_id": history.get("hub"),
        "device": device,
        "range": range,
        "points": len(points),
        "from": _ago(points[0]["at"]),
        "to": _ago(points[-1]["at"]),
    }
    for key, label, decimals in HISTORY_METRICS:
        values = [point[key] for point in points if point.get(key) is not None]
        if values:
            summary[label] = _summarise(values, decimals)
    return summary
