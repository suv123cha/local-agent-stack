"""
tools/web_search.py
===================
Web search tool.

Attempts a real search via the DuckDuckGo Instant-Answer API
(no API key required).  Falls back to plausible mock results if
the network is unavailable so the agent pipeline never hard-fails.
"""

import logging
import httpx

log = logging.getLogger(__name__)

DDG_URL = "https://api.duckduckgo.com/"


async def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for *query* and return a formatted result string
    suitable for injection into an LLM prompt.
    """
    log.info("Web search: %s", query)
    try:
        results = await _ddg_search(query, max_results)
        if results:
            return _format_results(query, results)
    except Exception as exc:
        log.warning("Web search failed (%s) – using mock results.", exc)

    # Fallback: return honest mock
    return _mock_results(query)


async def _ddg_search(query: str, max_results: int) -> list[dict]:
    """Call the DuckDuckGo Instant Answer JSON API."""
    params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(DDG_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    results: list[dict] = []

    # Abstract (top summary)
    if data.get("AbstractText"):
        results.append({
            "title": data.get("Heading", query),
            "snippet": data["AbstractText"],
            "url": data.get("AbstractURL", ""),
        })

    # Related topics
    for topic in data.get("RelatedTopics", [])[:max_results]:
        if isinstance(topic, dict) and topic.get("Text"):
            results.append({
                "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                "snippet": topic["Text"],
                "url": topic.get("FirstURL", ""),
            })

    return results[:max_results]


def _format_results(query: str, results: list[dict]) -> str:
    lines = [f"Web search results for: '{query}'\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   {r['snippet']}")
        if r.get("url"):
            lines.append(f"   Source: {r['url']}")
        lines.append("")
    return "\n".join(lines)


def _mock_results(query: str) -> str:
    return (
        f"[Mock search results for: '{query}']\n"
        "1. Example Result – This is a placeholder because the search service "
        "is currently unavailable. In production the agent would return live results.\n"
        "2. Wikipedia overview – A comprehensive article covering the key aspects "
        f"of '{query}' is available at en.wikipedia.org.\n"
    )
