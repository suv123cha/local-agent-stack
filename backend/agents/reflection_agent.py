"""
agents/reflection_agent.py
==========================
Reflection Agent – runs AFTER a response is delivered.

Analyses the latest user message (and optionally the assistant reply)
to extract:
  • Factual statements about the user (location, preferences, etc.)
  • Structured profile updates (name, location, skills, preferences)

Extracted facts are:
  1. Stored as vector embeddings in Qdrant (long-term memory)
  2. Used to update the MongoDB user profile (structured memory)

This runs asynchronously and should not block the response path.
"""

import json
import logging
import re

from llm.ollama_client import simple_prompt
from memory.vector_memory import store_memory
from memory.profile_memory import update_profile

log = logging.getLogger(__name__)

_SYSTEM = """You are a reflection agent inside an AI assistant system.

Your job is to analyse a conversation snippet and extract useful personal information about the user.

Extract ONLY clearly stated facts. Do NOT infer or guess.

Return ONLY a valid JSON object on a single line with this schema:
{
  "facts": ["<fact 1>", "<fact 2>"],
  "profile_updates": {
    "name": "<name or null>",
    "location": "<city/country or null>",
    "skills": ["<skill>"],
    "preferences": {"<key>": "<value>"}
  }
}

Rules:
- facts: concise statements like "User lives in Berlin" or "User is looking for backend engineering jobs"
- profile_updates: only include keys where you found concrete information
- If nothing useful is found, return {"facts": [], "profile_updates": {}}
- Do NOT include any text outside the JSON object
"""


async def reflect(session_id: str, user_message: str, assistant_reply: str) -> None:
    """
    Analyse the exchange and persist any extracted user information.
    Designed to be called with asyncio.create_task() so it never
    blocks the response path.
    """
    snippet = f"User: {user_message}\nAssistant: {assistant_reply}"

    try:
        raw = await simple_prompt(snippet, system=_SYSTEM, temperature=0.1, max_tokens=400)
        data = _parse_reflection(raw)

        facts: list[str] = data.get("facts", [])
        profile_updates: dict = data.get("profile_updates", {})

        # Store individual facts in vector memory
        for fact in facts:
            if fact.strip():
                await store_memory(fact, metadata={"session": session_id, "type": "fact"})
                log.info("Stored memory: %s", fact)

        # Update structured profile
        if profile_updates:
            update_profile(session_id, profile_updates)
            log.info("Profile updated for session %s: %s", session_id, profile_updates)

    except Exception as exc:
        # Reflection is best-effort – never crash the pipeline
        log.warning("Reflection failed for session %s: %s", session_id, exc)


def _parse_reflection(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    log.debug("Reflection produced no parseable JSON: %r", raw[:120])
    return {"facts": [], "profile_updates": {}}
