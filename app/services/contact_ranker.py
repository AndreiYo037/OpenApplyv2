"""LLM-assisted contact enrichment and ranking."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List
from urllib import error, request

from app.services.contact_scorer import score_contact


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


def _heuristic_enrichment(job_intent: Dict[str, Any], contact: Dict[str, Any]) -> Dict[str, Any]:
    role = str(contact.get("role", "")).lower()
    hint = str(contact.get("search_hint", "")).lower()
    domain = str(job_intent.get("domain", "")).lower()
    merged = f"{role} {hint}"

    if domain and domain in merged:
        domain_match = "exact"
    elif any(token in merged for token in ("software", "data", "analyst", "business", "product", "engineer")):
        domain_match = "related"
    else:
        domain_match = "weak"

    if any(token in role for token in ("ceo", "cto", "cfo", "chief", "founder")):
        seniority = "c_level"
    elif any(token in role for token in ("vp", "vice president", "director", "head")):
        seniority = "senior_leadership"
    elif any(token in role for token in ("junior", "intern", "associate")):
        seniority = "junior"
    else:
        seniority = "mid"

    singapore_based = "singapore" in merged or "sg.linkedin.com" in str(contact.get("linkedin_url", "")).lower()
    hiring_activity = any(token in merged for token in ("hiring", "talent", "recruit", "internship"))

    return {
        "domain_match": domain_match,
        "seniority_bucket": seniority,
        "singapore_based": singapore_based,
        "hiring_activity": hiring_activity,
    }


def _enrich_contacts_with_openai(job_intent: Dict[str, Any], contacts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return {}

    system_prompt = """You enrich contact metadata for internship outreach scoring.
Return STRICT JSON:
{
  "contacts": [
    {
      "name": string,
      "domain_match": "exact" | "related" | "weak",
      "seniority_bucket": "mid" | "junior" | "senior_leadership" | "c_level",
      "singapore_based": boolean,
      "hiring_activity": boolean
    }
  ]
}
Rules:
- Infer based only on provided role/title/snippet data.
- Keep the contact name exactly as provided when possible.
"""
    body = {
        "model": os.getenv("OPENAI_PARSER_MODEL", "gpt-4o-mini"),
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({"job_intent": job_intent, "contacts": contacts})},
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
        choices = payload.get("choices", [])
        if not choices:
            return {}
        content = str(choices[0].get("message", {}).get("content", "")).strip()
        parsed = json.loads(content) if content else {}
    except (error.HTTPError, ValueError, json.JSONDecodeError, Exception):
        return {}

    enriched: Dict[str, Dict[str, Any]] = {}
    for item in parsed.get("contacts", []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip().lower()
        if not name:
            continue
        enriched[name] = {
            "domain_match": str(item.get("domain_match", "weak")).strip().lower(),
            "seniority_bucket": str(item.get("seniority_bucket", "mid")).strip().lower(),
            "singapore_based": bool(item.get("singapore_based")),
            "hiring_activity": bool(item.get("hiring_activity")),
        }
    return enriched


def rank_contacts(job_intent: Dict[str, Any], contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enrich and rank contacts by continuous CONTACT_SCORE (0-100)."""
    if not contacts:
        return []

    safe_contacts = [_normalize_contact(c) for c in contacts if isinstance(c, dict)]
    llm_enrichment = _enrich_contacts_with_openai(job_intent, safe_contacts)

    ranked: List[Dict[str, Any]] = []
    for contact in safe_contacts:
        key = str(contact.get("name", "")).strip().lower()
        enrichment = llm_enrichment.get(key) or _heuristic_enrichment(job_intent, contact)
        scored = score_contact(contact, job_intent=job_intent, enrichment=enrichment)
        ranked.append(
            {
                **contact,
                "score": scored["score"],
                "reason": scored["reason"],
                "contact_components": scored["components"],
                "enrichment": enrichment,
            }
        )

    ranked.sort(key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True)
    return ranked[:10]
