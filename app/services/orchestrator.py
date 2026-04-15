"""Continuous scoring pipeline orchestration."""

from __future__ import annotations

from typing import Any, Dict, List

from app.services.contact_quality import compute_contact_quality
from app.services.contact_ranker import rank_contacts
from app.services.contact_scraper import find_contacts
from app.services.job_matcher import compute_job_fit
from app.services.parser import parse_job_text
from app.services.score_combiner import combine_final_score
from app.services.strategy_generator import generate_outreach_message


def _normalize_profile(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "skills": [str(s).strip() for s in user_profile.get("skills", []) if str(s).strip()],
        "experience": str(user_profile.get("experience", "")).strip(),
        "education": str(user_profile.get("education", "")).strip(),
        "projects": [str(p).strip() for p in user_profile.get("projects", []) if str(p).strip()],
    }


def _extract_job_intent(job: Dict[str, Any]) -> Dict[str, Any]:
    title = str(job.get("title", "")).lower()
    keywords = [str(item).lower() for item in job.get("keywords", [])]
    blob = " ".join([title, " ".join(keywords)])
    if any(token in blob for token in ("data", "analytics", "machine learning", "ai", "scientist")):
        domain = "data"
    elif any(token in blob for token in ("software", "engineer", "developer", "backend", "frontend", "swe")):
        domain = "swe"
    elif any(token in blob for token in ("business", "operations", "strategy", "growth", "product")):
        domain = "business"
    else:
        domain = "general"

    return {
        "domain": domain,
        "team": str(job.get("title", "")).strip() or "Internship Team",
        "tools": [str(item).strip() for item in job.get("skills", []) if str(item).strip()][:8],
    }


def _missing_core_skill_count(gaps: List[str]) -> int:
    for gap in gaps:
        if str(gap).startswith("missing_hard_requirements:"):
            try:
                return int(str(gap).split(":")[-1])
            except ValueError:
                return 0
    return 0


def _calibrate_cv_score(fit_result: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """Convert matcher output into calibrated CV_MATCH score (0-100)."""
    raw_score = max(0.0, min(float(fit_result.get("job_fit_score", 0.0) or 0.0), 1.0))
    strengths = [str(item).strip() for item in fit_result.get("strengths", []) if str(item).strip()]
    gaps = [str(item).strip() for item in fit_result.get("gaps", []) if str(item).strip()]

    calibrated = 45.0 + 50.0 * raw_score
    job_skills = [str(item).strip() for item in job.get("skills", []) if str(item).strip()]
    if job_skills and not strengths:
        calibrated -= 12.0

    missing_core = _missing_core_skill_count(gaps)
    calibrated -= min(36.0, 12.0 * missing_core)
    cv_score = round(max(0.0, min(calibrated, 100.0)), 2)

    return {
        "score": cv_score,
        "raw_match_score": round(raw_score * 100, 2),
        "strengths": strengths[:8],
        "gaps": gaps[:8],
        "missing_core_skill_count": missing_core,
    }


def _contacts_output(ranked_contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    top = ranked_contacts[:3]
    return [
        {
            "name": str(item.get("name", "")).strip(),
            "role": str(item.get("role", "")).strip(),
            "score": round(float(item.get("score", 0.0) or 0.0), 2),
            "reason": str(item.get("reason", "")).strip(),
        }
        for item in top
    ]


def run_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run end-to-end continuous scoring pipeline for one CV + one job."""
    job_text = str(payload.get("job_text", "")).strip()
    user_profile = _normalize_profile(payload.get("user_profile", {}) if isinstance(payload, dict) else {})

    # 1) Parse CV/user profile (normalize input structure).
    profile = user_profile
    # 2) Compute CV_MATCH.
    # 3) Extract job intent.
    job = parse_job_text(job_text)
    fit_result = compute_job_fit(job, profile)
    cv_match = _calibrate_cv_score(fit_result, job)
    job_intent = _extract_job_intent(job)

    # 4) Discover contacts (TinyFish).
    contacts = find_contacts(company=str(job.get("company", "Unknown")), role=str(job.get("title", "Unknown")))
    # 5-7) Enrich contacts (OpenAI), score each, and rank.
    ranked_contacts = rank_contacts(job_intent=job_intent, contacts=contacts)
    # 8) Aggregate CONTACT_QUALITY from top 2.
    contact_quality = compute_contact_quality(ranked_contacts)
    # 9) Compute FINAL_SCORE.
    final_score = combine_final_score(cv_match["score"], contact_quality)

    # 10) Generate personalized outreach message.
    outreach_message = generate_outreach_message(
        cv_structured=profile,
        top_projects=profile.get("projects", []),
        job=job,
        job_intent=job_intent,
        company_intel={
            "signals": [str(job.get("description", "")).strip()[:220]],
            "company": str(job.get("company", "Unknown")),
        },
        top_contact=ranked_contacts[0] if ranked_contacts else {},
    )

    top_contacts = _contacts_output(ranked_contacts)
    top_components = {
        item["name"]: ranked_contacts[idx].get("contact_components", {})
        for idx, item in enumerate(top_contacts)
        if idx < len(ranked_contacts)
    }

    return {
        "final_score": int(round(final_score)),
        "cv_score": round(cv_match["score"], 2),
        "contact_quality": round(contact_quality, 2),
        "contacts": top_contacts,
        "message": outreach_message,
        "score_breakdown": {
            "cv_match": cv_match,
            "contact_components": top_components,
        },
    }
