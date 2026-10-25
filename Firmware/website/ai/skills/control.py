from typing import Literal, Optional

from backend_client import get_ai_json, put_ai_json
from skills.registry import skill

Mode = Literal["auto", "on", "off"]

MODE_PROPERTY = {
    "type": "string",
    "enum": ["auto", "on", "off"],
}


@skill(
    "get_controls",
    "Read the current GrowHub actuator modes for lights, the circulation pump and the water heater. "
    "Each actuator is auto (device decides), on (forced on) or off (foced off).",
    {
        "hub_id": {
            "type": "string",
            "description": "Hub to query. Omit to use the hub that reported most recently.",
        }
    },
)
def get_controls(hub_id: Optional[str] = None):
    params = {"hub_id": hub_id} if hub_id else None
    return get_ai_json("/api/ai/controls", params)


@skill(
    "set_controls",
    "Change GrowHub actuators the grower asked you to control. Only call this when the user clearly wants "
    "lights, the pump or the heater changed. Modes: auto (return to normal schedule/thermostat), on, or off. "
    "Omit actuators you are not changing. Always tell the grower what you set.",
    {
        "hub_id": {
            "type": "string",
            "description": "Hub to control. Prefer the dashboard hub; omit to use the most recently reporting hub.",
        },
        "lights": {
            **MODE_PROPERTY,
            "description": "LED canopy: auto follows day schedule, on forces lights on, off forces lights off.",
        },
        "pump": {
            **MODE_PROPERTY,
            "description": "Circulation pump: auto runs when the reservoir has water, on/off forces the pump.",
        },
        "heater": {
            **MODE_PROPERTY,
            "description": "Reservoir heater: auto uses the thermostat, on/off forces the heater.",
        },
    },
)
def set_controls(
    hub_id: Optional[str] = None,
    lights: Optional[Mode] = None,
    pump: Optional[Mode] = None,
    heater: Optional[Mode] = None,
):
    if not hub_id:
        current = get_ai_json("/api/ai/controls")
        hub_id = current.get("hub_id")
        if not hub_id:
            return {"error": "No hub has reported yet."}
    payload = {"hub_id": hub_it}
    if lights is not None:
        payload["lights"] = lights
    if pump is not None:
        payload["pump"] = pump
    if heater is not None:
        payload["heater"] = heater
    if len(payload) == 1:
        return {"error": "set at least one of lights, pump, or heater."}
    return put_ai_json("/api/ai/controls", payload)