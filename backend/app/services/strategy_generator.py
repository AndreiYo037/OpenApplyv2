"""Outreach strategy generator."""

from __future__ import annotations

from typing import Any, Dict, List

from app.utils.llm import run_openai_json


def _fallback(job: Dict[str, Any], contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    first = contacts[0]["name"] if contacts else "Top contact"
    first_role = contacts[0].get("role", "hiring team") if contacts else "hiring team"
    skills = ", ".join(str(item) for item in job.get("skills", [])[:2]) or "relevant skills"
    company = str(job.get("company", "the company"))
    title = str(job.get("title", "the internship role"))
    fallback_message = (
        f"Hi {first}, I am keen on the {title} opportunity at {company}. "
        f"I recently applied {skills} in a project with measurable outcomes and would love to contribute to your team. "
        f"I was especially interested in your recent Singapore initiatives and how they connect to this role. "
        f"Given your role as {first_role}, could I ask for a brief chat on what the team values most in internship candidates?"
    )
    return {
        "who_to_contact_first": first,
        "outreach_angle": (
            f"Emphasize role fit for {job.get('title', 'the role')} and connect it to a recent "
            f"{job.get('company', 'company')} initiative in Singapore."
        ),
        "message": " ".join(fallback_message.split()[:120]),
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
    job_intent: Dict[str, Any],
) -> Dict[str, Any]:
    system = """Generate personalized outreach strategy JSON.
Return STRICT JSON:
{
  "who_to_contact_first": string,
  "outreach_angle": string,
  "message": string,
  "talking_points": [string]
}
Rules:
- Use Singapore-localized language when applicable.
- Fuse three signal types in the strategy:
  1) company signals (initiatives/products/momentum),
  2) contact signals (role + likely hiring influence),
  3) user signals (skills/projects/experience).
- Keep outreach_angle actionable and concise.
- `message` MUST be <= 120 words and include:
  1) specific project or skill,
  2) company insight (recent activity or product),
  3) alignment with team/problem,
  4) context-aware reference to contact role,
  5) clear ask.
- Tone: confident, concise, non-generic.
"""
    fallback = _fallback(job, contacts)
    top_contact = contacts[0] if contacts else {}
    try:
        output = run_openai_json(
            system,
            str(
                {
                    "cv_structured_data": profile,
                    "user_top_projects": profile.get("projects", []),
                    "job_description": job.get("description", ""),
                    "job_intent": job_intent,
                    "company_intel": company_intel,
                    "contact_role": top_contact.get("role", ""),
                    "contacts": contacts[:10],
                }
            ),
        )
        message = " ".join(str(output.get("message", "")).strip().split()[:120])
        return {
            "who_to_contact_first": str(output.get("who_to_contact_first", fallback["who_to_contact_first"])),
            "outreach_angle": str(output.get("outreach_angle", fallback["outreach_angle"])),
            "message": message or fallback["message"],
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
    """Generate outreach message only when user explicitly requests it."""
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
- Keep all scores in effectiveness_breakdown between 0 and 100.
"""
    fallback_message = (
        f"Hi {contact.get('name', 'there')}, I am an undergraduate in Singapore interested in "
        f"{job.get('title', 'this internship')} at {job.get('company', 'your company')}. "
        f"I recently built {', '.join(cv.get('projects', [])[:1]) or 'a relevant project'} using "
        f"{', '.join(cv.get('skills', [])[:2]) or 'relevant skills'} and would love to contribute to "
        f"your team priorities. I noticed {', '.join(company_intel.get('signals', [])[:1]) or 'your recent initiative'}; "
        f"given your role as {contact.get('role', 'hiring contact')}, could we do a brief 10-minute chat this week?"
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
                    "job_intent": job.get("job_intent", {}),
                    "company_intel": company_intel,
                    "contact_role": contact.get("role", ""),
                    "contact": contact,
                    "user_preferences": user_preferences,
                }
            ),
        )
        message = " ".join(str(output.get("message", "")).split()[:120]).strip() or fallback_message
        points = [str(p).strip() for p in output.get("personalization_points", []) if str(p).strip()]
        effectiveness = output.get("effectiveness_breakdown", {})
        if not isinstance(effectiveness, dict):
            effectiveness = {}
        return {
            "message": message,
            "personalization_points": points[:6],
            "effectiveness_breakdown": effectiveness,
        }
    except Exception:
        return {
            "message": " ".join(fallback_message.split()[:120]),
            "personalization_points": [
                "Specific skill/project alignment",
                "Company signal mention",
                "Role-aware contact context",
                "Low-friction ask",
            ],
            "effectiveness_breakdown": {
                "relevance": 70,
                "targeting": 68,
                "timing": 65,
                "low_friction_ask": 75,
            },
        }
