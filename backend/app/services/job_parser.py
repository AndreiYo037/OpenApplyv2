"""Job parser service."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from app.utils.llm import run_openai_json


SYSTEM_PROMPT = """You are an expert job description parser.

Extract structured data AND any decision-maker or recruiting contacts explicitly named in the text.

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
- Extract hiring managers, line managers, and people managers when a person name is given (e.g. "Hiring Manager: Jane Smith", "you will report to John Tan").
- Extract recruiter / talent / HR contacts when named (e.g. "Contact recruiter Maria Lee").
- Use role labels that match the JD: "Hiring Manager", "Line Manager", "Recruiter", etc.
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


def _extract_explicit_contacts(job_text: str) -> List[Dict[str, Any]]:
    """Regex fallback for hiring managers and named contacts when the LLM misses them."""
    text = str(job_text or "")
    if not text.strip():
        return []

    name_pattern = r"([A-Z][A-Za-z'-]+(?:\s+[A-Z][A-Za-z'-]+){1,3})"
    patterns: List[tuple[str, str]] = [
        (rf"(?i)hiring\s+manager\s*[:\-]\s*{name_pattern}", "Hiring Manager"),
        (rf"(?i)line\s+manager\s*[:\-]\s*{name_pattern}", "Line Manager"),
        (rf"(?i)recruiting\s+manager\s*[:\-]\s*{name_pattern}", "Recruiting Manager"),
        (rf"(?i)people\s+manager\s*[:\-]\s*{name_pattern}", "People Manager"),
        (rf"(?i)report(?:s)?\s+to\s*[:\-]?\s*{name_pattern}", "Manager"),
        (rf"(?i)recruiter\s*[:\-]\s*{name_pattern}", "Recruiter"),
        (rf"(?i)contact\s*[:\-]\s*{name_pattern}", "Recruiter"),
    ]

    emails = set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", text))
    contacts: List[Dict[str, Any]] = []
    seen_names: set[str] = set()

    for pattern, role in patterns:
        for match in re.finditer(pattern, text):
            name = str(match.group(1) or "").strip().strip(".,;:()[]{}")
            if not name:
                continue
            parts = [part for part in name.split() if part]
            if len(parts) < 2 or len(parts) > 4:
                continue
            if not all(re.match(r"^[A-Z][A-Za-z'-]+$", part) for part in parts):
                continue
            lowered = name.lower()
            if lowered in seen_names:
                continue
            seen_names.add(lowered)
            contacts.append(
                {
                    "name": name,
                    "role": role,
                    "email": next(iter(emails), None) if len(emails) == 1 else None,
                }
            )
    return contacts


def parse_job_text(job_text: str) -> Dict[str, Any]:
    safe = (job_text or "").strip()
    if not safe:
        return _fallback("")

    try:
        parsed = run_openai_json(SYSTEM_PROMPT, safe)
    except Exception:
        parsed = _fallback(safe)

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

    existing_names = {str(c.get("name", "")).strip().lower() for c in contacts}
    for contact in _extract_explicit_contacts(safe):
        name_key = str(contact.get("name", "")).strip().lower()
        if not name_key or name_key in existing_names:
            continue
        existing_names.add(name_key)
        contacts.append(contact)

    return {
        "title": str(parsed.get("title", "Unknown")).strip() or "Unknown",
        "company": str(parsed.get("company", "Unknown")).strip() or "Unknown",
        "hard_requirements": _normalize_list(parsed.get("hard_requirements", [])),
        "skills": _normalize_list(parsed.get("skills", [])),
        "keywords": _normalize_list(parsed.get("keywords", [])),
        "description": str(parsed.get("description", safe)),
        "recruiter_contacts": contacts,
    }
