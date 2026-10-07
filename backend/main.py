"""Campus Customs API — the file Uvicorn runs.

Run from the backend/ folder:
    uvicorn main:app --reload --port 8000

Problem 3: product endpoints + product images.
Problem 4: create-account / login / logout with hashed passwords and cookie sessions.
Problem 5: /api/chat is answered by the Pydantic AI shop agent (agent.py).
Problem 9: /api/chat/stream streams live tool status + the reply; replies carry a fact-check summary.
Problem 12: every agent run is appended to output/audit_trail.json (audit.py).
"""

import json
import logging
import re
import sqlite3
import threading
import time
from pathlib import Path

from fastapi import Cookie, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic_ai import capture_run_messages
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.messages import ModelResponse

import audit
import auth
from images import trimmed_photo
from agent import MODEL_NAME, AgentNotConfigured, run_chat, stream_chat
from models import (
    AuditEntry,
    ChatHistory,
    ChatHistoryItem,
    ChatReply,
    ChatRequest,
    ChatTurn,
    CustomerContext,
    LoginRequest,
    PageResults,
    ProductDetail,
    ProductSummary,
    ShopDeps,
    ShopReply,
    SignupRequest,
    UserPublic,
    Verification,
)
from tools import DATA_DIR, get_conn, list_categories as db_categories, list_products as db_products
from tools import SIZE_ORDER, build_page_context, load_product_detail, normalize_size, summaries_by_ids

log = logging.getLogger("campus_customs")

HISTORY_TURNS = 10  # earlier messages given to the agent as context

# Shown when the model provider's content filter blocks a message (e.g. jailbreak attempts).
FILTERED_REPLY = (
    "Sorry, I can't help with that. I'm here to help you find Campus Customs gear: "
    "ask me about products, prices, sizes or stock!"
)
# Shown if the fact-checker rejects every draft: better no number than a wrong one.
UNVERIFIED_REPLY = (
    "Sorry, I couldn't double-check the exact price or stock for that just now. "
    "Please open the product page for live sizes and prices, or ask me again."
)

app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Product photos: served with baked-in black bars trimmed (images.py). Only files that really exist in
# data/products are served, by exact name, so the DB file and other paths can never be reached.
PRODUCTS_DIR = DATA_DIR / "products"
IMAGE_CACHE = Path(__file__).resolve().parent / ".image_cache"
PHOTO_NAME = re.compile(r"^[a-z0-9-]+\.jpg$")


def _warm_image_cache() -> None:
    for f in sorted(PRODUCTS_DIR.glob("*.jpg")):
        try:
            trimmed_photo(f, IMAGE_CACHE)
        except Exception:  # noqa: BLE001 - a bad photo just falls back to the original
            log.exception("Could not trim %s", f.name)


threading.Thread(target=_warm_image_cache, daemon=True, name="image-cache").start()


@app.get("/media/products/{filename}", include_in_schema=False)
def product_photo(filename: str) -> FileResponse:
    source = PRODUCTS_DIR / filename
    if not PHOTO_NAME.match(filename) or not source.is_file():
        raise HTTPException(404, "Not found")
    try:
        path = trimmed_photo(source, IMAGE_CACHE)
    except Exception:  # noqa: BLE001
        log.exception("Could not trim %s", filename)
        path = source
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400"})

with get_conn() as _conn:
    auth.ensure_sessions_table(_conn)
    # Customer memory (Problem 8): chat_messages is the history table. Add the page the shopper was on
    # for each saved message, and an index so loading one shopper's history stays fast.
    if "page_path" not in {r["name"] for r in _conn.execute("PRAGMA table_info(chat_messages)")}:
        _conn.execute("ALTER TABLE chat_messages ADD COLUMN page_path TEXT")
    _conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages (user_id, id)")


# ---------- products ----------

@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/products", response_model=list[ProductSummary])
def list_products(
    q: str | None = Query(None, description="Free-text search over name, description, tags"),
    category: str | None = Query(None, description="One of the normalized categories"),
) -> list[ProductSummary]:
    return db_products(q, category)


@app.get("/api/categories", response_model=list[str])
def list_categories() -> list[str]:
    return db_categories()


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: str) -> ProductDetail:
    detail = load_product_detail(product_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return detail


# ---------- auth ----------

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def to_public(row: sqlite3.Row) -> UserPublic:
    first = row["first_name"] or row["name"].split(" ")[0]
    last = row["last_name"] or " ".join(row["name"].split(" ")[1:])
    return UserPublic(id=row["id"], first_name=first, last_name=last, name=row["name"], email=row["email"])


def set_session_cookie(response: Response, token: str) -> None:
    # HttpOnly: page JavaScript (or an XSS payload) can't read it. SameSite=Lax: blocks cross-site POSTs.
    response.set_cookie(
        auth.SESSION_COOKIE,
        token,
        max_age=int(auth.SESSION_TTL.total_seconds()),
        httponly=True,
        samesite="lax",
        secure=False,  # set True when served over HTTPS
        path="/",
    )


def validate_password(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(422, "Password must be at least 8 characters.")
    if not (re.search(r"[A-Za-z]", password) and re.search(r"\d", password)):
        raise HTTPException(422, "Password must include at least one letter and one number.")


@app.post("/api/auth/signup", response_model=UserPublic, status_code=201)
def signup(body: SignupRequest, response: Response) -> UserPublic:
    first, last = body.first_name.strip(), body.last_name.strip()
    email = body.email.strip().lower()
    if not first or not last:
        raise HTTPException(422, "First and last name are required.")
    if not EMAIL_RE.match(email):
        raise HTTPException(422, "Please enter a valid email address.")
    if body.password != body.confirm_password:
        raise HTTPException(422, "Passwords do not match.")
    validate_password(body.password)

    with get_conn() as conn:
        if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
            raise HTTPException(409, "An account with that email already exists. Try logging in.")
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
            (f"{first} {last}", email, auth.hash_password(body.password), first, last),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
        token = auth.create_session(conn, row["id"])
    set_session_cookie(response, token)
    return to_public(row)


@app.post("/api/auth/login", response_model=UserPublic)
def login(body: LoginRequest, request: Request, response: Response) -> UserPublic:
    email = body.email.strip().lower()
    client = request.client.host if request.client else "unknown"
    keys = (f"email:{email}", f"ip:{client}")
    if any(auth.is_locked(k) for k in keys):
        raise HTTPException(429, "Too many failed attempts. Please wait 15 minutes and try again.")

    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
        ok = auth.verify_password(body.password, row["password_hash"] if row else auth.DUMMY_HASH) and row is not None
        if not ok:
            for k in keys:
                auth.record_failure(k)
            # Same message whether the email or the password was wrong (no account enumeration).
            raise HTTPException(401, "Invalid email or password.")
        # Only reset the per-account counter; the per-IP one keeps running so an attacker
        # can't reset it by logging into their own account between guesses.
        auth.clear_failures(keys[0])
        if auth.needs_rehash(row["password_hash"]):
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (auth.hash_password(body.password), row["id"]))
        token = auth.create_session(conn, row["id"])
    set_session_cookie(response, token)
    return to_public(row)


@app.post("/api/auth/logout", status_code=204)
def logout(response: Response, cc_session: str | None = Cookie(default=None)) -> None:
    with get_conn() as conn:
        auth.delete_session(conn, cc_session)
    response.delete_cookie(auth.SESSION_COOKIE, path="/")


def current_user(cc_session: str | None) -> UserPublic | None:
    with get_conn() as conn:
        user_id = auth.session_user_id(conn, cc_session)
        if user_id is None:
            return None
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return to_public(row) if row else None


@app.get("/api/auth/me", response_model=UserPublic)
def me(cc_session: str | None = Cookie(default=None)) -> UserPublic:
    user = current_user(cc_session)
    if user is None:
        raise HTTPException(401, "Not logged in.")
    return user



# ---------- chat ----------

def saved_product_ids(products_json: str | None) -> list[str]:
    if not products_json:
        return []
    try:
        return [p["product_id"] for p in json.loads(products_json) if isinstance(p, dict) and "product_id" in p]
    except (json.JSONDecodeError, TypeError):
        return []


def load_saved_turns(user_id: int, limit: int) -> list[sqlite3.Row]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content, products_json, created_at FROM chat_messages WHERE user_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return list(reversed(rows))


def save_exchange(user_id: int, message: str, reply: ChatReply, page_path: str) -> None:
    """Persist one user turn + one assistant turn (logged-in shoppers only)."""
    products_json = json.dumps([p.model_dump() for p in reply.products]) if reply.products else None
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, page_path) VALUES (?, 'user', ?, ?)",
            (user_id, message, page_path),
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json, page_path) VALUES (?, 'assistant', ?, ?, ?)",
            (user_id, reply.reply, products_json, page_path),
        )


def customer_context(user: UserPublic) -> CustomerContext:
    """Who is chatting, for the agent's deps. Built server-side from the session, never from the request body."""
    with get_conn() as conn:
        created = conn.execute("SELECT created_at FROM users WHERE id = ?", (user.id,)).fetchone()[0]
        returning = conn.execute("SELECT 1 FROM chat_messages WHERE user_id = ? LIMIT 1", (user.id,)).fetchone()
    return CustomerContext(
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.name,
        email=user.email,
        member_since=created,
        returning=returning is not None,
    )


def prepare_chat(req: ChatRequest, user: UserPublic | None) -> tuple[str, list[ChatTurn], ShopDeps]:
    message = req.message.strip()
    if not message:
        raise HTTPException(422, "Message is empty.")
    # Logged-in shoppers: context comes from the server-side saved conversation (can't be forged).
    # Guests: the widget sends its recent turns.
    if user:
        history = [ChatTurn(role=r["role"], content=r["content"]) for r in load_saved_turns(user.id, HISTORY_TURNS)]
    else:
        history = req.history[-HISTORY_TURNS:]
    page = build_page_context(req.page)  # re-validated against the DB
    return message, history, ShopDeps(customer=customer_context(user) if user else None, page=page)


def agent_failure(exc: Exception) -> ShopReply | HTTPException:
    """Map an agent error to a safe reply (shown as a normal answer) or an HTTP error."""
    if isinstance(exc, AgentNotConfigured):
        log.error("Agent not configured: %s", exc)
        return HTTPException(503, "The shopping assistant isn't configured yet (missing API key).")
    if isinstance(exc, ModelHTTPError) and "content_filter" in str(exc.body):
        log.warning("Message blocked by the provider's content filter")
        return ShopReply(reply=FILTERED_REPLY)
    if isinstance(exc, UnexpectedModelBehavior):
        # e.g. the fact-checker rejected every draft: never show unverified numbers
        log.warning("Agent output failed validation: %s", exc)
        return ShopReply(reply=UNVERIFIED_REPLY)
    if isinstance(exc, UsageLimitExceeded):
        return HTTPException(502, "That question took too many steps for me. Could you ask it a bit more simply?")
    log.exception("Agent run failed", exc_info=exc)
    return HTTPException(502, "The shopping assistant is having trouble right now. Please try again in a moment.")


def stop_reason_for(exc: Exception | None) -> str:
    if exc is None:
        return "final_answer"
    if isinstance(exc, AgentNotConfigured):
        return "not_configured"
    if isinstance(exc, ModelHTTPError) and "content_filter" in str(exc.body):
        return "content_filter"
    if isinstance(exc, UnexpectedModelBehavior):
        return "fact_check_exhausted"
    if isinstance(exc, UsageLimitExceeded):
        return "usage_limit"
    return "model_error"


def record_run(
    *,
    run_id: str,
    started: float,
    started_at: str,
    endpoint: str,
    user: UserPublic | None,
    deps: ShopDeps,
    message: str,
    history: list[ChatTurn],
    messages: list,
    exc: Exception | None,
    reply: ChatReply | None,
) -> None:
    """Append this agent run to output/audit_trail.json. Auditing must never break a chat, so errors are logged."""
    try:
        steps, n_requests, n_tools = audit.steps_from_messages(messages)
        usages = [m.usage for m in messages if isinstance(m, ModelResponse) and m.usage]
        audit.append_entry(
            AuditEntry(
                run_id=run_id,
                started_at=started_at,
                duration_ms=int((time.monotonic() - started) * 1000),
                endpoint=endpoint,
                model=MODEL_NAME,
                shopper=f"user:{user.id}" if user else "guest",
                page=deps.page.path if deps.page else None,
                message=audit.short(message, audit.TEXT_CHARS),
                history_turns=len(history),
                steps=steps,
                model_requests=n_requests,
                tool_calls=n_tools,
                input_tokens=sum(u.input_tokens or 0 for u in usages) if usages else None,
                output_tokens=sum(u.output_tokens or 0 for u in usages) if usages else None,
                stop_reason=stop_reason_for(exc),
                error=f"{type(exc).__name__}: {audit.short(str(exc), 200)}" if exc else None,
                fact_check=deps.fact_check if (deps.fact_check.prices_checked or deps.fact_check.quantities_checked or deps.fact_check.retries) else None,
                reply=audit.short(reply.reply, audit.TEXT_CHARS) if reply else None,
                product_ids=[p.product_id for p in reply.products] if reply else [],
                page_results=len(reply.page.products) if reply and reply.page else None,
                size=reply.size if reply else None,
            )
        )
    except Exception:  # noqa: BLE001
        log.exception("Could not write audit entry")


def finish_chat(result: ShopReply, deps: ShopDeps, user: UserPublic | None, message: str) -> ChatReply:
    # Cards are built from the DB, so prices and stock shown on them are always the real ones.
    reply = ChatReply(reply=result.reply, products=summaries_by_ids(result.product_ids))
    size = normalize_size(result.size)
    reply.size = size if size in SIZE_ORDER else None  # ignore anything that isn't a real size
    if result.page:
        page_products = summaries_by_ids(result.page.product_ids)  # unknown ids are dropped
        if page_products:
            reply.page = PageResults(title=result.page.title, products=page_products)
    fc = deps.fact_check
    if fc.prices_checked or fc.quantities_checked or fc.retries:
        reply.verification = Verification(
            prices_checked=fc.prices_checked, quantities_checked=fc.quantities_checked, corrected=fc.retries > 0
        )
    if user:
        save_exchange(user.id, message, reply, deps.page.path if deps.page else "/")
    return reply


@app.post("/api/chat", response_model=ChatReply)
async def chat(req: ChatRequest, cc_session: str | None = Cookie(default=None)) -> ChatReply:
    user = current_user(cc_session)
    message, history, deps = prepare_chat(req, user)
    run = {"run_id": audit.new_run_id(), "started": time.monotonic(), "started_at": audit.now_iso(), "endpoint": "/api/chat"}
    error: Exception | None = None
    # capture_run_messages keeps the loop's messages even if the run raises (usage limit, fact-check exhausted…)
    with capture_run_messages() as messages:
        try:
            result = await run_chat(message, history, deps)
        except Exception as e:  # noqa: BLE001 - mapped to a safe reply or HTTP error
            error = e
            outcome = agent_failure(e)
            if isinstance(outcome, HTTPException):
                record_run(**run, user=user, deps=deps, message=message, history=history, messages=messages, exc=e, reply=None)
                raise outcome
            result = outcome
    reply = finish_chat(result, deps, user, message)
    record_run(**run, user=user, deps=deps, message=message, history=history, messages=messages, exc=error, reply=reply)
    return reply


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest, cc_session: str | None = Cookie(default=None)) -> StreamingResponse:
    """Same as /api/chat, but streams NDJSON events: status lines while tools run, the reply as it is
    written, and a final {"type": "done", "reply": ChatReply} (or {"type": "error", "message"})."""
    user = current_user(cc_session)
    message, history, deps = prepare_chat(req, user)

    async def events():
        def line(obj: dict) -> str:
            return json.dumps(obj, ensure_ascii=False) + "\n"

        run = {"run_id": audit.new_run_id(), "started": time.monotonic(), "started_at": audit.now_iso(), "endpoint": "/api/chat/stream"}
        audit_args = {"user": user, "deps": deps, "message": message, "history": history}
        result: ShopReply | None = None
        error: Exception | None = None
        with capture_run_messages() as messages:
            try:
                async for event in stream_chat(message, history, deps):
                    if event["type"] == "result":
                        result = event["output"]
                    else:
                        yield line(event)
            except Exception as e:  # noqa: BLE001
                error = e
                outcome = agent_failure(e)
                if isinstance(outcome, HTTPException):
                    record_run(**run, **audit_args, messages=messages, exc=e, reply=None)
                    yield line({"type": "error", "message": outcome.detail})
                    return
                yield line({"type": "reset"})
                result = outcome
        if result is None:
            record_run(**run, **audit_args, messages=messages, exc=RuntimeError("stream ended without a result"), reply=None)
            yield line({"type": "error", "message": "The shopping assistant didn't finish. Please try again."})
            return
        reply = finish_chat(result, deps, user, message)
        record_run(**run, **audit_args, messages=messages, exc=error, reply=reply)
        yield line({"type": "done", "reply": reply.model_dump()})

    # no-transform/no buffering so each line reaches the browser as soon as it is written
    return StreamingResponse(
        events(), media_type="application/x-ndjson", headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"}
    )


@app.get("/api/chat/history", response_model=ChatHistory)
def chat_history(cc_session: str | None = Cookie(default=None)) -> ChatHistory:
    user = current_user(cc_session)
    if user is None:
        raise HTTPException(401, "Not logged in.")
    items = [
        ChatHistoryItem(
            role=r["role"],
            content=r["content"],
            products=summaries_by_ids(saved_product_ids(r["products_json"])),
            created_at=r["created_at"],
        )
        for r in load_saved_turns(user.id, 50)
    ]
    return ChatHistory(messages=items)


@app.delete("/api/chat/history", status_code=204)
def clear_chat_history(cc_session: str | None = Cookie(default=None)) -> None:
    """Let a logged-in shopper erase their own saved conversation."""
    user = current_user(cc_session)
    if user is None:
        raise HTTPException(401, "Not logged in.")
    with get_conn() as conn:
        conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user.id,))
