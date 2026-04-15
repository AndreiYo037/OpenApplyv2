"""Outreach strategy generator."""

from __future__ import annotations

from typing import Any, Dict, List

from app.utils.llm import run_openai_json


def _fallback(job: Dict[str, Any], contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    first = contacts[0]["name"] if contacts else "Top contact"
    return {
        "who_to_contact_first": first,
        "outreach_angle": (
            f"Emphasize role fit for {job.get('title', 'the role')} and connect it to a recent "
            f"{job.get('company', 'company')} initiative in Singapore."
        ),
        "talking_points": [
            "Reference one direct skill match from the role.",
            "Share one measurable project outcome tied to company priorities.",
            "Ask a specific question showing context on the team or function.",
        ],
    }


def generate_strategy(
    job: Dict[str, Any],
    profile: Dict[str, Any],
    contacts: List[Dict[str, Any]],
    company_intel: Dict[str, Any],
) -> Dict[str, Any]:
    system = """Generate personalized outreach strategy JSON.
Return STRICT JSON:
{
  "who_to_contact_first": string,
  "outreach_angle": string,
  "talking_points": [string]
}
Rules:
- Use Singapore-localized language when applicable.
- Fuse three signal types in the strategy:
  1) company signals (initiatives/products/momentum),
  2) contact signals (role + likely hiring influence),
  3) user signals (skills/projects/experience).
- Keep outreach_angle actionable and concise.
"""
    fallback = _fallback(job, contacts)
    try:
        output = run_openai_json(
            system,
            str({"job": job, "profile": profile, "contacts": contacts[:5], "company_intel": company_intel}),
        )
        return {
            "who_to_contact_first": str(output.get("who_to_contact_first", fallback["who_to_contact_first"])),
            "outreach_angle": str(output.get("outreach_angle", fallback["outreach_angle"])),
            "talking_points": output.get("talking_points", fallback["talking_points"]),
        }
    except Exception:
        return fallback


def generate_on_demand_message(
    *,
    contact_id: str,
    cv: Dict[str, Any],
    job: Dict[str, Any],
    company_intel: Dict[str, Any],
    contact: Dict[str, Any],
    user_preferences: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate outreach message only when explicitly requested by user."""
    system = """You generate high-conversion outreach messages for internship candidates.
Return STRICT JSON:
{
  "message": string,
  "personalization_points": [string],
  "effectiveness_breakdown": {
    "relevance": number,
    "targeting": number,
    "timing": number,
    "low_friction_ask": number
  }
}
Rules:
- Max 120 words.
- Must include:
  1) specific project/skill,
  2) company insight (recent activity/product),
  3) alignment with team/problem,
  4) context-aware reference to contact role,
  5) clear low-friction ask.
- Tone: confident, concise, non-generic.
- Keep all effectiveness scores between 0 and 100.
"""
    fallback_message = (
        f"Hi {contact.get('name', 'there')}, I am interested in {job.get('title', 'this internship')} at "
        f"{job.get('company', 'your company')}. I recently applied "
        f"{', '.join(cv.get('skills', [])[:2]) or 'relevant skills'} in "
        f"{', '.join(cv.get('projects', [])[:1]) or 'a relevant project'} and would love to contribute to your team. "
        f"I noticed {', '.join(company_intel.get('signals', [])[:1]) or 'your recent initiative'}. "
        f"Given your role as {contact.get('role', 'hiring contact')}, could we do a brief 10-minute chat this week?"
    )

    try:
        output = run_openai_json(
            system,
            str(
                {
                    "contact_id": contact_id,
                    "cv_structured_data": cv,
                    "user_top_projects": cv.get("projects", []),
                    "job_description": job.get("description", ""),
                    "job": job,
                    "company_intel": company_intel,
                    "contact": contact,
                    "contact_role": contact.get("role", ""),
                    "user_preferences": user_preferences,
                }
            ),
        )
        message = " ".join(str(output.get("message", "")).split()[:120]).strip() or fallback_message
        personalization_points = [
            str(point).strip()
            for point in output.get("personalization_points", [])
            if str(point).strip()
        ]
        effectiveness = output.get("effectiveness_breakdown", {})
        if not isinstance(effectiveness, dict):
            effectiveness = {}
        return {
            "message": message,
            "personalization_points": personalization_points[:6],
            "effectiveness_breakdown": effectiveness,
        }
    except Exception:
        return {
            "message": " ".join(fallback_message.split()[:120]),
            "personalization_points": [
                "Specific skill and project relevance",
                "Company initiative alignment",
                "Role-aware contact targeting",
                "Clear low-friction ask",
            ],
            "effectiveness_breakdown": {
                "relevance": 70,
                "targeting": 68,
                "timing": 65,
                "low_friction_ask": 74,
            },
        }
