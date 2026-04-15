"""LLM-driven contact target generation service."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List
from urllib import error, request


OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def _fallback_targets(role: str) -> List[Dict[str, Any]]:
    safe_role = (role or "target role").strip()
    return [
        {
            "type": "recruiter",
            "titles": [
                "Recruiter",
                "Talent Acquisition Specialist",
                f"{safe_role} Recruiter",
            ],
        },
        {
            "type": "hiring_manager",
            "titles": [
                f"{safe_role} Manager",
                f"Head of {safe_role}",
                f"{safe_role} Team Lead",
            ],
        },
        {
            "type": "team_member",
            "titles": [
                safe_role,
                f"Senior {safe_role}",
                f"Lead {safe_role}",
            ],
        },
    ]


def _extract_json(content: str) -> Any:
    text = (content or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return None
    return None


def _normalize_targets(raw: Any, role: str) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return _fallback_targets(role)

    normalized: List[Dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        target_type = str(item.get("type") or "").strip().lower()
        titles_raw = item.get("titles", [])
        if not target_type or not isinstance(titles_raw, list):
            continue
        titles = [str(t).strip() for t in titles_raw if str(t).strip()]
        if not titles:
            continue
        normalized.append({"type": target_type, "titles": titles[:10]})

    return normalized or _fallback_targets(role)


def _call_openai_for_targets(job: Dict[str, Any]) -> Any:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    role = str(job.get("title") or "target role")
    company = str(job.get("company") or "Unknown")
    skills = job.get("skills", [])
    description = str(job.get("description") or "")

    prompt = (
        "You generate outreach contact targets for hiring.\n"
        "Given one job, return ONLY JSON array with objects:\n"
        '[{"type":"recruiter","titles":["..."]}, {"type":"hiring_manager","titles":["..."]}, {"type":"team_member","titles":["..."]}]\n'
        "Rules:\n"
        "- Include recruiter, hiring_manager, team_member types.\n"
        "- Titles must be realistic for this job/company context.\n"
        "- Keep each titles list concise (3-8 items).\n"
        "- Output valid JSON only (no markdown).\n"
    )

    user_content = json.dumps(
        {
            "title": role,
            "company": company,
            "skills": skills,
            "description": description,
        }
    )

    body = {
        "model": os.getenv("OPENAI_PARSER_MODEL", "gpt-4o-mini"),
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content},
        ],
    }

    req = request.Request(
        OPENAI_API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"OpenAI API HTTP error: {exc.code} {raw}") from exc
    except Exception as exc:
        raise RuntimeError(f"OpenAI API call failed: {exc}") from exc

    choices = payload.get("choices", [])
    if not choices:
        raise RuntimeError("OpenAI API returned no choices")

    content = choices[0].get("message", {}).get("content", "")
    parsed = _extract_json(content)
    if parsed is None:
        raise RuntimeError("Failed to parse target JSON")
    return parsed


def generate_contact_targets(job: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate recruiter/hiring-manager/team contact title targets."""
    safe_job = job or {}
    role = str(safe_job.get("title") or "target role")
    try:
        raw = _call_openai_for_targets(safe_job)
        return _normalize_targets(raw, role)
    except Exception:
        return _fallback_targets(role)
