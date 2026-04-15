"""TinyFish-safe contact discovery service."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import unquote


def _build_queries(company: str, role: str) -> List[str]:
    return [
        f"{company} {role} LinkedIn",
        f"{company} recruiter LinkedIn",
    ]


def _extract_urls(text: str) -> List[str]:
    return re.findall(r'https?://[^\s"\'<>]+', text or "", flags=re.IGNORECASE)


def _tinyfish_fetch_texts(query: str) -> List[str]:
    """Fetch query snippets and page content via TinyFish SDK."""
    api_key = os.getenv("TINYFISH_API_KEY", "").strip()
    if not api_key:
        return []

    try:
        from tinyfish import TinyFish  # type: ignore

        client = TinyFish(api_key=api_key)
        texts: List[str] = []
        try:
            search = client.search.query(query=query, language="en")
            for result in search.results or []:
                snippet = " ".join(
                    [str(result.title or "").strip(), str(result.snippet or "").strip(), str(result.url or "").strip()]
                ).strip()
                if snippet:
                    texts.append(snippet)
        finally:
            client.close()

        return texts
    except Exception:
        return []


def _extract_linkedin_url(urls: List[str]) -> Optional[str]:
    for url in urls:
        value = (unquote(url) or "").strip().rstrip(").,;\"'")
        if "linkedin.com/in/" in value.lower():
            return value
    return None


def _extract_name(text: str) -> Optional[str]:
    match = re.search(r"\b([A-Z][a-z]{1,20}\s+[A-Z][a-z]{1,25})\b", text)
    return match.group(1) if match else None


def _infer_role(text: str, default_role: str) -> str:
    lowered = text.lower()
    for label in ("recruiter", "hiring manager", "manager", "lead", "director"):
        if label in lowered:
            return label.title()
    return default_role


def _confidence(company: str, role: str, snippet: str, linkedin_url: Optional[str]) -> float:
    score = 0.0
    if company.lower() in snippet.lower():
        score += 0.45
    if any(token in snippet.lower() for token in role.lower().split()):
        score += 0.35
    if linkedin_url:
        score += 0.2
    return round(min(score, 1.0), 4)


def find_contacts(company: str, role: str) -> List[Dict[str, Any]]:
    safe_company = (company or "Unknown").strip() or "Unknown"
    safe_role = (role or "Unknown").strip() or "Unknown"
    contacts: List[Dict[str, Any]] = []
    seen = set()

    for query in _build_queries(safe_company, safe_role):
        snippets = _tinyfish_fetch_texts(query)
        for snippet in snippets:
            if len(snippet) < 20:
                continue
            name = _extract_name(snippet)
            if not name:
                continue

            urls = _extract_urls(snippet)
            linkedin_url = _extract_linkedin_url(urls)
            contact_role = _infer_role(snippet, safe_role)
            confidence = _confidence(safe_company, safe_role, snippet, linkedin_url)
            key = (name.lower(), safe_company.lower())
            if key in seen:
                continue
            seen.add(key)

            contacts.append(
                {
                    "name": name,
                    "role": contact_role,
                    "company": safe_company,
                    "linkedin_url": linkedin_url,
                    "email": None,
                    "source": "discovered",
                    "confidence": confidence,
                    "search_hint": f"{name} {safe_company} {safe_role} LinkedIn",
                }
            )

    contacts.sort(key=lambda c: float(c.get("confidence", 0.0)), reverse=True)
    return contacts[:10]
