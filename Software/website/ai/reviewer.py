import json
import re
import threading
from typing import Dict

import llm
import prompts
from backend_client import get_json, post_ai_json
from config import GROWHUB_AI_KEY, REVIEW_INTERVAL_MINUTES

STARTUP_DELAY_SECONDS = 20
MAX_SUMMARY_CHARS = 300
STATUSES = {status.lower(): status for status in ("Healthy", "Watch", "Action needed")}

_stop = threading.Event()
_last_reviewed: Dict[str, int] = {}


def parse_review(reply: str) -> dict:
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object in reply: {reply[:200]!r}")

    data = json.loads(match.group(0))
    status = STATUSES.get(str(data.get("status", "")).strip().lower())
    summary = str(data.get("summary", "")).strip()
    if not status or not summary:
        raise ValueError(f"missing status or summary: {data!r}")

    return {"status": status, "summary": summary[:MAX_SUMMARY_CHARS]}


def review_hub(hub_id: str) -> dict:
    reply = llm.run([
        {"role": "system", "content": prompts.SYSTEM_PROMPT},
        {"role": "user", "content": prompts.review_prompt(hub_id)},
    ])
    review = parse_review(reply)
    post_ai_json("/api/ai/status", {"hub_id": hub_id, **review})
    return review


def review_pending_hubs() -> None:
    """Review each hub that has sent telemetry since its last review."""
    for hub in get_json("/api/web/hubs"):
        hub_id, reported_at = hub["hub_id"], hub["last_telemetry_at"]
        if not reported_at or _last_reviewed.get(hub_id) == reported_at:
            continue
        try:
            review = review_hub(hub_id)
        except Exception as error:
            print(f"AI review of {hub_id} failed: {error}")
            continue
        _last_reviewed[hub_id] = reported_at
        print(f"AI review of {hub_id}: {review['status']} - {review['summary']}")


def _loop() -> None:
    if _stop.wait(STARTUP_DELAY_SECONDS):
        return
    while True:
        try:
            review_pending_hubs()
        except Exception as error:
            print(f"AI review pass failed: {error}")
        if _stop.wait(REVIEW_INTERVAL_MINUTES * 60):
            return


def start() -> None:
    if REVIEW_INTERVAL_MINUTES <= 0:
        print("Automatic AI review disabled (REVIEW_INTERVAL_MINUTES=0).")
        return
    if not llm.is_configured() or not GROWHUB_AI_KEY:
        print("Automatic AI review disabled: set LLM_API_KEY and GROWHUB_AI_KEY.")
        return
    threading.Thread(target=_loop, name="ai-reviewer", daemon=True).start()
    print(f"Automatic AI review every {REVIEW_INTERVAL_MINUTES:g} minutes.")


def stop() -> None:
    _stop.set()
