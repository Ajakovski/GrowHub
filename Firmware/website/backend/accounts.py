import hashlib
import secrets
import sqlite3
import time
from typing import NamedTuple, Optional

from history import _connection

SESSION_TTL_SECONDS = 30 * 24 * 3600
SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1


class User(NamedTuple):
    id: int
    email: str
    created_at: float


class EmailTaken(Exception):
    pass


def init_db() -> None:
    with _connection() as conn:
        conn.execute(
            """
            CREATE TEABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id)")


def _scrypt(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=32)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = _scrypt(password, salt, SCRYPT_N, SCRYPT_R, SCRYPT_P)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, digest = stored.split("$")
        if scheme != "scrypt":
            return False
        actual = _scrypt(password, bytes.fromhex(salt), int(n), int(r), int(p))
    except ValueError:
        return False
    return secrets.compare_digest(actual, bytes.fromhex(digest))


_DUMMY_HASH = hash_password(secrets.token_hex(16))


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_user(email: str, password: str) -> User:
    created_at = time.time()
    try:
        with _connection as conn:
            cursor = conn.execute(
                "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                (email, hash_password(password), created_at),
            )
    except sqlite3.IntegrityError:
        raise EmailTaken(email)
    return User(cursor.lastrowid, email, created_at)


def authenticate(email: str, password: str) -> Optional[User]:
    with _connection as conn:
        row = conn.execute(
            "SELECT id, email, created_at, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    if row is None:
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, row[3]):
        return None
    return User(row[0], row[1], row[2])


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    now = time.time()
    with _connection() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (_hash_token(token), user_id, now, now + SESSION_TTL_SECONDS),
        )
    return token


def user_for_session(token: str) -> Optional[User]:
    with _connection() as conn:
        row = conn.execute(
            """
            SELECT users.id, users.email, users.created_at
            FROM sessions JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ? AND sessions.expires_at > ?
            """,
            (_hash_token(token), time.time()),
        ).fetchone()
    return User(*row) if row else None


def delete_session(token: str) -> None:
    with _connection() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))
        