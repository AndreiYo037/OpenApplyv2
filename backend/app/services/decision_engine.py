"""End-to-end decision engine."""

from __future__ import annotations

from typing import Any, Dict

from app.services.contact_merger import merge_contacts
from app.services.contact_ranker import rank_contacts
from app.services.contact_scorer import compute_contact_score
from app.services.contact_scraper import find_contacts
from app.services.cv_parser import parse_cv_text
from app.services.job_matcher import compute_job_fit
from app.services.job_parser import parse_job_text
from app.services.strategy_generator import generate_strategy


def _decision_label(final_score: float) -> str:
    if final_score > 0.75:
        return "highly_recommended"
    if final_score >= 0.5:
        return "consider"
    return "not_recommended"


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

    strategy = generate_strategy(job, profile, ranked_contacts)

    final_score = max(0.0, min(1.0, 0.6 * job_fit + 0.4 * contact_score))
    decision = _decision_label(final_score)
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
    }
