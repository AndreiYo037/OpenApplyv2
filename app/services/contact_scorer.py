"""Per-contact scoring model for continuous decision engine."""

from __future__ import annotations

import re
from typing import Any, Dict


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _hiring_authority(role: str) -> float:
    value = _normalize_text(role)
    if "university recruiter" in value:
        return 100.0
    if "recruiter" in value and any(token in value for token in ("technical", "tech", "engineering", "talent")):
        return 95.0
    if "hiring manager" in value:
        return 90.0
    if "recruiter" in value:
        return 100.0
    if any(token in value for token in ("manager", "head of", "lead")):
        return 90.0
    if any(token in value for token in ("senior engineer", "staff engineer", "principal", "senior analyst")):
        return 60.0
    return 20.0


def _role_relevance(job_domain: str, role: str, domain_match: str) -> float:
    if domain_match == "exact":
        return 100.0
    if domain_match == "related":
        return 70.0
    if domain_match == "weak":
        return 30.0

    role_text = _normalize_text(role)
    domain = _normalize_text(job_domain)
    if domain and domain in role_text:
        return 100.0

    related_map = {
        "data": ("analytics", "machine learning", "ai", "scientist"),
        "swe": ("software", "engineer", "developer", "backend", "frontend"),
        "business": ("strategy", "operations", "growth", "product", "bizdev"),
    }
    if any(token in role_text for token in related_map.get(domain, ())):
        return 70.0
    return 30.0


def _accessibility(role: str, seniority_bucket: str) -> float:
    bucket = _normalize_text(seniority_bucket)
    if bucket in ("mid", "mid_level", "mid-level"):
        return 100.0
    if bucket == "junior":
        return 70.0
    if bucket in ("senior leadership", "senior_leadership"):
        return 20.0
    if bucket in ("c-level", "c_level", "c suite", "c-suite"):
        return 0.0

    role_text = _normalize_text(role)
    if re.search(r"\b(ceo|cto|cfo|coo|chief|founder)\b", role_text):
        return 0.0
    if re.search(r"\b(vp|vice president|director|head)\b", role_text):
        return 20.0
    if re.search(r"\b(intern|junior|associate)\b", role_text):
        return 70.0
    return 100.0


def _contactability(contact: Dict[str, Any], hiring_activity: bool, singapore_based: bool) -> float:
    role_text = _normalize_text(contact.get("role"))
    snippet = " ".join(
        [
            _normalize_text(contact.get("search_hint")),
            _normalize_text(contact.get("source")),
            _normalize_text(contact.get("reason")),
        ]
    )
    value = 0.0
    if contact.get("linkedin_url"):
        value += 30.0
    if any(token in role_text for token in ("recruiter", "talent", "hiring manager", "hr")):
        value += 30.0
    if hiring_activity or any(token in snippet for token in ("hiring", "talent", "recruiting", "internship")):
        value += 20.0
    if singapore_based or "singapore" in snippet or "sg.linkedin.com" in _normalize_text(contact.get("linkedin_url")):
        value += 20.0
    return min(value, 100.0)


def score_contact(contact: Dict[str, Any], job_intent: Dict[str, Any], enrichment: Dict[str, Any]) -> Dict[str, Any]:
    """Return per-contact score and component breakdown (0-100)."""
    role = str(contact.get("role", ""))
    domain = str(job_intent.get("domain", ""))
    domain_match = _normalize_text(enrichment.get("domain_match"))
    seniority_bucket = _normalize_text(enrichment.get("seniority_bucket"))
    hiring_activity = bool(enrichment.get("hiring_activity"))
    singapore_based = bool(enrichment.get("singapore_based"))

    components = {
        "hiring_authority": _hiring_authority(role),
        "role_relevance": _role_relevance(domain, role, domain_match),
        "accessibility": _accessibility(role, seniority_bucket),
        "contactability": _contactability(contact, hiring_activity=hiring_activity, singapore_based=singapore_based),
    }

    score = (
        0.50 * components["hiring_authority"]
        + 0.20 * components["role_relevance"]
        + 0.15 * components["accessibility"]
        + 0.15 * components["contactability"]
    )

    reason = (
        f"Authority {int(components['hiring_authority'])}, "
        f"role relevance {int(components['role_relevance'])}, "
        f"accessibility {int(components['accessibility'])}, "
        f"contactability {int(components['contactability'])}."
    )
    return {
        "score": round(max(0.0, min(score, 100.0)), 2),
        "components": components,
        "reason": reason,
    }
