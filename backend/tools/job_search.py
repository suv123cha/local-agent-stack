"""
tools/job_search.py
===================
Job search tool.

Returns mock job listings enriched with the user's query terms.
In a production system this would integrate with a real jobs API
(e.g. Adzuna, LinkedIn, Greenhouse, etc.).
"""

import logging
import random

log = logging.getLogger(__name__)

_MOCK_COMPANIES = [
    "Acme Tech", "NovaSoft", "DataDriven GmbH", "CloudPeak AG",
    "InnovateCo", "ByteWorks", "Sigma Systems", "Apex Digital",
]

_MOCK_LOCATIONS = ["Berlin", "Munich", "Remote", "Hamburg", "Frankfurt", "London"]

_SALARY_RANGES = [
    "€60,000 – €80,000", "€80,000 – €100,000", "€90,000 – €120,000",
    "€70,000 – €95,000", "Competitive",
]


def _generate_listing(index: int, role: str, location: str | None) -> dict:
    company = random.choice(_MOCK_COMPANIES)
    loc = location or random.choice(_MOCK_LOCATIONS)
    salary = random.choice(_SALARY_RANGES)
    return {
        "id": f"JOB-{1000 + index}",
        "title": f"{role} Engineer" if "engineer" not in role.lower() else role,
        "company": company,
        "location": loc,
        "salary": salary,
        "type": random.choice(["Full-time", "Contract", "Part-time"]),
        "posted": f"{random.randint(1, 14)} days ago",
        "description": (
            f"{company} is looking for an experienced {role} professional to join "
            f"our {random.choice(['growing', 'dynamic', 'innovative'])} team in {loc}. "
            f"You will work on exciting projects and collaborate with talented engineers."
        ),
    }


async def job_search(query: str, location: str | None = None, limit: int = 5) -> str:
    """
    Search for jobs matching *query* (optionally filtered by *location*).
    Returns a formatted string of listings.
    """
    log.info("Job search: query=%s location=%s", query, location)

    # Extract a role keyword from the query
    role = query.strip().title()

    listings = [_generate_listing(i, role, location) for i in range(limit)]

    lines = [f"Job search results for '{query}'" + (f" in {location}" if location else "") + ":\n"]
    for job in listings:
        lines.append(f"🏢  {job['title']} at {job['company']}")
        lines.append(f"    📍 {job['location']}  |  💰 {job['salary']}  |  ⏰ {job['type']}")
        lines.append(f"    Posted: {job['posted']}")
        lines.append(f"    {job['description']}")
        lines.append("")

    lines.append("(Results are illustrative – integrate a live API for production use.)")
    return "\n".join(lines)
