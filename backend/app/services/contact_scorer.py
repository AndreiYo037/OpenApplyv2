"""Contact scoring service."""

from __future__ import annotations

from typing import Any, Dict, List


def compute_contact_score(contacts: List[Dict[str, Any]]) -> float:
    if not contacts:
        return 0.0

    score = 0.0
    if any(c.get("source") == "job_description" for c in contacts):
        score += 0.5
    if any(c.get("email") for c in contacts):
        score += 0.3
    if any(c.get("linkedin_url") for c in contacts):
        score += 0.2
    if len(contacts) > 1:
        score += 0.2
    return min(score, 1.0)
