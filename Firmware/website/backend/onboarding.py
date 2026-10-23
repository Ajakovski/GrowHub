from collections import Counter
from math import ceil
from typing import Any, Dict, List, Optional, Sequence

from plants import KNOWN_PLANT_IDS, normalise_plant_ids, plants_for_ids

MAX_FLOORS_PER_HUB = 3
GRID_LABELS = {4: "4-cup (large plants)", 18: "18-cup (medium plants)", 36: "36-cup (small plants)"}

GOALS = frozenset({"food", "hobby", "both", "learning"})
HARVESTS = frozenset({"garnish", "weekly", "serious"})
TIMES = frozenset({"low", "medium", "high"})
EXPERIENCES = frozenset({"first", "some", "hydro"})
SPACES = frozenset({"corner", "wall", "room"})


class InvalidAnswers(ValueError):
    pass


def empty_state() -> dict:
    return {
        "completed": False,
        "answers": None,
        "recommendation": None,
        "completed_at": None,
        "tour_seen_at": None,
    }


def parse_state(raw: Any) -> dict:
    if not isinstance(raw, dict):
        return empty_state()
    return {
        "completed": bool(raw.get("completed")),
        "answers": raw.get("answers") if isinstance(raw.get("answers"), dict) else None,
        "recommendation": raw.get("recommendation") if isinstance(raw.get("recommendation"), dict) else None,
        "completed_at": raw.get("completed_at"),
        "tour_seen_at": raw.get("tour_seen_at"),
    }


def validate_answers(raw: Any) -> dict:
    if not isinstance(raw, dict):
        raise InvalidAnswers("Answers must be an object")

    goal = raw.get("goal")
    harvest = raw.get("harvest")
    time_budget = raw.get("time")
    experience = raw.get("experience")
    space = raw.get("space")
    plant_ids = normalise_plant_ids(raw.get("plant_ids") if isinstance(raw.get("plant_ids"), list) else [])

    if goal not in GOALS:
        raise InvalidAnswers("Pick what you want GrowHub for")
    if harvest not in HARVESTS:
        raise InvalidAnswers("Pick how much you'd like to harvest")
    if not plant_ids:
        raise InvalidAnswers("Pick at least one plant you're interested in")
    if any(plant_id not in KNOWN_PLANT_IDS for plant_id in plant_ids):
        raise InvalidAnswers("One of those plants isn't on the menu")
    if time_budget not in TIMES:
        raise InvalidAnswers("Pick how much time you have each week")
    if experience not in EXPERIENCES:
        raise InvalidAnswers("Pick your growing experience")
    if space not in SPACES:
        raise InvalidAnswers("Pick how much space you have")

    return {
        "goal": goal,
        "harvest": harvest,
        "plant_ids": plant_ids,
        "time": time_budget,
        "experience": experience,
        "space": space,
    }


def _floor_count(answers: dict) -> int:
    score = 0
    score += {"garnish": 0, "weekly": 2, "serious": 4}[answers["harvest"]]
    score += {"food": 2, "both": 2, "hobby": 0, "learning": 0}[answers["goal"]]
    score += {"low": 0, "medium": 1, "high": 2}[answers["time"]]
    score += {"corner": 0, "wall": 1, "room": 2}[answers["space"]]
    # Beginners stay small even if they're ambitious.
    if answers["experience"] == "first":
        score = max(0, score - 1)

    if score <= 1:
        return 1
    if score <= 3:
        return 2
    if score <= 5:
        return 3
    if score <= 7:
        return 4
    return 6


def _grid_mix(plant_ids: Sequence[str], floor_count: int) -> List[dict]:
    plants = plants_for_ids(plant_ids)
    if not plants:
        return [{"grid_cups": 18, "floors": floor_count, "label": GRID_LABELS[18]}]

    counts = Counter(plant["grid_cups"] for plant in plants)
    # Weight floors by how many plant interests map to each grid.
    weights = {cups: count for cups, count in counts.items()}
    total_weight = sum(weights.values())
    allocated = 0
    mix = []
    ordered = sorted(weights.items(), key=lambda item: (-item[1], -item[0]))
    for index, (cups, weight) in enumerate(ordered):
        if index == len(ordered) - 1:
            floors = floor_count - allocated
        else:
            floors = max(1, round(floor_count * weight / total_weight))
            floors = min(floors, floor_count - allocated - (len(ordered) - index - 1))
        if floors <= 0:
            continue
        mix.append({"grid_cups": cups, "floors": floors, "label": GRID_LABELS[cups]})
        allocated += floors
    if allocated < floor_count and mix:
        mix[0]["floors"] += floor_count - allocated
    return mix or [{"grid_cups": 18, "floors": floor_count, "label": GRID_LABELS[18]}]


def _pack_hubs(floor_count: int) -> List[dict]:
    hub_count = max(1, ceil(floor_count / MAX_FLOORS_PER_HUB))
    remaining = floor_count
    hubs = []
    for index in range(hub_count):
        floors = min(MAX_FLOORS_PER_HUB, remaining)
        remaining -= floors
        hubs.append({"hub_index": index + 1, "floors": floors})
    return hubs


def _headline(hubs: List[dict], mix: List[dict]) -> str:
    hub_n = len(hubs)
    floor_n = sum(hub["floors"] for hub in hubs)
    hub_bit = f"{hub_n} hub" if hub_n == 1 else f"{hub_n} hubs"
    floor_bit = f"{floor_n} floor" if floor_n == 1 else f"{floor_n} floors"
    grid_bits = " + ".join(f"{part['floors']}×{part['grid_cups']}-cup" for part in mix)
    return f"{hub_bit} · {floor_bit} · {grid_bits}"


def _why(answers: dict, floor_count: int, mix: List[dict]) -> List[str]:
    reasons = []
    plant_names = [plant["name"] for plant in plants_for_ids(answers["plant_ids"])]
    if plant_names:
        if len(mix) == 1:
            reasons.append(
                f"{mix[0]['label']} fits {plant_names[0] if len(plant_names) == 1 else 'your plant mix'} best."
            )
        else:
            reasons.append("You picked plants of different sizes, so we mixed grid types across floors.")

    if answers["harvest"] == "serious" or answers["goal"] in {"food", "both"}:
        reasons.append(f"{floor_count} growing floor{'s' if floor_count != 1 else ''} gives you room to harvest regularly.")
    elif answers["time"] == "low" or answers["experience"] == "first":
        reasons.append("We kept the setup small so it stays easy to manage while you learn the rhythm.")
    else:
        reasons.append("This size matches a relaxed hobby grow without feeling cramped.")

    if floor_count > MAX_FLOORS_PER_HUB:
        reasons.append(f"Each hub holds up to {MAX_FLOORS_PER_HUB} floors, so we split them across hubs.")
    elif answers["space"] == "corner":
        reasons.append("One corner is plenty for this footprint.")

    return reasons[:3]


def recommend(answers: dict) -> dict:
    validated = validate_answers(answers)
    floor_count = _floor_count(validated)
    mix = _grid_mix(validated["plant_ids"], floor_count)
    hubs = _pack_hubs(floor_count)
    return {
        "hubs": len(hubs),
        "floors": floor_count,
        "max_floors_per_hub": MAX_FLOORS_PER_HUB,
        "hub_layout": hubs,
        "grids": mix,
        "plant_ids": validated["plant_ids"],
        "plants": plants_for_ids(validated["plant_ids"]),
        "headline": _headline(hubs, mix),
        "why": _why(validated, floor_count, mix),
        "summary": (
            f"Start with {_headline(hubs, mix)}. "
            "Each floor is a basin + planter grid + canopy on top of a hub base."
        ),
    }


def quiz_options() -> Dict[str, List[dict]]:
    return {
        "goal": [
            {"id": "food", "label": "Grow real food", "blurb": "I want something I can actually cook with"},
            {"id": "hobby", "label": "A fun hobby", "blurb": "Watching plants thrive is the main reward"},
            {"id": "both", "label": "A bit of both", "blurb": "Tasty harvests, but no pressure"},
            {"id": "learning", "label": "Learning the ropes", "blurb": "I'm curious how hydroponics works"},
        ],
        "harvest": [
            {"id": "garnish", "label": "A little garnish", "blurb": "Herbs and a handful of leaves"},
            {"id": "weekly", "label": "Weekly salads", "blurb": "Enough greens for a few meals a week"},
            {"id": "serious", "label": "A real food source", "blurb": "I want GrowHub to pull its weight"},
        ],
        "time": [
            {"id": "low", "label": "Under 30 minutes", "blurb": "Quick check-ins when I remember"},
            {"id": "medium", "label": "About an hour", "blurb": "A calm weekly ritual"},
            {"id": "high", "label": "A few hours", "blurb": "I'm happy to tinker and tend"},
        ],
        "experience": [
            {"id": "first", "label": "First grow", "blurb": "Brand new to this"},
            {"id": "some", "label": "Some plant care", "blurb": "I've kept houseplants or a garden"},
            {"id": "hydro", "label": "Hydro already", "blurb": "I've grown in water before"},
        ],
        "space": [
            {"id": "corner", "label": "One corner", "blurb": "A compact spot in the room"},
            {"id": "wall", "label": "Half a wall", "blurb": "Room to stack a few floors"},
            {"id": "room", "label": "Dedicated space", "blurb": "I can give it a proper home"},
        ],
    }
