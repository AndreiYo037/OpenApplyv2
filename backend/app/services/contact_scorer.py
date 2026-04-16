"""Contact scoring service."""

from __future__ import annotations

from typing import Any, Dict, List


def _role_relevance(contact: Dict[str, Any], job_title: str) -> float:
    role = str(contact.get("role", "")).lower()
    title = str(job_title or "").lower()
    if any(token in role for token in ("recruiter", "manager", "lead", "head")):
        return 100.0
    if any(token in role for token in title.split()):
        return 70.0
    return 40.0


def _accessibility(contact: Dict[str, Any]) -> float:
    role_type = str(contact.get("role_type", "unknown"))
    if role_type in {"recruiter", "hiring_manager"}:
        return 85.0
    if role_type == "senior_ic":
        return 70.0
    if role_type == "junior_ic":
        return 95.0
    return 60.0


def _contactability(contact: Dict[str, Any]) -> float:
    score = 20.0
    if contact.get("linkedin_url"):
        score += 40.0
    if contact.get("email"):
        score += 40.0
    if contact.get("source") == "job_description":
        score += 20.0
    return min(score, 100.0)


def _single_contact_score(contact: Dict[str, Any], job_title: str) -> float:
    influence = float(contact.get("influence_level", 40.0) or 40.0)
    role_relevance = _role_relevance(contact, job_title)
    accessibility = _accessibility(contact)
    contactability = _contactability(contact)
    return (
        0.50 * influence
        + 0.20 * role_relevance
        + 0.15 * accessibility
        + 0.15 * contactability
    ) / 100.0


def compute_contact_score(contacts: List[Dict[str, Any]], job_title: str = "") -> float:
    if not contacts:
        return 0.0
    top = contacts[:2]
    scores = [_single_contact_score(contact, job_title) for contact in top]
    if len(scores) == 1:
        return max(0.0, min(scores[0], 1.0))
    blended = 0.7 * scores[0] + 0.3 * scores[1]
    return max(0.0, min(blended, 1.0))
