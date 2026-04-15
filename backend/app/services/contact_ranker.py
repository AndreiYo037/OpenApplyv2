"""Contact ranking service (LLM + deterministic guardrails)."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from app.utils.llm import run_openai_json

INVALID_CONTACT_NAMES = {
    "job application",
    "data science",
    "data scientist",
    "analytics internship",
    "machine learning",
    "careers current",
}


def _is_valid_contact(contact: Dict[str, Any]) -> bool:
    name = str(contact.get("name", "")).strip()
    if not name:
        return False
    lowered = name.lower()
    if lowered in INVALID_CONTACT_NAMES:
        return False
    parts = [p for p in name.split() if p]
    if len(parts) < 2 or len(parts) > 4:
        return False
    if not all(re.match(r"^[A-Za-z][A-Za-z'-.]*$", part) for part in parts):
        return False
    return True


def _priority(item: Dict[str, Any]) -> int:
    source = item.get("source")
    role = str(item.get("role", "")).lower()
    if source == "job_description":
        return 0
    if "hiring manager" in role or "manager" in role:
        return 1
    if "recruiter" in role or "talent" in role:
        return 2
    if "lead" in role:
        return 3
    return 4


def _fallback_rank(contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def order_key(item: Dict[str, Any]) -> tuple[int, float, int]:
        has_channel = int(bool(item.get("linkedin_url") or item.get("email")))
        return (_priority(item), -float(item.get("confidence", 0.0) or 0.0), -has_channel)

    filtered = [contact for contact in contacts if _is_valid_contact(contact)]
    sorted_contacts = sorted(filtered, key=order_key)
    return sorted_contacts[:5]


def rank_contacts(job: Dict[str, Any], contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not contacts:
        return []

    fallback = _fallback_rank(contacts)
    system = """Rank contacts for outreach.

Priority:
1) job_description recruiters
2) hiring managers
3) others

Return STRICT JSON:
{"top_contacts": [contact_objects_in_best_order_max_5]}
"""
    try:
        output = run_openai_json(system, str({"job": job, "contacts": contacts}))
        ranked = output.get("top_contacts", [])
        if not isinstance(ranked, list):
            return fallback

        # Keep only canonical discovered contacts to avoid LLM hallucinated entries.
        canonical = {
            (
                str(contact.get("name", "")).strip().lower(),
                str(contact.get("linkedin_url", "")).strip().lower(),
            ): contact
            for contact in contacts
            if isinstance(contact, dict)
        }

        merged: List[Dict[str, Any]] = []
        seen = set()
        for item in ranked:
            if not isinstance(item, dict):
                continue
            key = (
                str(item.get("name", "")).strip().lower(),
                str(item.get("linkedin_url", "")).strip().lower(),
            )
            candidate = canonical.get(key)
            if not candidate:
                # Name-only fallback when linkedin_url differs.
                candidate = next(
                    (
                        contact
                        for contact in contacts
                        if str(contact.get("name", "")).strip().lower() == key[0]
                    ),
                    None,
                )
            if not isinstance(candidate, dict) or not _is_valid_contact(candidate):
                continue
            dedupe_key = (
                str(candidate.get("name", "")).strip().lower(),
                str(candidate.get("linkedin_url", "")).strip().lower(),
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            merged.append(candidate)

        if not merged:
            return fallback
        return _fallback_rank(merged)
    except Exception:
        return fallback
