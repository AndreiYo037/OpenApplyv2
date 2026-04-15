"""LLM-powered contact ranking service."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List
from urllib import error, request


OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def _normalize_contact(contact: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": str(contact.get("name", "")).strip(),
        "role": str(contact.get("role", "")).strip(),
        "company": str(contact.get("company", "Unknown")).strip() or "Unknown",
        "source": str(contact.get("source", "")).strip(),
        "profile_url": contact.get("profile_url"),
        "linkedin_url": contact.get("linkedin_url"),
        "email": contact.get("email"),
        "confidence": float(contact.get("confidence", 0.0) or 0.0),
        "search_hint": str(contact.get("search_hint", "")).strip(),
    }


def _fallback_rank_contacts(job: Dict[str, Any], contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    role = str(job.get("title", "")).lower()

    def score(contact: Dict[str, Any]) -> float:
        base = float(contact.get("confidence", 0.0) or 0.0)
        role_text = str(contact.get("role", "")).lower()
        if role and role in role_text:
            base += 0.2
        if contact.get("linkedin_url"):
            base += 0.15
        if contact.get("email"):
            base += 0.1
        if any(word in role_text for word in ("recruiter", "hiring manager", "manager", "lead")):
            base += 0.1
        return min(base, 1.0)

    ranked = []
    for contact in contacts:
        c = _normalize_contact(contact)
        relevance = round(score(c), 4)
        c["relevance_score"] = relevance
        c["reason"] = "Ranked by confidence, role alignment, and reachable contact signals."
        ranked.append(c)

    ranked.sort(key=lambda x: float(x.get("relevance_score", 0.0)), reverse=True)
    return ranked[:5]


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


def _call_openai_ranker(job: Dict[str, Any], contacts: List[Dict[str, Any]]) -> Any:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    system_prompt = (
        "You rank hiring outreach contacts for one job.\n"
        "Return ONLY a JSON array with up to 5 contacts, sorted best to worst.\n"
        "Each item must include:\n"
        "{\n"
        '  "name": str,\n'
        '  "role": str,\n'
        '  "company": str,\n'
        '  "source": str,\n'
        '  "profile_url": str|null,\n'
        '  "linkedin_url": str|null,\n'
        '  "email": str|null,\n'
        '  "confidence": float,\n'
        '  "search_hint": str,\n'
        '  "relevance_score": float,\n'
        '  "reason": str\n'
        "}\n"
        "Rules:\n"
        "- Prioritize recruiters, hiring managers, and role-adjacent team members.\n"
        "- Prefer strong company/role matches and reachable contacts.\n"
        "- relevance_score must be between 0 and 1.\n"
        "- Output valid JSON only."
    )

    user_payload = {
        "job": {
            "title": job.get("title"),
            "company": job.get("company"),
            "skills": job.get("skills", []),
            "keywords": job.get("keywords", []),
        },
        "contacts": contacts,
    }

    body = {
        "model": os.getenv("OPENAI_PARSER_MODEL", "gpt-4o-mini"),
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload)},
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
        raise RuntimeError("Failed to parse ranked contact JSON")
    return parsed


def _normalize_ranked_output(raw: Any, fallback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return fallback

    normalized: List[Dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        role = str(item.get("role", "")).strip()
        if not name or not role:
            continue

        relevance_raw = item.get("relevance_score", 0.0)
        try:
            relevance = max(0.0, min(float(relevance_raw), 1.0))
        except (TypeError, ValueError):
            relevance = 0.0

        normalized.append(
            {
                "name": name,
                "role": role,
                "company": str(item.get("company", "Unknown")).strip() or "Unknown",
                "source": str(item.get("source", "")).strip(),
                "profile_url": item.get("profile_url"),
                "linkedin_url": item.get("linkedin_url"),
                "email": item.get("email"),
                "confidence": float(item.get("confidence", 0.0) or 0.0),
                "search_hint": str(item.get("search_hint", "")).strip(),
                "relevance_score": round(relevance, 4),
                "reason": str(item.get("reason", "")).strip()
                or "Selected for role and company relevance.",
            }
        )

    if not normalized:
        return fallback

    normalized.sort(key=lambda x: float(x.get("relevance_score", 0.0)), reverse=True)
    return normalized[:5]


def rank_contacts(job: Dict[str, Any], contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rank top contacts using LLM with a deterministic fallback."""
    if not contacts:
        return []

    safe_contacts = [_normalize_contact(c) for c in contacts if isinstance(c, dict)]
    fallback = _fallback_rank_contacts(job, safe_contacts)

    try:
        raw_ranked = _call_openai_ranker(job, safe_contacts)
        return _normalize_ranked_output(raw_ranked, fallback)
    except Exception:
        return fallback
