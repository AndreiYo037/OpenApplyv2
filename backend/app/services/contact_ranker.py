"""Contact ranking service (LLM + fallback)."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from app.utils.llm import run_openai_json


def _is_valid_contact(contact: Dict[str, Any]) -> bool:
    name = str(contact.get("name", "")).strip()
    if not name:
        return False
    parts = [p for p in name.split() if p]
    return 2 <= len(parts) <= 4 and all(re.match(r"^[A-Za-z][A-Za-z'-.]*$", part) for part in parts)


def _priority_bucket(item: Dict[str, Any]) -> int:
    source = item.get("source")
    role = str(item.get("role", "")).lower()
    affinity = float(item.get("company_affinity", 0.0) or 0.0)
    external_agency = bool(item.get("external_agency", False))
    is_hm = any(
        phrase in role
        for phrase in ("hiring manager", "line manager", "recruiting manager", "people manager")
    )
    is_broad_mgr = (
        ("manager" in role or "director" in role or "head" in role or "vp" in role)
        and "recruiter" not in role
        and "talent" not in role
    )
    is_recruiter = any(x in role for x in ("recruiter", "talent", "human resources", "people partner"))

    if source == "job_description":
        if is_hm or is_broad_mgr:
            return 0
        if is_recruiter:
            return 1
        return 2
    if external_agency and affinity < 0.8:
        return 9
    if is_hm:
        return 3 if affinity >= 0.45 else 5
    if is_broad_mgr:
        return 4 if affinity >= 0.45 else 6
    if is_recruiter:
        return 5 if affinity >= 0.6 else 7
    return 6 if affinity >= 0.7 else 8


def _fallback_rank(contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def order_key(item: Dict[str, Any]) -> tuple[int, float, float]:
        return (
            _priority_bucket(item),
            -float(item.get("company_affinity", 0.0) or 0.0),
            -float(item.get("confidence", 0.0) or 0.0),
        )

    filtered = [c for c in contacts if _is_valid_contact(c)]
    sorted_contacts = sorted(filtered, key=order_key)
    return sorted_contacts[:5]


def rank_contacts(job: Dict[str, Any], contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not contacts:
        return []

    fallback = _fallback_rank(contacts)
    system = """Rank contacts for outreach.

Priority:
1) job_description hiring managers and people managers
2) job_description recruiters
3) discovered hiring managers
4) other discovered contacts

Return STRICT JSON:
{"top_contacts": [contact_objects_in_best_order_max_5]}

Each object must include the same name and linkedin_url fields as the input contacts when known.
"""
    try:
        output = run_openai_json(system, str({"job": job, "contacts": contacts}))
        ranked = output.get("top_contacts", [])
        if not isinstance(ranked, list):
            return fallback

        canonical = {
            (
                str(contact.get("name", "")).strip().lower(),
                str(contact.get("linkedin_url", "")).strip().lower(),
            ): contact
            for contact in contacts
            if isinstance(contact, dict)
        }

        merged: List[Dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for item in ranked:
            if not isinstance(item, dict):
                continue
            key = (
                str(item.get("name", "")).strip().lower(),
                str(item.get("linkedin_url", "")).strip().lower(),
            )
            candidate = canonical.get(key)
            if not candidate:
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
