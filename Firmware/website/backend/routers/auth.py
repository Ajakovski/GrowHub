from annotated_types import MaxLen
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel, field_validator, Field
from typing import Optional
from urllib.parse import urlencode
import logging
import os
import re

import accounts
import mailer
from ratelimit import RateLimiter
from routers.ai import ai_key_matches

SESSION_COOKIE = "growhub_session"
COOKIE_SECURE = os.environ.get("GROWHUB_COOKIE_SECURE", "0") == "1"
AUTH_ATTEMPTS_PER_MINUTE = int(os.environ.get("GROWHUB_AUTH_ATTEMPTS_PER_MINUTE", "10"))
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
WEB_ORIGIN_REGEX = os.environ.get("GROWHUB_WEB_ORIGIN_REGEX") or (
    r"https?://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)(:\d+)?"
)
PUBLIC_URL = os.environ.get("GROWHUB_PUBLIC_URL", "").rstrip("/")
FALLBACK_PUBLIC_URL = "http://localhost:5000"

router = APIRouter()
limiter = RateLimiter(AUTH_ATTEMPTS_PER_MINUTE)
resend_limiter = RateLimiter(3, window_seconds=600)
logger = logging.getLogger("uvicorn.error")


def _normalise_email(value: str) -> str:
    value = value.strip().lower()
    if not EMAIL_PATTERN.match(value):
        raise ValueError("Enter a valid email address")
    return value


class Credentials(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return _normalise_email(value)


class NewAccount(Credentials):
    password: str = Field(min_length=8, max_length=128)


class EmailOnly(BaseModel):
    email: str = Field(max_length=254)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return _normalise_email(value)


class VerificationToken(BaseModel):
    token: str = Field(min_length=1, max_length=200)


def current_user(request: Request) -> Optional[accounts.User]:
    token = request.cookies.get(SESSION_COOKIE)
    return accounts.user_for_session(token) if token else None


def require_user(request: Request) -> accounts.User:
    user = current_user(request)
    if user is None or not user.email_verified:
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


def _site_url(request: Request) -> str:
    if PUBLIC_URL:
        return PUBLIC_URL
    origin = request.headers.get("origin", "")
    return origin if re.fullmatch(WEB_ORIGIN_REGEX, origin) else FALLBACK_PUBLIC_URL


def _send_verification(request: Request, user: accounts.User) -> bool:
    token = accounts.create_verification_token(user.id)
    link = f"{_site_url(request)}/verify.html?{urlencode({'token': token})}"
    try:
        mailer.send_verification_email(user.email, link)
    except mailer.EmailError as error:
        logger.error("Verification email to %s failed: %s", user.email, error)
        return False
    return True


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
def register(body: NewAccount, request: Request):
    _check_rate_limit(request)
    try:
        user = accounts.create_user(body.email, body.password)
    except accounts.EmailTaken:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    return {"email": user.email, "email_sent": _send_verification(request, user)}


@router.post("/login")
def login(body: Credentials, request: Request, response: Response):
    _check_rate_limit(request)
    user = accounts.authenticate(body.email, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Wrong email or password")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Verify your email first. Check your inbox for the link.")
    return _start_session(response, user)


@router.post("/verify")
def verify(body: VerificationToken, request: Request, response: Response):
    _check_rate_limit(request)
    user = accounts.verify_email(body.token)
    if user is None:
        raise HTTPException(status_code=400, detail="This verification link is invalid or has expired.")
    return _start_session(response, user)


@router.post("/resend-verification")
def resend_verification(body: EmailOnly, request: Request):
    _check_rate_limit(request)
    if not resend_limiter.allow(body.email):
        raise HTTPException(status_code=429, detail="We already sent a few emails. Wait 10 minutes and try again.")
    user = accounts.find_user(body.email)
    if user is not None and not user.email_verified:
        _send_verification(request, user)
    return {"status": "If that account still needs verifying, a new link is on its way."}


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
