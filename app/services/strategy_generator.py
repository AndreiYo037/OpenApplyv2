"""Outreach strategy generation service."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List
from urllib import error, request

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def _safe_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text if text else default


def _extract_json(content: str) -> Dict[str, Any]:
    text = (content or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                data = json.loads(text[start : end + 1])
                return data if isinstance(data, dict) else {}
            except json.JSONDecodeError:
                return {}
    return {}


def _fallback_strategy(job: Dict[str, Any], user_profile: Dict[str, Any], contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    title = _safe_text(job.get("title"), "target role")
    company = _safe_text(job.get("company"), "target company")
    skills = [str(s).strip() for s in user_profile.get("skills", []) if str(s).strip()]

    first_contact = "No strong contact identified yet"
    if contacts:
        sorted_contacts = sorted(
            contacts,
            key=lambda c: float(c.get("relevance_score", c.get("confidence", 0.0)) or 0.0),
            reverse=True,
        )
        top = sorted_contacts[0]
        first_contact = f"{_safe_text(top.get('name'), 'Top contact')} ({_safe_text(top.get('role'), 'Contact')})"

    angle = (
        f"Position yourself as a high-fit candidate for {title} at {company}, "
        "emphasizing direct role alignment and immediate execution value."
    )

    talking_points = [
        f"Highlight 2-3 matching skills: {', '.join(skills[:3]) if skills else 'relevant technical strengths'}.",
        "Share one measurable project outcome that maps to the role priorities.",
        "Ask one focused question about team priorities to start a practical conversation.",
    ]

    return {
        "who_to_message_first": first_contact,
        "angle": angle,
        "key_talking_points": talking_points,
    }


def _normalize_strategy(raw: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    who = _safe_text(raw.get("who_to_message_first"), fallback["who_to_message_first"])
    angle = _safe_text(raw.get("angle"), fallback["angle"])

    points = raw.get("key_talking_points")
    if isinstance(points, list):
        normalized_points = [str(p).strip() for p in points if str(p).strip()]
    else:
        normalized_points = []

    if not normalized_points:
        normalized_points = list(fallback["key_talking_points"])

    return {
        "who_to_message_first": who,
        "angle": angle,
        "key_talking_points": normalized_points[:5],
    }


def _call_openai_strategy(job: Dict[str, Any], user_profile: Dict[str, Any], contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    prompt = (
        "You generate concise job outreach strategy.\n"
        "Return ONLY valid JSON object with keys:\n"
        "{\n"
        '  "who_to_message_first": "string",\n'
        '  "angle": "string",\n'
        '  "key_talking_points": ["string"]\n'
        "}\n"
        "Rules:\n"
        "- Prioritize best contact (recruiter/hiring manager/high relevance).\n"
        "- Angle must be specific to role + company + candidate fit.\n"
        "- Provide 3-5 practical talking points.\n"
        "- Output JSON only.\n"
    )

    body = {
        "model": os.getenv("OPENAI_PARSER_MODEL", "gpt-4o-mini"),
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "job": {
                            "title": job.get("title"),
                            "company": job.get("company"),
                            "skills": job.get("skills", []),
                            "keywords": job.get("keywords", []),
                        },
                        "user_profile": user_profile,
                        "contacts": contacts[:5],
                    }
                ),
            },
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
    if not parsed:
        raise RuntimeError("Failed to parse strategy JSON")
    return parsed


def generate_strategy(job: Dict[str, Any], user_profile: Dict[str, Any], contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate outreach strategy: first contact, angle, and talking points."""
    safe_job = job or {}
    safe_profile = user_profile or {}
    safe_contacts = contacts or []

    fallback = _fallback_strategy(safe_job, safe_profile, safe_contacts)
    try:
        raw = _call_openai_strategy(safe_job, safe_profile, safe_contacts)
        return _normalize_strategy(raw, fallback)
    except Exception:
        return fallback


def _limit_words(text: str, max_words: int = 120) -> str:
    tokens = str(text or "").strip().split()
    if len(tokens) <= max_words:
        return " ".join(tokens)
    return " ".join(tokens[:max_words]).strip()


def generate_outreach_message(
    cv_structured: Dict[str, Any],
    top_projects: List[str],
    job: Dict[str, Any],
    job_intent: Dict[str, Any],
    company_intel: Dict[str, Any],
    top_contact: Dict[str, Any],
) -> str:
    """Generate highly personalized outreach message (<=120 words)."""
    fallback_skill = ", ".join(cv_structured.get("skills", [])[:2]) or "relevant technical skills"
    fallback_project = ", ".join(top_projects[:1]) or "my recent project"
    fallback_company_signal = ", ".join(company_intel.get("signals", [])[:1]) or "your recent initiative"
    fallback_contact_role = str(top_contact.get("role", "your team")).strip() or "your team"
    fallback = (
        f"Hi, I am an undergraduate in Singapore applying for {job.get('title', 'this internship')} at "
        f"{job.get('company', 'your company')}. I recently built {fallback_project}, where I used {fallback_skill} "
        f"to deliver measurable results. I was interested in {fallback_company_signal}, which aligns with my interest "
        f"in {job_intent.get('domain', 'this domain')} problems. Given your role as {fallback_contact_role}, could I "
        f"ask for 10 minutes to understand what the team values most in internship candidates?"
    )

    if not os.getenv("OPENAI_API_KEY", "").strip():
        return _limit_words(fallback, 120)

    system_prompt = """Write one outreach message for internship conversion.
Rules:
- Maximum 120 words.
- Must include:
  1) specific project or skill,
  2) company insight (recent activity/product),
  3) alignment with team/problem,
  4) context-aware reference to the contact role,
  5) a clear ask.
- Tone: confident, concise, non-generic.
- Output plain text only.
"""
    body = {
        "model": os.getenv("OPENAI_PARSER_MODEL", "gpt-4o-mini"),
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "cv_structured": cv_structured,
                        "top_projects": top_projects[:3],
                        "job": job,
                        "job_intent": job_intent,
                        "company_intel": company_intel,
                        "top_contact": top_contact,
                    }
                ),
            },
        ],
    }

    req = request.Request(
        OPENAI_API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', '').strip()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        choices = payload.get("choices", [])
        if not choices:
            return _limit_words(fallback, 120)
        message = str(choices[0].get("message", {}).get("content", "")).strip()
        return _limit_words(message or fallback, 120)
    except Exception:
        return _limit_words(fallback, 120)
