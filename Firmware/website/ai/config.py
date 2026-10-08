import os

LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "google/gemini-2.5-flash")

GROWHUB_API_BASE = os.environ.get("GROWHUB_API_BASE", "http://localhost:8000").rstrip("/")
GROWHUB_AI_KEY = os.environ.get("GROWHUB_AI_KEY", "")

REVIEW_INTERVAL_MINUTES = float(os.environ.get("REVIEW_INTERVAL_MINUTES", "30"))

MAX_TOOL_ROUNDS = 5
MAX_CHAT_MESSAGES = 20
MAX_MESSAGE_CHARS = 2000
CHAT_REQUESTS_PER_MINUTE = int(os.environ.get("CHAT_REQUESTS_PER_MINUTE", "10"))
