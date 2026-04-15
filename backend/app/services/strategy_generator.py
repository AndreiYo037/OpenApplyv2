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
