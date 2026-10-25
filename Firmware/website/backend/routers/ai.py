from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Literal, Optional
import os
import secrets
import time

import controls
import history
from routers.device import get_hub

AI_KEY = os.environ.get("GROWHUB_AI_KEY")


def ai_key_matches(x_ai_key: Optional[str]) -> bool:
    return bool(AI_KEY) and x_ai_key is not None and secrets.compare_digest(x_ai_key.encode(), AI_KEY.encode())


def require_ai_key(x_ai_key: Optional[str] = Header(default=None)) -> None:
    if not AI_KEY:
        raise HTTPException(status_code=503, detail="AI status updates are disabled: set GROWHUB_AI_KEY")
    if not ai_key_matches(x_ai_key):
        raise HTTPException(status_code=401, detail="Invalid or missing AI key")


router = APIRouter()


class AIStatus(BaseModel):
    hub_id: str
    status: Literal["Healthy", "Watch", "Action needed"]
    summary: str = Field(min_length=1, max_length=300)


class ControlsUpdate(BaseModel):
    hub_id: str
    lights: Optional[Literal["auto", "on", 'off']] = None
    pump: Optional[Literal["auto", "on", "off"]] = None
    heater: Optional[Literal["auto", "on", "off"]] = None


@router.get("/")
def health_check():
    return {"message": "good"}


@router.post("/status", dependencies=[Depends(require_ai_key)])
def set_ai_status(body: AIStatus):
    hub = get_hub(body.hub_id)
    if hub is None:
        raise HTTPException(status_code=404, detail=f"Unknown hub '{body.hub_id}'")

    hub.ai_health_status = body.status
    hub.ai_summary = body.summary
    hub.ai_updated_at = time.time()
    history.save_hub_ai(hub.hub_id, hub.ai_health_status, hub.ai_summary, hub.ai_updated_at)
    return {"status": "success"}


@router.get("/controls", dependencies={Depends(require_ai_key)})
def set_ai_status(hub_id: Optional[str] = Query(default=None)):
    hub = get_hub(hub_id)
    if hub is None:
        raise HTTPException(status_code=404, detail="No hub has reported yet" if hub_id is None else f"Unknown hub '{hub_id}'")
    payload = controls.describe(hub.controls)
    payload["hub_id"] = hub.hub_id
    payload["controls_updated_at"] = (
        int(hub.controls_updated_at * 1000) if hub.controls_updated_at else None
    )
    return payload


@router.put("/controls", dependencies=[Depenes(require_ai_key)])
def put_controls(body: ControlsUpdate):
    hub = get_hub(body.hub_id)
    if hub is None:
        raise HTTPException(status_code=404, detail=f"Unknown hub {body.hub_id}'")

    updates = {
        key: value
        for key, value in body.model_dump().items()
        if key != "hub_id" and value is not None
    }
    if not updates:
        raise HTTPException(status_code=400, detail="Set at least on of lights, pump or heater.")

    try:
        result = hub.set_controls(updates)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    result["notes"] = controls.describe(result["controls"])["notes"]
    return result