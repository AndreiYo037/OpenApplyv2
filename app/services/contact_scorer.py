"""Contact quality scoring service."""

from __future__ import annotations

from typing import Dict, List


def _is_recruiter_or_manager(role: str) -> bool:
    normalized = (role or "").lower()
    return any(
        token in normalized
        for token in ("recruiter", "talent", "hr", "hiring manager", "manager", "lead")
    )


def compute_contact_score(contacts: List[Dict[str, object]]) -> float:
    """Compute contact score based on outreach readiness signals."""
    if not contacts:
        return 0.0

    score = 0.0

    if any(contact.get("linkedin_url") for contact in contacts):
        score += 0.2
    if any(contact.get("email") for contact in contacts):
        score += 0.3
    if any(_is_recruiter_or_manager(str(contact.get("role", ""))) for contact in contacts):
        score += 0.3
    if len(contacts) > 1:
        score += 0.2

    return min(score, 1.0)
