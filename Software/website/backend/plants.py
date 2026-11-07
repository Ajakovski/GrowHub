from typing import List, Optional, Sequence

# Shared nutrient targets for a Deep Water Culture reservoir. Keep ids stable; they are stored in the DB.
# size + grid_cups drive onboarding hardware recommendations (4 large / 18 medium / 36 small cups).
PLANT_CATALOG = [
    {
        "id": "lettuce",
        "name": "Lettuce & leafy greens",
        "blurb": "Butterhead, romaine, spinach, kale",
        "ec": [0.8, 1.2],
        "ph": [5.5, 6.5],
        "light_hours": 14,
        "size": "small",
        "grid_cups": 36,
    },
    {
        "id": "basil",
        "name": "Herbs",
        "blurb": "Basil, mint, parsley, cilantro",
        "ec": [1.0, 1.6],
        "ph": [5.5, 6.5],
        "light_hours": 14,
        "size": "small",
        "grid_cups": 36,
    },
    {
        "id": "strawberry",
        "name": "Strawberries",
        "blurb": "Day-neutral varieties do best indoors",
        "ec": [1.0, 1.5],
        "ph": [5.5, 6.5],
        "light_hours": 14,
        "size": "medium",
        "grid_cups": 18,
    },
    {
        "id": "pepper",
        "name": "Peppers",
        "blurb": "Bell peppers and mild chilies",
        "ec": [1.8, 2.8],
        "ph": [5.5, 6.5],
        "light_hours": 16,
        "size": "large",
        "grid_cups": 4,
    },
    {
        "id": "tomato",
        "name": "Tomatoes",
        "blurb": "Cherry and cocktail tomatoes suit DWC well",
        "ec": [2.0, 3.5],
        "ph": [5.5, 6.5],
        "light_hours": 16,
        "size": "large",
        "grid_cups": 4,
    },
]

PLANT_BY_ID = {plant["id"]: plant for plant in PLANT_CATALOG}
KNOWN_PLANT_IDS = frozenset(PLANT_BY_ID)


def catalog() -> List[dict]:
    return list(PLANT_CATALOG)


def normalise_plant_ids(ids: Optional[Sequence[str]]) -> List[str]:
    if not ids:
        return []
    seen = set()
    ordered = []
    for plant_id in ids:
        if plant_id in KNOWN_PLANT_IDS and plant_id not in seen:
            seen.add(plant_id)
            ordered.append(plant_id)
    return ordered


def plants_for_ids(ids: Sequence[str]) -> List[dict]:
    return [dict(PLANT_BY_ID[plant_id]) for plant_id in normalise_plant_ids(ids)]


def combined_ec_range(ids: Sequence[str]) -> Optional[List[float]]:
    """Union of the selected crops' EC windows so one shared reservoir can feed all of them."""
    plants = plants_for_ids(ids)
    if not plants:
        return None
    return [min(plant["ec"][0] for plant in plants), max(plant["ec"][1] for plant in plants)]


def plants_conflict(ids: Sequence[str]) -> bool:
    """True when the selected crops have no overlapping EC window (hard to share one reservoir)."""
    plants = plants_for_ids(ids)
    if len(plants) < 2:
        return False
    low = max(plant["ec"][0] for plant in plants)
    high = min(plant["ec"][1] for plant in plants)
    return low > high


def parse_hub_plants(raw) -> dict:
    if not isinstance(raw, dict):
        return {"configured": False, "plant_ids": [], "tile_plants": {}}
    plant_ids = normalise_plant_ids(raw.get("plant_ids") or [])
    tile_plants = {}
    raw_tiles = raw.get("tile_plants") or {}
    if isinstance(raw_tiles, dict):
        for tile_id, tile_ids in raw_tiles.items():
            if not isinstance(tile_id, str) or not tile_id.startswith("tile_"):
                continue
            cleaned = normalise_plant_ids(tile_ids if isinstance(tile_ids, list) else [])
            if cleaned:
                tile_plants[tile_id] = cleaned
    return {
        "configured": bool(raw.get("configured")) or bool(plant_ids),
        "plant_ids": plant_ids,
        "tile_plants": tile_plants,
    }


def plants_payload(raw) -> dict:
    parsed = parse_hub_plants(raw)
    plant_ids = parsed["plant_ids"]
    return {
        "configured": parsed["configured"],
        "plant_ids": plant_ids,
        "plants": plants_for_ids(plant_ids),
        "tile_plants": parsed["tile_plants"],
        "ec_range": combined_ec_range(plant_ids),
        "ec_conflict": plants_conflict(plant_ids),
    }
