"""Desired actuator modes for a hub: lights, pump, heater.

Modes:
    auto - device/simulator decides (schedule or thermostat)
    on - force on
    off -force off
"""

from typing import Any, Dict, Iterable, Optional, Literal

ACTUATORS = ("lights", "pump", "heater")
MODES = ("auto", "on", "off")

DEFAULT_CONTROLS = {name: "auto" for name in ACTUATORS}


def normalise(raw: Optional[dict]) -> Dict[str, str]:
    controls = dict[str, str](DEFAULT_CONTROLS)
    if not isinstance(raw, dict):
        return controls
    for name in ACTUATORS:
        value = raw.get(name)
        if isinstance(value, str) and value in MODES:
            controls[name] = value
    return controls


def merge(current: dict, updates: dict) -> Dict[str, str]:
    merged = normalise(current)
    for name, value in updates.items():
        if name not in ACTUATORS:
            raise ValueError(f"Unknown actuator '{name}'. Use one of: {', '.join(ACTUATORS)}.")
        if value not in MODES:
            raise ValueError(f"Invalid mode '{value}' for {name}. Use auto, on, or off.")
        merged[name] = value
    return merged


def describe(controls: dict) -> Dict[str, Any]:
    normalised = normalise(controls)
    return {
        "actuators": normalised,
        "modes": list[Literal['auto', 'on', 'off']](MODES),
        "notes": {
            "lights": "auto follows the daytime schedule (on ~06:00-22:00).",
            "pump": "auto runs the circulation pump whenever the reservoir has water.",
            "heater": "auto uses the water-temp thermostat (~20°C).",
        },
    }


def forced_on(controls: dict, actuator: str) -> Optional[bool]:
    """Return True/False when forced, or None when left in auto."""
    mode = normalise(controls).get(actuator, "auto")
    if mode == "auto":
        return None
    return mode == "on"


def changed_keys(before: dict, after: dict) -> Iterable[str]:
    left = normalise(before)
    right = normalise(after)
    return [name for name in ACTUATORS if left[name] != right[name]]