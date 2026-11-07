import os

# Any OpenAI-compatible provider works: OpenRouter (default), OpenAI, or Gemini's OpenAI endpoint.
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "google/gemini-2.5-flash")

GROWHUB_API_BASE = os.environ.get("GROWHUB_API_BASE", "http://localhost:8000").rstrip("/")
GROWHUB_AI_KEY = os.environ.get("GROWHUB_AI_KEY", "")

SESSION_COOKIE = "growhub_session"
# Must match the backend: login cookies need exact origins, so "*" is not allowed.
WEB_ORIGIN_REGEX = os.environ.get("GROWHUB_WEB_ORIGIN_REGEX") or (
    r"https?://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)(:\d+)?"
)

# Set to 0 to disable the automatic review.
REVIEW_INTERVAL_MINUTES = float(os.environ.get("REVIEW_INTERVAL_MINUTES", "30"))

MAX_TOOL_ROUNDS = 5
MAX_CHAT_MESSAGES = 20
MAX_MESSAGE_CHARS = 2000
CHAT_REQUESTS_PER_MINUTE = int(os.environ.get("CHAT_REQUESTS_PER_MINUTE", "10"))
