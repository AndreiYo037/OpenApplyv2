"""Contact quality scoring."""

from __future__ import annotations

from typing import Dict, List, Optional


def _is_priority_role(role: Optional[str]) -> bool:
    if not role:
        return False
    normalized = role.lower()
    return any(keyword in normalized for keyword in ("recruiter", "talent", "hr", "hiring manager"))


def compute_contact_score(contacts: List[Dict[str, Optional[str]]]) -> float:
    """Compute contact discovery quality score between 0 and 1."""
    if not contacts:
        return 0.0

    score = 0.0

    if any(contact.get("linkedin_url") for contact in contacts):
        score += 0.2
    if any(contact.get("email") for contact in contacts):
        score += 0.3
    if any(_is_priority_role(contact.get("role")) for contact in contacts):
        score += 0.3
    if len(contacts) > 1:
        score += 0.2

    return min(score, 1.0)
