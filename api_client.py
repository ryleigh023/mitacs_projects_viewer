"""
Fetches every Mitacs GRI project via the portal's own public JSON API --
no browser automation needed. The endpoint has no observed page-size cap,
so the whole dataset (~3,359 projects as of writing) comes back in two
small HTTP requests instead of hundreds of page loads.
"""

from __future__ import annotations

import json
import logging
import time

import requests

from config import (
    API_URL,
    BACKOFF_BASE_SECONDS,
    BASE_PAYLOAD,
    DISCIPLINE_LOOKUP,
    MAX_RETRIES,
    REQUEST_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)


def _post_with_retries(payload: dict) -> dict:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(API_URL, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # deliberately broad -- any transient failure is worth a retry
            last_error = exc
            wait = BACKOFF_BASE_SECONDS ** attempt
            logger.warning(
                "API request failed (attempt %d/%d): %s -- retrying in %.1fs",
                attempt, MAX_RETRIES, exc, wait,
            )
            time.sleep(wait)
    raise RuntimeError(f"API request failed after {MAX_RETRIES} attempts") from last_error


def _decode_disciplines(raw: str | None) -> str:
    """PreferredBackgroundCollection arrives as a JSON string of numeric
    IDs, e.g. '[88,73,68]'. Map each to its name via DISCIPLINE_LOOKUP."""
    if not raw:
        return "N/A"
    try:
        ids = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return "N/A"
    names = [DISCIPLINE_LOOKUP.get(str(i), f"Unknown ({i})") for i in ids]
    return ", ".join(names) if names else "N/A"


def _to_record(row: dict) -> dict[str, str]:
    professor = row.get("Professor") or {}
    first = (professor.get("FirstName") or "").strip()
    last = (professor.get("LastName") or "").strip()
    professor_name = f"{first} {last}".strip() or "N/A"

    description = (row.get("ProjectDescription") or row.get("projectDescription") or "").strip()
    skills = (row.get("StudentSkills") or "").strip()

    return {
        "Project Title": (row.get("ProjectTitle") or "N/A").strip(),
        "Host University": professor.get("UniversityName") or "N/A",
        "Host Province": professor.get("FacultyProvince") or "N/A",
        "Professor Name": professor_name,
        "Department": "N/A",  # not present anywhere in the portal's data model
        "Project Description": description or "N/A",
        "Required Skills": skills or "N/A",
        "Preferred Disciplines": _decode_disciplines(row.get("PreferredBackgroundCollection")),
    }


def fetch_all_projects() -> list[dict[str, str]]:
    """Ask the API how many projects exist, then fetch all of them in a
    single follow-up request."""
    probe = _post_with_retries({**BASE_PAYLOAD, "offset": 0, "limit": 1})
    total = probe.get("count", 0)
    logger.info("Portal reports %d total projects", total)

    if total == 0:
        return []

    data = _post_with_retries({**BASE_PAYLOAD, "offset": 0, "limit": total})
    rows = data.get("rows", [])
    logger.info("Fetched %d project rows", len(rows))

    return [_to_record(row) for row in rows]
