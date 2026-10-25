from typing import Any, Mapping, Optional, Tuple

import requests

from config import GROWHUB_AI_KEY, GROWHUB_API_BASE, SESSION_COOKIE

TIMEOUT_SECONDS = 10


class BackendError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _raise_for_status(response: requests.Response) -> None:
    if response.ok:
        return
    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text
    raise BackendError(response.status_code, str(detail))


def _ai_headers() -> dict:
    return {"X-AI-Key": GROWHUB_AI_KEY} if GROWHUB_AI_KEY else {}


def get_json(path: str, params: Optional[dict] = None) -> Any:
    response = requests.get(f"{GROWHUB_API_BASE}{path}", params=params, headers=_ai_headers(), timeout=TIMEOUT_SECONDS)
    _raise_for_status(response)
    return response.json()


def get_bytes(path: str, params: Optional[dict] = None) -> Tuple[bytes, Mapping[str, str]]:
    response = requests.get(f"{GROWHUB_API_BASE}{path}", params=params, headers=_ai_headers(), timeout=TIMEOUT_SECONDS)
    _raise_for_status(response)
    return response.content, response.headers


def session_user(session_token: str) -> Optional[dict]:
    response = requests.get(
        f"{GROWHUB_API_BASE}/api/auth/me",
        cookies={SESSION_COOKIE: session_token},
        timeout=TIMEOUT_SECONDS,
    )
    if response.status_code == 401:
        return None
    _raise_for_status(response)
    return response.json()


def post_ai_json(path: str, payload: dict) -> Any:
    response = requests.post(
        f"{GROWHUB_API_BASE}{path}",
        json=payload,
        headers={"X-AI-Key": GROWHUB_AI_KEY},
        timeout=TIMEOUT_SECONDS,
    )
    _raise_for_status(response)
    return response.json()


def put_ai_json(path: str, payload: dict) -> Any:
    response = requests.put(
        f"{GROWHUB_API_BASE}{path}",
        json=payload,
        headers={"X-AI-Key": GROWHUB_AI_KEY},
        timeout=TIMEOUT_SECONDS,
    )
    _raise_for_status(response)
    return response.json()