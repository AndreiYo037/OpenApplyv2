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
    cv: Dict[str, Any],
    job: Dict[str, Any],
    company_intel: Dict[str, Any],
    contact: Dict[str, Any],
    user_preferences: Dict[str, Any],
) -> Dict[str, Any]:
    role_type = str(contact.get("role_type", "unknown"))
    role = str(contact.get("role", "contact"))
    name = str(contact.get("name", "there"))
    project = str(cv.get("project", "") or cv.get("highlight_project", "") or "a recent project")
    if not project and isinstance(cv.get("projects"), list) and cv.get("projects"):
        project = str(cv.get("projects")[0])
    signals = company_intel.get("signals", []) if isinstance(company_intel.get("signals"), list) else []
    company_signal = str(signals[0]) if signals else f"{job.get('company', 'the company')} growth in Singapore"

    strategy_by_role = {
        "recruiter": "Ask for application positioning advice and internship fit.",
        "hiring_manager": "Connect your project directly to the team's technical problem space.",
        "senior_ic": "Request practical insight into team workflows and learning path.",
        "junior_ic": "Ask about their internship journey and concrete tips.",
        "unknown": "Use a concise networking ask tied to internship relevance.",
    }

    system = """Write one personalized outreach message in STRICT JSON.
Return:
{
  "message": string,
  "personalization_points": [string],
  "effectiveness_breakdown": {"relevance": number, "clarity": number, "role_alignment": number}
}
Rules:
- Student is sender, contact is recipient.
- Do not describe recipient's skills or assume their background beyond role/title.
- Must include one student project reference and one role-aware ask.
- Keep to <=120 words.
- No generic fluff.
"""
    user = str(
        {
            "job": job,
            "contact": contact,
            "role_strategy": strategy_by_role.get(role_type, strategy_by_role["unknown"]),
            "company_signal": company_signal,
            "student_project": project,
            "preferences": user_preferences,
        }
    )
    try:
        output = run_openai_json(system, user)
        message = str(output.get("message", "")).strip()
        if message:
            return {
                "message": message,
                "personalization_points": output.get("personalization_points", []),
                "effectiveness_breakdown": output.get("effectiveness_breakdown", {}),
            }
    except Exception:
        pass

    fallback_message = (
        f"Hi {name}, I am applying for the {job.get('title', 'internship')} role at {job.get('company', 'your company')}. "
        f"I recently built {project} and want to align that experience with your team's priorities. "
    )
    if role_type == "recruiter":
        fallback_message += "Could you share advice on how to position my profile for this internship?"
    elif role_type == "hiring_manager":
        fallback_message += f"Could I get your view on whether this project aligns with {role} needs?"
    elif role_type == "senior_ic":
        fallback_message += "Could I ask for a short chat on the team workflow and skills to strengthen?"
    elif role_type == "junior_ic":
        fallback_message += "Could you share how you approached the application process and what helped most?"
    else:
        fallback_message += "Could you share one practical suggestion on how to approach this role?"

    return {
        "message": fallback_message[:1200],
        "personalization_points": [
            f"Company signal: {company_signal}",
            f"Role-aware strategy for {role_type}",
            f"Project reference: {project}",
        ],
        "effectiveness_breakdown": {"relevance": 78, "clarity": 80, "role_alignment": 80},
    }
