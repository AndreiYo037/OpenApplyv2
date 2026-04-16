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
from app.services.strategy_generator import generate_strategy

MIN_ACTIONABLE_JOB_FIT = 0.12
MIN_RELIABLE_CONTACT_CONFIDENCE = 0.55


def _decision_label(final_score: float) -> str:
    if final_score > 0.75:
        return "highly_recommended"
    if final_score >= 0.5:
        return "consider"
    return "not_recommended"


def _is_reliable_contact(contact: Dict[str, Any]) -> bool:
    has_reach_channel = bool(contact.get("linkedin_url") or contact.get("email"))
    confidence = float(contact.get("confidence", 0.0) or 0.0)
    return has_reach_channel and confidence >= MIN_RELIABLE_CONTACT_CONFIDENCE


def _classify_contact(contact: Dict[str, Any]) -> Dict[str, Any]:
    role = str(contact.get("role", "")).lower()
    role_type = "unknown"
    influence = 40.0
    if any(token in role for token in ("recruiter", "talent", "hr", "human resources")):
        role_type, influence = "recruiter", 98.0
    elif any(token in role for token in ("manager", "lead", "head")):
        role_type, influence = "hiring_manager", 90.0
    elif any(token in role for token in ("senior", "staff", "principal")):
        role_type, influence = "senior_ic", 68.0
    elif any(token in role for token in ("intern", "junior", "associate")):
        role_type, influence = "junior_ic", 30.0
    else:
        role_type, influence = "unknown", 40.0
    raw = "||".join(
        [
            str(contact.get("name", "")).strip().lower(),
            str(contact.get("role", "")).strip().lower(),
            str(contact.get("linkedin_url", "")).strip().lower(),
            str(contact.get("email", "")).strip().lower(),
        ]
    )
    return {
        **contact,
        "id": hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12],
        "role_type": role_type,
        "influence_level": influence,
    }


def evaluate_job(job_text: str, cv_text: str) -> Dict[str, Any]:
    job = parse_job_text(job_text)
    profile = parse_cv_text(cv_text)

    fit_result = compute_job_fit(job, profile)
    job_fit = float(fit_result.get("job_fit_score", 0.0) or 0.0)

    company = str(job.get("company", "Unknown")) or "Unknown"
    title = str(job.get("title", "Unknown")) or "Unknown"

    scraped_contacts = find_contacts(company, title)
    contacts = merge_contacts(job.get("recruiter_contacts", []), scraped_contacts, company, title)
    ranked_contacts = rank_contacts(job, contacts)
    ranked_contacts = [_classify_contact(contact) for contact in ranked_contacts]
    contact_score = compute_contact_score(ranked_contacts, title)
    reliable_contacts = [item for item in ranked_contacts if _is_reliable_contact(item)]
    company_intel = get_company_intel(company, title, job)

    strategy = generate_strategy(job, profile, ranked_contacts, company_intel)

    final_score = max(0.0, min(1.0, 0.6 * job_fit + 0.4 * contact_score))
    decision = _decision_label(final_score)
    actionable = job_fit >= MIN_ACTIONABLE_JOB_FIT and bool(reliable_contacts)

    action_plan = (
        f"Contact {strategy.get('who_to_contact_first', 'top contact')} first. "
        f"{strategy.get('outreach_angle', 'Use a role-aligned outreach angle.')}"
    )

    return {
        "title": title,
        "company": company,
        "job_fit": round(job_fit, 4),
        "contact_score": round(contact_score, 4),
        "final_score": round(final_score, 4),
        "contacts": ranked_contacts[:5],
        "decision": decision,
        "action_plan": action_plan,
        "actionable": actionable,
        "discard_reason": None,
        "company_signals": company_intel.get("signals", []),
        "job_summary": str(company_intel.get("job_summary", "")).strip(),
        "required_skills": company_intel.get("required_skills", []),
    }
