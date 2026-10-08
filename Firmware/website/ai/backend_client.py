from typing import Any, Mapping, Optional, Tuple

import requests

from config import GROWHUB_AI_KEY, GROWHUB_API_BASE

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


def get_json(path: str, params: Optional[dict] = None) -> Any:
    response = requests.get(f"{GROWHUB_API_BASE}{path}", params=params, timeout=TIMEOUT_SECONDS)
    _raise_for_status(response)
    return response.json()


def get_bytes(path: str, params: Optional[dict] = None) -> Tuple[bytes, Mapping[str, str]]:
    response = requests.get(f"{GROWHUB_API_BASE}{path}", params=params, timeout=TIMEOUT_SECONDS)
    _raise_for_status(response)
    return response.content, response.headers


def post_ai_json(path: str, payload: dict) -> Any:
    response = requests.post(
        f"{GROWHUB_API_BASE}{path}",
        json=payload,
        headers={"X-AI-Key": GROWHUB_AI_KEY},
        timeout=TIMEOUT_SECONDS,
    )
    _raise_for_status(response)
    return response.json()
