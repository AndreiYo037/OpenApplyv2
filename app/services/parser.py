"""LLM-powered job text parser service."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List
from urllib import error, request


OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def _minimal_structure(job_text: str) -> Dict[str, Any]:
    return {
        "title": "Unknown",
        "company": "Unknown",
        "skills": [],
        "keywords": [],
        "description": (job_text or "").strip(),
    }


def _normalize_parsed_payload(payload: Dict[str, Any], job_text: str) -> Dict[str, Any]:
    title = str(payload.get("title") or "Unknown").strip() or "Unknown"
    company = str(payload.get("company") or "Unknown").strip() or "Unknown"

    raw_skills = payload.get("skills", [])
    skills = [str(item).strip() for item in raw_skills if str(item).strip()] if isinstance(raw_skills, list) else []

    raw_keywords = payload.get("keywords", [])
    keywords = (
        [str(item).strip() for item in raw_keywords if str(item).strip()]
        if isinstance(raw_keywords, list)
        else []
    )

    description = str(payload.get("description") or (job_text or "").strip())

    return {
        "title": title,
        "company": company,
        "skills": skills,
        "keywords": keywords,
        "description": description,
    }


def _extract_json(content: str) -> Dict[str, Any]:
    """Extract JSON object from model output with basic tolerance."""
    content = (content or "").strip()
    if not content:
        return {}

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(content[start : end + 1])
            except json.JSONDecodeError:
                return {}
    return {}


def _call_openai_parser(job_text: str) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    parser_prompt = (
        "You are a structured parser for job descriptions.\n"
        "Extract and return ONLY valid JSON with this exact schema:\n"
        "{\n"
        '  "title": "string",\n'
        '  "company": "string",\n'
        '  "skills": ["string"],\n'
        '  "keywords": ["string"],\n'
        '  "description": "string"\n'
        "}\n\n"
        "Rules:\n"
        "- Keep output strictly JSON (no markdown).\n"
        "- If title/company is missing, use \"Unknown\".\n"
        "- Skills should be specific technical/professional skills.\n"
        "- Keywords should include concise role-relevant terms.\n"
        "- description must preserve the original job text exactly.\n"
    )

    body = {
        "model": os.getenv("OPENAI_PARSER_MODEL", "gpt-4o-mini"),
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": parser_prompt},
            {"role": "user", "content": job_text},
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

    message = choices[0].get("message", {})
    content = message.get("content", "")
    parsed = _extract_json(content)
    if not parsed:
        raise RuntimeError("Failed to parse JSON from OpenAI response")
    return parsed


def parse_job_text(job_text: str) -> Dict[str, Any]:
    """Parse raw job text into structured fields using OpenAI with fallback."""
    safe_text = (job_text or "").strip()
    if not safe_text:
        return _minimal_structure(job_text="")

    try:
        parsed = _call_openai_parser(safe_text)
        return _normalize_parsed_payload(parsed, safe_text)
    except Exception:
        return _minimal_structure(safe_text)
