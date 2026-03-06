"""
api/chat.py
===========
FastAPI router exposing the /chat endpoint.

POST /api/chat
  Body:  {"session": "<session_id>", "message": "<user text>"}
  Reply: {"response": "<assistant reply>"}

GET /api/chat/history/{session_id}
  Reply: {"session": "...", "history": [...]}

DELETE /api/chat/history/{session_id}
  Reply: {"cleared": true}
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from orchestrator.agent_loop import run_agent_loop
from memory.short_memory import get_history, clear_history
from memory.profile_memory import get_profile

log = logging.getLogger(__name__)

router = APIRouter()


# ── Request / Response Models ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session: str = Field(..., min_length=1, max_length=128, description="Unique session ID")
    message: str = Field(..., min_length=1, max_length=4096, description="User message")


class ChatResponse(BaseModel):
    response: str
    session: str


class HistoryResponse(BaseModel):
    session: str
    history: list[dict]


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Main chat endpoint.  Runs the full agent loop and returns the reply.
    """
    log.info("POST /chat | session=%s | message=%r", req.session, req.message[:80])
    try:
        reply = await run_agent_loop(session_id=req.session, user_message=req.message)
        return ChatResponse(response=reply, session=req.session)
    except Exception as exc:
        log.exception("Agent loop failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/chat/history/{session_id}", response_model=HistoryResponse)
async def get_chat_history(session_id: str):
    """Return the conversation history for a session."""
    history = await get_history(session_id)
    return HistoryResponse(session=session_id, history=history)


@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear all history for a session (e.g. on 'New Chat')."""
    await clear_history(session_id)
    return {"cleared": True, "session": session_id}


@router.get("/profile/{session_id}")
async def get_user_profile(session_id: str):
    """Return the structured user profile stored in MongoDB."""
    return get_profile(session_id)
