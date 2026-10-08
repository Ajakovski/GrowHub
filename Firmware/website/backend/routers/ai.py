from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional
import os
import secrets
import time

import history
from routers.device import get_hub

AI_KEY = os.environ.get("GROWHUB_AI_KEY")


def require_ai_key(x_ai_key: Optional[str] = Header(default=None)) -> None:
    if not AI_KEY:
        raise HTTPException(status_code=503, detail="AI status updates are disabled: set GROWHUB_AI_KEY")
    if x_ai_key is None or not secrets.compare_digest(x_ai_key.encode(), AI_KEY.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing AI key")


router = APIRouter()


class AIStatus(BaseModel):
    hub_id: str
    status: Literal["Healthy", "Watch", "Action needed"]
    summary: str = Field(min_length=1, max_length=300)


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
