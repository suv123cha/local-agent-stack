"""
memory/short_memory.py
======================
Short-term (session) memory backed by Redis.

Each session stores an ordered list of message dicts:
  [{"role": "user"|"assistant", "content": "..."}]

The list is serialised as JSON and stored under the key
  chat:<session_id>

with a configurable TTL (default 24 h).
"""

import json
import logging
import os

import redis.asyncio as redis

log = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SESSION_TTL = int(os.getenv("SESSION_TTL_SECONDS", 86400))  # 24 hours
MAX_HISTORY = int(os.getenv("MAX_HISTORY_MESSAGES", 40))


def _client() -> redis.Redis:
    return redis.from_url(REDIS_URL, decode_responses=True)


def _key(session_id: str) -> str:
    return f"chat:{session_id}"


async def get_history(session_id: str) -> list[dict]:
    """Return the full conversation history for *session_id*."""
    async with _client() as r:
        raw = await r.get(_key(session_id))
        if not raw:
            return []
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            log.warning("Corrupt history for session %s – resetting.", session_id)
            return []


async def append_message(session_id: str, role: str, content: str) -> None:
    """Append a single message to the session history and refresh TTL."""
    history = await get_history(session_id)
    history.append({"role": role, "content": content})

    # Keep history bounded to avoid giant prompts
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    async with _client() as r:
        await r.set(_key(session_id), json.dumps(history), ex=SESSION_TTL)


async def clear_history(session_id: str) -> None:
    """Delete all history for a session (e.g. on logout / reset)."""
    async with _client() as r:
        await r.delete(_key(session_id))
