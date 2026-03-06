"""
llm/ollama_client.py
====================
Thin async wrapper around the Ollama REST API.
Handles both streaming and non-streaming completions.
"""

import os
import logging
import httpx

log = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """
    Send a list of OpenAI-style messages to Ollama and return the
    assistant reply as a plain string.

    messages format: [{"role": "system"|"user"|"assistant", "content": "..."}]
    """
    target_model = model or OLLAMA_MODEL

    payload = {
        "model": target_model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"].strip()
    except httpx.ConnectError:
        log.error("Cannot reach Ollama at %s – is the container running?", OLLAMA_URL)
        return "[Error: LLM service unavailable. Please ensure Ollama is running.]"
    except Exception as exc:
        log.exception("Ollama request failed: %s", exc)
        return f"[Error: {exc}]"


async def simple_prompt(prompt: str, system: str = "", **kwargs) -> str:
    """Convenience wrapper for single-turn prompts."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return await chat_completion(messages, **kwargs)
