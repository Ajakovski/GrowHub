from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel, field_validator, Field
from typing import Optional
import os
import re

import accounts
from ratelimit import RateLimiter
from routers.ai import ai_key_matches

SESSION_COOKIE = "growhub_session"
COOKIE_SECURE = os.environ.get("GROWHUB_COOKIE_SECURE", "0") == "1"
AUTH_ATTEMPTS_PER_MINUTE = int(os.environ.get("GROWHUB_AUTH_ATTEMPTS_PER_MINUTE", "10"))
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

router = APIRouter()
limiter = RateLimiter(AUTH_ATTEMPTS_PER_MINUTE)


class Credentials(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not EMAIL_PATTERN.match(value):
            raise ValueError("Enter a valid email address")
        return value


class NewAccount(Credentials):
    password: str = Field(min_length=8, max_length=128)


def current_user(request: Request) -> Optional[accounts.User]:
    token = request.cookies.get(SESSION_COOKIE)
    return accounts.user_for_session(token) if token else None


def require_user(request: Request) -> accounts.User:
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Log in to continue")
    return user


def require_viewer(request: Request, x_ai_key: Optional[str] = Header(default=None)) -> None:
    if ai_key_matches(x_ai_key):
        return
    require_user(request)


def _check_rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "Unknown"
    if not limiter.allow(client):
        raise HTTPException(status_code=429, detail="Too many attempts, wait a minute and try again.")


def _start_session(response: Response, user: accounts.User) -> User:
    response.set_cookie(
        SESSION_COOKIE,
        accounts.create_session(user.id),
        max_age=accounts.SESSION_TTL_SECONDS,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return {"email": user.email}


@router.post("/register", status_code=201)
def register(body: NewAccount, request: Request, response: Response):
    _check_rate_limit(request)
    try:
        user = account.create_user(body.email, body.password)
    except accounts.EmailTaken:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    return _start_session(response, user)


@router.post("/login")
def login(body: Credentials, request: Request, response: Response):
    _check_rate_limit(request)
    user = accounts.authenticate(body.email, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Wrong email or password")
    return _start_session(response, user)


@router.get("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        accounts.delete_session(token)
    response.delete_cookie(SESSION_COOKIE, path="/", secure=COOKIE_SECURE, httponly=True, samesite="lax")
    return {"status": "logged out"}


@router.get("/me")
def me(user: accounts.User = Depends(require_user)):
    return {"email": user.email}
