"""
memory/profile_memory.py
========================
Structured user-profile memory backed by MongoDB.

Each user/session gets one document in the `profiles` collection:
{
  "_id":        <session_id>,
  "name":       str | None,
  "location":   str | None,
  "skills":     [str, ...],
  "preferences":{str: str, ...},
  "facts":      [str, ...]      # free-form extracted facts
}

The document is upserted so partial updates are safe.
"""

import logging
import os

from pymongo import MongoClient, ReturnDocument

log = logging.getLogger(__name__)

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "agent_system"
COLLECTION = "profiles"


def _col():
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    return client[DB_NAME][COLLECTION]


def get_profile(session_id: str) -> dict:
    """Return the stored profile for *session_id*, or an empty skeleton."""
    col = _col()
    doc = col.find_one({"_id": session_id})
    if doc:
        doc.pop("_id", None)
        return doc
    return {"name": None, "location": None, "skills": [], "preferences": {}, "facts": []}


def update_profile(session_id: str, updates: dict) -> dict:
    """
    Merge *updates* into the existing profile document.

    Handles two special array fields:
      - skills   → $addToSet (de-duplicated)
      - facts    → $addToSet

    All other top-level fields use $set.
    """
    col = _col()

    set_ops = {}
    add_to_set_ops = {}

    for key, value in updates.items():
        if key in ("skills", "facts") and isinstance(value, list):
            for item in value:
                add_to_set_ops.setdefault(key, {"$each": []})["$each"].append(item)
        elif key == "preferences" and isinstance(value, dict):
            for pref_key, pref_val in value.items():
                set_ops[f"preferences.{pref_key}"] = pref_val
        else:
            set_ops[key] = value

    update_doc: dict = {}
    if set_ops:
        update_doc["$set"] = set_ops
    if add_to_set_ops:
        update_doc["$addToSet"] = add_to_set_ops

    if not update_doc:
        return get_profile(session_id)

    doc = col.find_one_and_update(
        {"_id": session_id},
        update_doc,
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    doc.pop("_id", None)
    log.debug("Updated profile for session %s: %s", session_id, updates)
    return doc


def profile_summary(session_id: str) -> str:
    """Return a human-readable summary of the user profile (for prompt injection)."""
    p = get_profile(session_id)
    lines = []
    if p.get("name"):
        lines.append(f"User name: {p['name']}")
    if p.get("location"):
        lines.append(f"User location: {p['location']}")
    if p.get("skills"):
        lines.append(f"User skills: {', '.join(p['skills'])}")
    if p.get("preferences"):
        for k, v in p["preferences"].items():
            lines.append(f"User preference – {k}: {v}")
    if p.get("facts"):
        lines.append("Known facts about user:")
        lines.extend(f"  • {f}" for f in p["facts"][-10:])
    return "\n".join(lines) if lines else "No profile data available yet."
