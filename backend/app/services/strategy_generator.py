"""Outreach strategy generator."""

from __future__ import annotations

from typing import Any, Dict, List

from app.utils.llm import run_openai_json


def _fallback(job: Dict[str, Any], contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    first = contacts[0]["name"] if contacts else "Top contact"
    return {
        "who_to_contact_first": first,
        "outreach_angle": f"Emphasize strong alignment to {job.get('title', 'the role')} and immediate impact.",
        "talking_points": [
            "Reference one direct skill match from the role.",
            "Share one measurable project outcome.",
            "Ask a specific question about team priorities.",
        ],
    }


def generate_strategy(job: Dict[str, Any], profile: Dict[str, Any], contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    system = """Generate personalized outreach strategy JSON.
Return STRICT JSON:
{
  "who_to_contact_first": string,
  "outreach_angle": string,
  "talking_points": [string]
}
"""
    fallback = _fallback(job, contacts)
    try:
        output = run_openai_json(system, str({"job": job, "profile": profile, "contacts": contacts[:5]}))
        return {
            "who_to_contact_first": str(output.get("who_to_contact_first", fallback["who_to_contact_first"])),
            "outreach_angle": str(output.get("outreach_angle", fallback["outreach_angle"])),
            "talking_points": output.get("talking_points", fallback["talking_points"]),
        }
    except Exception:
        return fallback
