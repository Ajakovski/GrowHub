from contextlib import asynccontextmanager
from typing import List, Literal, Optional

import openai
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import llm
import prompts
import reviewer
from backend_client import BackendError
from config import CHAT_REQUESTS_PER_MINUTE, LLM_MODEL, MAX_CHAT_MESSAGES, MAX_MESSAGE_CHARS
from ratelimit import RateLimiter
from skills import SKILLS


@asynccontextmanager
async def lifespan(_: FastAPI):
    reviewer.start()
    yield
    reviewer.stop()


app = FastAPI(title="GrowHub AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = RateLimiter(CHAT_REQUESTS_PER_MINUTE)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    hub_id: Optional[str] = None
    messages: List[ChatMessage] = Field(min_length=1)


def _check_rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    if not limiter.allow(client):
        raise HTTPException(status_code=429, detail="Too many AI requests, wait a minute and try again.")


def _call_llm(action):
    try:
        return action()
    except llm.LLMNotConfigured as error:
        raise HTTPException(status_code=503, detail=str(error))
    except openai.AuthenticationError:
        raise HTTPException(status_code=502, detail="The LLM provider rejected the API key.")
    except openai.APIStatusError as error:
        raise HTTPException(status_code=502, detail=f"LLM provider error ({error.status_code}).")
    except openai.APIConnectionError:
        raise HTTPException(status_code=502, detail="Could not reach the LLM provider.")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "llm_configured": llm.is_configured(),
        "model": LLM_MODEL,
        "skills": sorted(SKILLS),
    }


@app.post("/chat")
def chat(body: ChatRequest, request: Request):
    messages = body.messages[-MAX_CHAT_MESSAGES:]
    while messages and messages[0].role != "user":
        messages = messages[1:]
    if not messages or messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="The last message must be from the user.")
    if len(messages[-1].content) > MAX_MESSAGE_CHARS:
        raise HTTPException(status_code=400, detail=f"Keep questions under {MAX_MESSAGE_CHARS} characters.")

    _check_rate_limit(request)
    conversation = [
        {"role": "system", "content": prompts.chat_system_prompt(body.hub_id)},
        *({"role": m.role, "content": m.content} for m in messages),
    ]
    reply = _call_llm(lambda: llm.run(conversation))
    return {"reply": reply or "Sorry, I could not come up with an answer.", "model": LLM_MODEL}


@app.post("/review")
def review_now(hub_id: str, request: Request):
    _check_rate_limit(request)
    try:
        review = _call_llm(lambda: reviewer.review_hub(hub_id))
    except BackendError as error:
        raise HTTPException(status_code=502, detail=f"Backend error ({error.status_code}): {error.detail}")
    except ValueError as error:
        raise HTTPException(status_code=502, detail=f"Could not parse the AI review: {error}")
    return {"hub_id": hub_id, **review}
