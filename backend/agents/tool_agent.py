"""
agents/tool_agent.py
====================
Tool Agent – executes the tool chosen by the Planner.

Dispatches to the correct tool module, captures the output, and
returns it as a string that the Response Agent can incorporate.
"""

import logging

from tools.calculator import calculate
from tools.web_search import web_search
from tools.job_search import job_search
from tools.file_reader import read_file

log = logging.getLogger(__name__)


async def execute_tool(action: str, query: str, context: dict | None = None) -> str | None:
    """
    Execute the tool identified by *action* using *query* as input.

    Returns the tool's text output, or None if no tool is needed
    (i.e. action == "ANSWER").

    *context* may carry extra kwargs extracted from the conversation
    (e.g. {"location": "Berlin"} for job search).
    """
    ctx = context or {}
    action = action.upper()
    log.info("ToolAgent executing action=%s query=%r", action, query[:80])

    if action == "CALC":
        return calculate(query)

    if action == "SEARCH":
        return await web_search(query)

    if action == "JOBS":
        location = ctx.get("location")
        return await job_search(query, location=location)

    if action == "FILE":
        return read_file(query)

    if action == "MEMORY":
        # Memory search is handled by the Memory Agent before we get here;
        # return None so the Response Agent uses the injected context.
        return None

    if action == "ANSWER":
        return None

    log.warning("Unknown action '%s' – defaulting to ANSWER.", action)
    return None
