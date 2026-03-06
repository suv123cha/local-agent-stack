"""
agents/memory_agent.py
======================
Memory Agent – retrieves relevant context for the current query.

Combines three memory sources:
  1. Short-term  – recent conversation turns (from Redis, already
                   passed in as history list)
  2. Vector      – semantically similar long-term memories (Qdrant)
  3. Profile     – structured user facts (MongoDB)

Returns a formatted context string ready to be injected into the
LLM prompt.
"""

import logging

from memory.vector_memory import search_memories
from memory.profile_memory import profile_summary

log = logging.getLogger(__name__)


async def retrieve_context(session_id: str, query: str, top_k: int = 5) -> str:
    """
    Build a context string for *query* by pulling from vector memory
    and the user profile.

    The short-term (Redis) history is handled separately by the
    orchestrator and passed directly into the LLM messages array.
    """
    parts: list[str] = []

    # 1. Structured profile
    profile = profile_summary(session_id)
    if profile and "No profile" not in profile:
        parts.append("=== User Profile ===")
        parts.append(profile)

    # 2. Semantic long-term memories
    memories = await search_memories(query, top_k=top_k)
    if memories:
        parts.append("=== Relevant Memories ===")
        for mem in memories:
            parts.append(f"• {mem}")

    if not parts:
        return ""

    return "\n".join(parts)
