"""CV parser service."""

from __future__ import annotations

from typing import Any, Dict, List

from app.utils.llm import run_openai_json


SYSTEM_PROMPT = """You parse CV text into structured JSON.

Return STRICT JSON:
{
  "skills": [string],
  "experience_summary": string,
  "projects": [string],
  "education": [string],
  "roles": [string],
  "seniority_level": string
}
"""


def _fallback(cv_text: str) -> Dict[str, Any]:
    return {
        "skills": [],
        "experience_summary": (cv_text or "").strip()[:500],
        "projects": [],
        "education": [],
        "roles": [],
        "seniority_level": "Unknown",
    }


def _normalize(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    return [str(v).strip() for v in values if str(v).strip()]


def parse_cv_text(cv_text: str) -> Dict[str, Any]:
    safe = (cv_text or "").strip()
    if not safe:
        return _fallback("")

    try:
        parsed = run_openai_json(SYSTEM_PROMPT, safe)
    except Exception:
        return _fallback(safe)

    return {
        "skills": _normalize(parsed.get("skills", [])),
        "experience_summary": str(parsed.get("experience_summary", "")),
        "projects": _normalize(parsed.get("projects", [])),
        "education": _normalize(parsed.get("education", [])),
        "roles": _normalize(parsed.get("roles", [])),
        "seniority_level": str(parsed.get("seniority_level", "Unknown")) or "Unknown",
    }
