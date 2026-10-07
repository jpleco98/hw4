"""Append-only audit trail of agent loop activity (Problem 12).

Every chat message (one agent run) appends one AuditEntry to output/audit_trail.json:
when it ran, every model request, tool call (name + short args), tool result (short),
fact-check retry, the stop reason, token usage and the final answer.

The file is never wiped between runs. It is a JSON list; each write reads the list, appends,
and writes to a temp file that atomically replaces the old one, under a lock (FastAPI handles
requests concurrently). If the file is ever unreadable it is renamed aside, not overwritten.
"""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
)

from models import AuditEntry, AuditStep

AUDIT_FILE = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
ARGS_CHARS = 200  # "short args"
RESULT_CHARS = 300  # "short results"
TEXT_CHARS = 400  # message / reply
FINAL_TOOL = "final_result"  # Pydantic AI's name for the structured-output tool

_lock = threading.Lock()
_adapter = TypeAdapter(list[AuditEntry])


def new_run_id() -> str:
    return uuid4().hex[:12]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def short(value, limit: int) -> str:
    if hasattr(value, "model_dump_json"):
        text = value.model_dump_json()
    elif isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, default=str, ensure_ascii=False)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _ts(dt) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds") if dt else now_iso()


def steps_from_messages(messages: list[ModelMessage]) -> tuple[list[AuditStep], int, int]:
    """Flatten Pydantic AI messages into ordered audit steps. Returns (steps, model_requests, tool_calls)."""
    steps: list[AuditStep] = []
    requests = tool_calls = 0

    def add(**kw) -> None:
        steps.append(AuditStep(step=len(steps) + 1, **kw))

    for msg in messages:
        if isinstance(msg, ModelResponse):
            requests += 1
            add(kind="model_request", time=_ts(msg.timestamp), result=f"finish_reason={msg.finish_reason}")
            for part in msg.parts:
                if isinstance(part, ToolCallPart):
                    if part.tool_name == FINAL_TOOL:
                        add(kind="final_output", time=_ts(msg.timestamp), tool=FINAL_TOOL, args=short(part.args_as_json_str(), ARGS_CHARS))
                    else:
                        tool_calls += 1
                        add(kind="tool_call", time=_ts(msg.timestamp), tool=part.tool_name, args=short(part.args_as_json_str(), ARGS_CHARS))
                elif isinstance(part, TextPart) and part.content.strip():
                    add(kind="final_output", time=_ts(msg.timestamp), result=short(part.content, RESULT_CHARS))
        elif isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, ToolReturnPart) and part.tool_name != FINAL_TOOL:
                    add(kind="tool_result", time=_ts(part.timestamp), tool=part.tool_name, result=short(part.content, RESULT_CHARS))
                elif isinstance(part, RetryPromptPart):
                    # e.g. the fact-checker rejecting a draft, or a tool-argument validation error
                    add(kind="retry", time=_ts(part.timestamp), tool=part.tool_name, result=short(part.content, RESULT_CHARS))
    return steps, requests, tool_calls


def append_entry(entry: AuditEntry) -> None:
    """Append one entry; never wipes existing history."""
    with _lock:
        entries: list[AuditEntry] = []
        if AUDIT_FILE.exists() and AUDIT_FILE.stat().st_size:
            try:
                entries = _adapter.validate_json(AUDIT_FILE.read_bytes())
            except ValidationError:
                # keep the unreadable file for inspection instead of overwriting it
                AUDIT_FILE.rename(AUDIT_FILE.with_suffix(f".unreadable-{new_run_id()}.json"))
        entries.append(entry)
        AUDIT_FILE.parent.mkdir(exist_ok=True)
        tmp = AUDIT_FILE.with_suffix(".json.tmp")
        tmp.write_bytes(_adapter.dump_json(entries, indent=2))
        os.replace(tmp, AUDIT_FILE)
