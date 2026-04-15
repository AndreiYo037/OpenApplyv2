"""Contact merge and dedup service."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _from_job_contact(item: Dict[str, Any], company: str, role: str) -> Dict[str, Any]:
    name = str(item.get("name", "")).strip()
    return {
        "name": name,
        "role": str(item.get("role", "Recruiter")).strip() or "Recruiter",
        "company": company,
        "linkedin_url": None,
        "email": item.get("email"),
        "source": "job_description",
        "confidence": 1.0,
        "search_hint": f"{name} {company} {role} LinkedIn",
    }


def _dedupe_key(contact: Dict[str, Any]) -> Tuple[str, str]:
    email = str(contact.get("email") or "").lower().strip()
    if email:
        return ("email", email)
    return (
        "name_company",
        f"{str(contact.get('name','')).lower().strip()}::{str(contact.get('company','')).lower().strip()}",
    )


def merge_contacts(
    job_contacts: List[Dict[str, Any]],
    scraped_contacts: List[Dict[str, Any]],
    company: str,
    role: str,
) -> List[Dict[str, Any]]:
    merged: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for contact in job_contacts:
        normalized = _from_job_contact(contact, company, role)
        key = _dedupe_key(normalized)
        merged[key] = normalized

    for contact in scraped_contacts:
        key = _dedupe_key(contact)
        if key not in merged:
            merged[key] = contact
            continue
        if merged[key].get("source") == "job_description":
            continue
        if float(contact.get("confidence", 0.0) or 0.0) > float(merged[key].get("confidence", 0.0) or 0.0):
            merged[key] = contact

    results = list(merged.values())
    results.sort(
        key=lambda c: (0 if c.get("source") == "job_description" else 1, -float(c.get("confidence", 0.0) or 0.0))
    )
    return results[:10]
