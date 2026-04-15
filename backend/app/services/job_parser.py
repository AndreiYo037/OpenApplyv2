"""Job parser service."""

from __future__ import annotations

from typing import Any, Dict, List

from app.utils.llm import run_openai_json


SYSTEM_PROMPT = """You are an expert job description parser.

Extract structured data AND any recruiter contact details explicitly mentioned.

OUTPUT STRICT JSON:
{
  "title": string,
  "company": string,
  "hard_requirements": [string],
  "skills": [string],
  "keywords": [string],
  "description": string,
  "recruiter_contacts": [
    {
      "name": string,
      "role": string,
      "email": string | null
    }
  ]
}

RULES:
- Extract recruiter names if present (e.g. "Contact John Tan")
- Extract emails ONLY if explicitly written
- Do NOT hallucinate contacts
- If none found, return empty list
- Normalize skills
"""


def _fallback(job_text: str) -> Dict[str, Any]:
    return {
        "title": "Unknown",
        "company": "Unknown",
        "hard_requirements": [],
        "skills": [],
        "keywords": [],
        "description": (job_text or "").strip(),
        "recruiter_contacts": [],
    }


def _normalize_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    return [str(v).strip() for v in values if str(v).strip()]


def parse_job_text(job_text: str) -> Dict[str, Any]:
    safe = (job_text or "").strip()
    if not safe:
        return _fallback("")

    try:
        parsed = run_openai_json(SYSTEM_PROMPT, safe)
    except Exception:
        return _fallback(safe)

    contacts: List[Dict[str, Any]] = []
    for item in parsed.get("recruiter_contacts", []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        contacts.append(
            {
                "name": name,
                "role": str(item.get("role", "Recruiter")).strip() or "Recruiter",
                "email": item.get("email") if item.get("email") else None,
            }
        )

    return {
        "title": str(parsed.get("title", "Unknown")).strip() or "Unknown",
        "company": str(parsed.get("company", "Unknown")).strip() or "Unknown",
        "hard_requirements": _normalize_list(parsed.get("hard_requirements", [])),
        "skills": _normalize_list(parsed.get("skills", [])),
        "keywords": _normalize_list(parsed.get("keywords", [])),
        "description": str(parsed.get("description", safe)),
        "recruiter_contacts": contacts,
    }
