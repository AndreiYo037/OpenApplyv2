"""Decision engine orchestration."""

from __future__ import annotations

from typing import Dict, List, Optional

from enrichment.contact_scraper import find_contacts
from ingestion.parser import parse_job_text
from ranking.contact_scorer import compute_contact_score
from ranking.job_matcher import compute_job_fit


def evaluate_job(job_text: str, user_profile: Dict[str, object]) -> Dict[str, object]:
    """Evaluate one job using match quality and contact quality."""
    job = parse_job_text(job_text)
    job_fit = compute_job_fit(job, user_profile or {})

    company = str(job.get("company") or "Unknown")
    title = str(job.get("title") or "Unknown")

    try:
        contacts: List[Dict[str, Optional[str]]] = find_contacts(company, title)
    except Exception:
        contacts = []

    contact_score = compute_contact_score(contacts)
    final_score = max(0.0, min(0.6 * job_fit + 0.4 * contact_score, 1.0))

    return {
        "title": title,
        "company": company,
        "job_fit": round(job_fit, 4),
        "contact_score": round(contact_score, 4),
        "final_score": round(final_score, 4),
        "contacts": contacts,
    }
