import json
from functools import lru_cache
from typing import List

from openai import OpenAI

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, MAX_TOOL_ROUNDS
from skills import run_skill, tool_definitions


class LLMNotConfigured(Exception):
    pass


def is_configured() -> bool:
    return bool(LLM_API_KEY)


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    if not is_configured():
        raise LLMNotConfigured("Set LLM_API_KEY to enable the AI.")
    return OpenAI(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        timeout=60,
        default_headers={"X-Title": "GrowHub"},
    )


def _assistant_message(message) -> dict:
    entry = {
        "role": "assistant",
        "content": message.content or "",
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.function.name, "arguments": call.function.arguments or "{}"},
            }
            for call in message.tool_calls
        ],
    }
    # Some OpenRouter models (e.g. Gemini) need their reasoning echoed back to continue a tool call.
    reasoning = (message.model_extra or {}).get("reasoning_details")
    if reasoning:
        entry["reasoning_details"] = reasoning
    return entry


def _parse_arguments(raw: str) -> dict:
    try:
        parsed = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def run(messages: List[dict]) -> str:
    """Answer the conversation, letting the model call skills for up to MAX_TOOL_ROUNDS rounds."""
    client = _client()
    conversation = list(messages)
    tools = tool_definitions()

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(model=LLM_MODEL, messages=conversation, tools=tools)
        message = response.choices[0].message
        if not message.tool_calls:
            return (message.content or "").strip()

        conversation.append(_assistant_message(message))
        images = []
        for call in message.tool_calls:
            result = run_skill(call.function.name, _parse_arguments(call.function.arguments))
            conversation.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result.data, default=str),
            })
            if result.image_data_url:
                images.append(result.image_data_url)

        # Tool results must be text, so photos go in a follow-up user message.
        if images:
            conversation.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": "Camera photo returned by the get_latest_photo skill."},
                    *({"type": "image_url", "image_url": {"url": url}} for url in images),
                ],
            })

    response = client.chat.completions.create(
        model=LLM_MODEL, messages=conversation, tools=tools, tool_choice="none"
    )
    return (response.choices[0].message.content or "").strip()
