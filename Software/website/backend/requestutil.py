"""HTTP request helpers shared by auth/web rate limiting."""

from __future__ import annotations

import os
import re

from fastapi import Request

# Only used when GROWHUB_TRUST_PROXY=1 (set in compose behind nginx).
_IP_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$|^\[?[0-9a-fA-F:]+\]?$")


def client_ip(request: Request) -> str:
    """Client address for rate limits.

    When GROWHUB_TRUST_PROXY=1, prefer X-Real-IP / first X-Forwarded-For hop
    (nginx sets these). Otherwise use the direct TCP peer so clients cannot
    spoof limits by sending forged forwarded headers to a published :8000.
    """
    if os.environ.get("GROWHUB_TRUST_PROXY", "0") == "1":
        forwarded = (request.headers.get("x-real-ip") or "").strip()
        if not forwarded:
            raw = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
            forwarded = raw
        if forwarded and _IP_RE.match(forwarded):
            return forwarded.lstrip("[").rstrip("]")
    if request.client and request.client.host:
        return request.client.host
    return "unknown"
