"""TinyFish-based contact discovery.

TinyFish integration is isolated in this module by design.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional


ROLE_KEYWORDS = (
    "recruiter",
    "talent",
    "hr",
    "hiring manager",
    "manager",
    "lead",
)


def _is_relevant_role(role_text: str) -> bool:
    normalized = role_text.lower()
    return any(keyword in normalized for keyword in ROLE_KEYWORDS)


def _extract_email(text: str) -> Optional[str]:
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else None


def _extract_linkedin(text: str) -> Optional[str]:
    match = re.search(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/[^\s)\"'>]+", text, flags=re.IGNORECASE)
    return match.group(0) if match else None


def _parse_contact_from_text(raw_text: str) -> Optional[Dict[str, Optional[str]]]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return None

    name = lines[0][:120]
    role = lines[1][:120] if len(lines) > 1 else "Unknown"
    linkedin_url = _extract_linkedin(raw_text)
    email = _extract_email(raw_text)

    if not _is_relevant_role(role):
        return None

    return {
        "name": name,
        "role": role,
        "linkedin_url": linkedin_url,
        "email": email,
    }


def _tinyfish_fetch_text(query: str) -> List[str]:
    """Fetch candidate snippets using TinyFish only.

    Replace this stub with your environment's TinyFish client call.
    Expected return: list of public page text snippets.
    """
    try:
        # Example contract for a TinyFish client:
        # from tinyfish import TinyFishClient
        # client = TinyFishClient()
        # pages = client.search_public_pages(query=query, max_results=10)
        # return [page.get("text", "") for page in pages]
        _ = query
        return []
    except Exception:
        return []


def find_contacts(company: str, role: str) -> List[Dict[str, Optional[str]]]:
    """Find relevant contacts for one company and role using TinyFish only."""
    safe_company = (company or "Unknown").strip() or "Unknown"
    safe_role = (role or "Unknown").strip() or "Unknown"

    queries = [
        f"{safe_company} recruiter",
        f"{safe_company} {safe_role}",
        f"{safe_company} hiring manager",
    ]

    contacts: List[Dict[str, Optional[str]]] = []
    seen_keys = set()

    for query in queries:
        snippets = _tinyfish_fetch_text(query)
        for snippet in snippets:
            contact = _parse_contact_from_text(snippet)
            if not contact:
                continue
            dedupe_key = (
                (contact.get("name") or "").lower(),
                (contact.get("linkedin_url") or "").lower(),
                (contact.get("email") or "").lower(),
            )
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            contacts.append(contact)
            if len(contacts) >= 10:
                return contacts

    return contacts[:10]
