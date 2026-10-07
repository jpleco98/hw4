"""Password hashing, login throttling and server-side sessions for Campus Customs.

Password hash formats (both live in users.password_hash):
  legacy (seed DB):  pbkdf2_sha256$<salt>$<hex digest>                  — 120,000 iterations
  current:           pbkdf2_sha256$<iterations>$<salt>$<hex digest>     — 600,000 iterations
Legacy hashes still verify and are upgraded to the current format on the next successful login.
"""

import hashlib
import hmac
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000  # OWASP 2023 recommendation for PBKDF2-HMAC-SHA256
LEGACY_ITERATIONS = 120_000  # what the seed users were hashed with
SALT_BYTES = 16

SESSION_COOKIE = "cc_session"
SESSION_TTL = timedelta(days=7)

MAX_FAILURES_PER_EMAIL = 5   # stops guessing one account's password
MAX_FAILURES_PER_IP = 20     # stops one client spraying guesses across many accounts
FAILURE_WINDOW_SECONDS = 15 * 60


# ---------- password hashing ----------

def _pbkdf2(password: str, salt: str, iterations: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(SALT_BYTES)
    return f"{ALGORITHM}${ITERATIONS}${salt}${_pbkdf2(password, salt, ITERATIONS)}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if parts[0] != ALGORITHM:
        return False
    if len(parts) == 3:  # legacy seed format
        _, salt, digest = parts
        iterations = LEGACY_ITERATIONS
    elif len(parts) == 4:
        _, iters, salt, digest = parts
        iterations = int(iters)
    else:
        return False
    return hmac.compare_digest(_pbkdf2(password, salt, iterations), digest)


def needs_rehash(stored: str) -> bool:
    parts = stored.split("$")
    return len(parts) != 4 or int(parts[1]) < ITERATIONS


# Used when the email doesn't exist, so a miss costs the same time as a wrong password
# (stops attackers from discovering which emails have accounts by timing the response).
DUMMY_HASH = hash_password(secrets.token_hex(16))


# ---------- login throttling ----------

_failures: dict[str, deque[float]] = defaultdict(deque)


def _recent(key: str) -> deque[float]:
    q, cutoff = _failures[key], time.monotonic() - FAILURE_WINDOW_SECONDS
    while q and q[0] < cutoff:
        q.popleft()
    return q


def is_locked(key: str) -> bool:
    limit = MAX_FAILURES_PER_IP if key.startswith("ip:") else MAX_FAILURES_PER_EMAIL
    return len(_recent(key)) >= limit


def record_failure(key: str) -> None:
    _recent(key).append(time.monotonic())


def clear_failures(key: str) -> None:
    _failures.pop(key, None)


# ---------- sessions ----------

def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def ensure_sessions_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )


def create_session(conn: sqlite3.Connection, user_id: int) -> str:
    """Return a fresh random token; only its SHA-256 is stored, so a DB leak can't hijack sessions."""
    token = secrets.token_urlsafe(32)
    expires = (datetime.now(timezone.utc) + SESSION_TTL).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
        (_token_hash(token), user_id, expires),
    )
    return token


def session_user_id(conn: sqlite3.Connection, token: str | None) -> int | None:
    if not token:
        return None
    row = conn.execute(
        "SELECT user_id FROM sessions WHERE token_hash = ? AND expires_at > datetime('now')",
        (_token_hash(token),),
    ).fetchone()
    return row[0] if row else None


def delete_session(conn: sqlite3.Connection, token: str | None) -> None:
    if token:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))
