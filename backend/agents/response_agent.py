"""
agents/response_agent.py
========================
Response Agent – generates the final reply sent to the user.

Assembles a structured prompt from:
  • System instructions
  • Retrieved memory context
  • Tool output (if any)
  • Conversation history
  • The user's latest message

Then calls the LLM and returns the reply string.
"""

import logging

from llm.ollama_client import chat_completion

log = logging.getLogger(__name__)

_BASE_SYSTEM = """You are a helpful, knowledgeable, and friendly AI assistant.

You have access to memory about the user and can use tools to answer questions.
Always be clear, concise, and accurate.
If tool results are provided, base your answer on them.
If memory context is provided, use it to personalise your response.
Never make up facts – if you don't know something, say so.
"""


async def generate_response(
    user_message: str,
    history: list[dict],
    memory_context: str = "",
    tool_output: str | None = None,
    plan: dict | None = None,
) -> str:
    """
    Build the full message array and call the LLM.

    Parameters
    ----------
    user_message:   The latest user input.
    history:        List of previous {"role", "content"} dicts (short-term memory).
    memory_context: Retrieved long-term memories and profile info.
    tool_output:    Result from the Tool Agent (None if no tool was used).
    plan:           The plan dict from the Planner Agent (for logging).
    """
    system_parts = [_BASE_SYSTEM]

    if memory_context:
        system_parts.append("\n--- Context from Memory ---")
        system_parts.append(memory_context)
        system_parts.append("--- End of Memory Context ---\n")

    if tool_output:
        action = (plan or {}).get("action", "TOOL")
        system_parts.append(f"\n--- {action} Result ---")
        system_parts.append(tool_output)
        system_parts.append(f"--- End of {action} Result ---\n")
        system_parts.append(
            "Use the above result to answer the user's question accurately."
        )

    system_content = "\n".join(system_parts)

    # Build messages: system → history → current user message
    messages: list[dict] = [{"role": "system", "content": system_content}]

    # Include recent history (skip the very last user message if already appended)
    for msg in history[:-1]:  # orchestrator appends current msg before calling us
        messages.append(msg)

    messages.append({"role": "user", "content": user_message})

    if plan:
        log.info(
            "Generating response | action=%s | tool_output=%s | history_len=%d",
            plan.get("action"),
            bool(tool_output),
            len(history),
        )

    reply = await chat_completion(messages, temperature=0.7, max_tokens=1024)
    return reply
