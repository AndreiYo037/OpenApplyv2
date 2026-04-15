"""Decision engine orchestration service."""

from __future__ import annotations

from typing import Any, Dict, List

from app.services.contact_ranker import rank_contacts
from app.services.contact_scorer import compute_contact_score
from app.services.contact_scraper import find_contacts
from app.services.contact_targets import generate_contact_targets
from app.services.job_matcher import compute_job_fit
from app.services.parser import parse_job_text
from app.services.strategy_generator import generate_strategy


def _build_decision(final_score: float) -> str:
    if final_score >= 0.75:
        return "Strong Apply"
    if final_score >= 0.5:
        return "Apply with Targeted Outreach"
    if final_score >= 0.3:
        return "Borderline - Improve Positioning First"
    return "Low Priority"


def _build_action_plan(strategy: Dict[str, Any], contacts: List[Dict[str, Any]]) -> str:
    who = str(strategy.get("who_to_message_first", "Top contact")).strip() or "Top contact"
    angle = str(strategy.get("angle", "Use a role-specific value proposition.")).strip()
    points = strategy.get("key_talking_points", [])
    if isinstance(points, list):
        key_points = "; ".join(str(p).strip() for p in points[:3] if str(p).strip())
    else:
        key_points = ""

    contact_count = len(contacts)
    parts = [
        f"Message {who} first.",
        angle,
        f"Use these talking points: {key_points or 'Highlight role match and measurable outcomes.'}",
        f"Prioritize outreach to top {contact_count} contact(s).",
    ]
    return " ".join(parts)


def evaluate_job(job_text: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate one job through parser, matching, contact, and strategy pipeline."""
    safe_profile = user_profile if isinstance(user_profile, dict) else {}

    # 1. Parse job text.
    job = parse_job_text(job_text)

    # 2. Compute job fit.
    fit_result = compute_job_fit(job, safe_profile)
    job_fit = float(fit_result.get("job_fit_score", 0.0) or 0.0)

    # 3. Generate contact target buckets.
    contact_targets = generate_contact_targets(job)

    # 4. Discover contacts via TinyFish service.
    company = str(job.get("company", "Unknown"))
    role = str(job.get("title", "Unknown"))
    contacts = find_contacts(company=company, role=role)

    # 5. Rank contacts with relevance score.
    ranked_contacts = rank_contacts(job=job, contacts=contacts)

    # 6. Compute contact readiness score.
    contact_score = compute_contact_score(ranked_contacts)

    # 7. Generate outreach strategy.
    strategy = generate_strategy(job=job, user_profile=safe_profile, contacts=ranked_contacts)

    final_score = max(0.0, min(1.0, 0.6 * job_fit + 0.4 * contact_score))
    decision = _build_decision(final_score)
    action_plan = _build_action_plan(strategy, ranked_contacts)

    return {
        "title": str(job.get("title", "Unknown")),
        "company": company if company else "Unknown",
        "job_fit": round(job_fit, 4),
        "contact_score": round(contact_score, 4),
        "final_score": round(final_score, 4),
        "contacts": ranked_contacts,
        "decision": decision,
        "action_plan": action_plan,
        "job_fit_details": fit_result,
        "contact_targets": contact_targets,
        "strategy": strategy,
    }
