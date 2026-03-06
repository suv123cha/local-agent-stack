"""
agents/planner_agent.py
=======================
Planner Agent – decides HOW to respond to the user.

Given the conversation history and retrieved memories, the planner
classifies the intent into one of:

  ANSWER   – reply directly from knowledge
  SEARCH   – perform a web search
  CALC     – run the calculator
  JOBS     – search for job listings
  FILE     – read a file
  MEMORY   – search long-term memory more aggressively

The planner returns a structured plan dict:
{
  "action":  str,          # one of the above
  "query":   str,          # extracted query / expression for the tool
  "reason":  str,          # brief explanation (for logging / debugging)
}
"""

import json
import logging
import re

from llm.ollama_client import simple_prompt

log = logging.getLogger(__name__)

_SYSTEM = """You are a planning agent inside an AI assistant system.

Your job is to analyse the user's latest message and decide which action the assistant should take.

Available actions:
  ANSWER  – the assistant can answer directly from knowledge or the provided context
  SEARCH  – a web search would help answer the question
  CALC    – the message contains a mathematical calculation to evaluate
  JOBS    – the user is asking about job listings or career opportunities
  FILE    – the user wants to read or summarise a file
  MEMORY  – the assistant should search its long-term memory for relevant information

Rules:
- If the message contains arithmetic expressions (e.g. "what is 15 * 7?") → CALC
- If the message asks for current news, facts about recent events, or research → SEARCH
- If the message mentions job search, vacancies, openings, career, hiring → JOBS
- If the message mentions reading a file, uploading a document, parsing a CSV → FILE
- Otherwise → ANSWER

Respond ONLY with a valid JSON object on a single line in this exact format:
{"action": "<ACTION>", "query": "<extracted query or expression>", "reason": "<one sentence>"}

Do NOT include any text outside the JSON object.
"""


async def plan(user_message: str, context: str = "") -> dict:
    """
    Analyse *user_message* (with optional retrieved *context*) and
    return a plan dict with keys: action, query, reason.
    """
    prompt = f"User message: {user_message}"
    if context:
        prompt += f"\n\nContext from memory:\n{context}"

    raw = await simple_prompt(prompt, system=_SYSTEM, temperature=0.1, max_tokens=200)

    return _parse_plan(raw, user_message)


def _parse_plan(raw: str, fallback_query: str) -> dict:
    """Extract JSON from LLM output, with a sensible fallback."""
    # Try to find the first {...} block
    match = re.search(r"\{.*?\}", raw, re.DOTALL)
    if match:
        try:
            plan = json.loads(match.group())
            plan["action"] = plan.get("action", "ANSWER").upper()
            plan.setdefault("query", fallback_query)
            plan.setdefault("reason", "")
            return plan
        except json.JSONDecodeError:
            pass

    log.warning("Planner could not parse JSON from: %r", raw[:120])
    return {"action": "ANSWER", "query": fallback_query, "reason": "fallback – parse error"}
