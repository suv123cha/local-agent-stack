"""
orchestrator/agent_loop.py
==========================
Central orchestration loop.

Implements the full agent pipeline:

  receive_user_input
       ↓
  retrieve_memory          (Memory Agent)
       ↓
  plan                     (Planner Agent)
       ↓
  call_tool_if_needed      (Tool Agent)
       ↓
  generate_response        (Response Agent)
       ↓
  store_short_term_memory  (Redis)
       ↓
  reflect_and_store        (Reflection Agent → Qdrant + MongoDB)

The reflection step is fired as a background task so it never
adds latency to the user-facing response.
"""

import asyncio
import logging

from agents.planner_agent import plan
from agents.tool_agent import execute_tool
from agents.memory_agent import retrieve_context
from agents.reflection_agent import reflect
from agents.response_agent import generate_response
from memory.short_memory import get_history, append_message

log = logging.getLogger(__name__)


async def run_agent_loop(session_id: str, user_message: str) -> str:
    """
    Execute the full multi-agent pipeline for one user turn.

    Parameters
    ----------
    session_id:   Unique identifier for the conversation session.
    user_message: The raw message submitted by the user.

    Returns
    -------
    str – The assistant's reply to be sent back to the client.
    """
    log.info("=== Agent Loop START | session=%s ===", session_id)

    # ── 1. Retrieve short-term history ──────────────────────────────────────
    history = await get_history(session_id)
    log.debug("History: %d messages", len(history))

    # ── 2. Retrieve long-term memory & user profile ──────────────────────────
    memory_context = await retrieve_context(session_id, user_message)
    log.debug("Memory context length: %d chars", len(memory_context))

    # ── 3. Plan – decide what action to take ────────────────────────────────
    plan_result = await plan(user_message, context=memory_context)
    log.info("Plan: action=%s | reason=%s", plan_result["action"], plan_result.get("reason"))

    # ── 4. Execute tool (if required) ───────────────────────────────────────
    # Pass location from user profile as extra context for job searches
    extra_ctx: dict = {}
    if plan_result["action"] == "JOBS":
        from memory.profile_memory import get_profile
        profile = get_profile(session_id)
        if profile.get("location"):
            extra_ctx["location"] = profile["location"]

    tool_output = await execute_tool(
        action=plan_result["action"],
        query=plan_result["query"],
        context=extra_ctx,
    )

    # ── 5. Append user message to short-term memory ─────────────────────────
    await append_message(session_id, "user", user_message)
    history.append({"role": "user", "content": user_message})

    # ── 6. Generate response ─────────────────────────────────────────────────
    reply = await generate_response(
        user_message=user_message,
        history=history,
        memory_context=memory_context,
        tool_output=tool_output,
        plan=plan_result,
    )

    # ── 7. Append assistant reply to short-term memory ──────────────────────
    await append_message(session_id, "assistant", reply)

    # ── 8. Reflect & store long-term memories (background) ──────────────────
    asyncio.create_task(reflect(session_id, user_message, reply))

    log.info("=== Agent Loop END | session=%s ===", session_id)
    return reply
