"""End-to-end decision engine."""

from __future__ import annotations

import hashlib
from typing import Any, Dict

from app.services.company_intel import get_company_intel
from app.services.contact_merger import merge_contacts
from app.services.contact_ranker import rank_contacts
from app.services.contact_scorer import compute_contact_score
from app.services.contact_scraper import find_contacts
from app.services.cv_parser import parse_cv_text
from app.services.job_matcher import compute_job_fit
from app.services.job_parser import parse_job_text


def _build_job_intent(job: Dict[str, Any]) -> Dict[str, Any]:
    title = str(job.get("title", "")).lower()
    keywords = " ".join(str(item).lower() for item in job.get("keywords", []))
    blob = f"{title} {keywords}"
    if any(token in blob for token in ("data", "analytics", "machine learning", "ml", "ai")):
        domain = "data"
    elif any(token in blob for token in ("software", "engineer", "developer", "backend", "frontend")):
        domain = "swe"
    elif any(token in blob for token in ("business", "operations", "strategy", "growth", "product")):
        domain = "business"
    else:
        domain = "general"
    return {
        "domain": domain,
        "team": str(job.get("title", "Internship Team")).strip() or "Internship Team",
        "tools": [str(item).strip() for item in job.get("skills", []) if str(item).strip()][:8],
    }


def _contact_id(contact: Dict[str, Any]) -> str:
    raw = "||".join(
        [
            str(contact.get("name", "")).strip().lower(),
            str(contact.get("role", "")).strip().lower(),
            str(contact.get("linkedin_url", "")).strip().lower(),
            str(contact.get("email", "")).strip().lower(),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def _normalize_contacts(contacts: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    normalized: list[Dict[str, Any]] = []
    for item in contacts:
        confidence = float(item.get("confidence", 0.0) or 0.0)
        score = float(item.get("score", confidence * 100.0) or 0.0)
        normalized.append(
            {
                **item,
                "id": _contact_id(item),
                "score": round(max(0.0, min(score, 100.0)), 2),
                "confidence": round(max(0.0, min(confidence, 1.0)), 4),
            }
        )
    return normalized


def evaluate_job(job_text: str, cv_text: str) -> Dict[str, Any]:
    job = parse_job_text(job_text)
    profile = parse_cv_text(cv_text)

    fit_result = compute_job_fit(job, profile)
    job_fit = float(fit_result.get("job_fit_score", 0.0) or 0.0)

    company = str(job.get("company", "Unknown")) or "Unknown"
    title = str(job.get("title", "Unknown")) or "Unknown"

    scraped_contacts = find_contacts(company, title)
    contacts = merge_contacts(job.get("recruiter_contacts", []), scraped_contacts, company, title)
    contact_score = compute_contact_score(contacts)
    ranked_contacts = rank_contacts(job, contacts)
    ranked_contacts = _normalize_contacts(ranked_contacts)[:10]
    company_intel = get_company_intel(company, title)
    _ = _build_job_intent(job)

    final_score = max(0.0, min(100.0, (0.6 * job_fit + 0.4 * contact_score) * 100.0))
    cv_score = max(0.0, min(100.0, job_fit * 100.0))
    contact_quality = max(0.0, min(100.0, contact_score * 100.0))

    return {
        "title": title,
        "company": company,
        "cv_score": round(cv_score, 2),
        "contact_quality": round(contact_quality, 2),
        "final_score": round(final_score, 2),
        "contacts": ranked_contacts,
        "company_signals": company_intel.get("signals", []),
    }
