"""TinyFish-only contact scraping from public search result pages.

Constraints enforced:
- Never scrape or parse linkedin.com pages directly.
- Only extract linkedin.com/in/ links if present in third-party/public pages.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote


SEARCH_ENGINES = [
    "https://www.google.com/search?q={query}",
    "https://www.bing.com/search?q={query}",
]

RELEVANT_ROLE_WORDS = {
    "recruiter",
    "talent",
    "acquisition",
    "hiring",
    "manager",
    "lead",
    "head",
    "director",
    "engineer",
    "developer",
}

NAME_STOPWORDS = {
    "linkedin",
    "jobs",
    "hiring",
    "careers",
    "company",
    "team",
    "official",
    "home",
    "page",
}


def _build_queries(company: str, role: str) -> List[str]:
    return [
        f"{company} {role} LinkedIn",
        f"{company} recruiter LinkedIn",
        f"{company} hiring manager {role}",
        f"{company} team {role}",
    ]


def _tinyfish_fetch_html(url: str) -> str:
    """Fetch public HTML via TinyFish only.

    Replace this stub with your TinyFish SDK call in production.
    """
    try:
        # Example integration seam:
        # from tinyfish import TinyFishClient
        # client = TinyFishClient()
        # response = client.fetch_public_html(url=url)
        # return response.get("html", "")
        _ = url
        return ""
    except Exception:
        return ""


def _strip_tags(text: str) -> str:
    cleaned = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"<style[\s\S]*?</style>", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _extract_urls(html: str) -> List[str]:
    urls = re.findall(r'https?://[^\s"\'<>]+', html, flags=re.IGNORECASE)
    return list(dict.fromkeys(urls))


def _extract_linkedin_url(urls: List[str]) -> Optional[str]:
    for url in urls:
        if "linkedin.com/in/" in url.lower():
            return url.rstrip(").,;\"'")
    return None


def _extract_profile_url(urls: List[str], linkedin_url: Optional[str]) -> Optional[str]:
    for url in urls:
        lower = url.lower()
        if "linkedin.com" in lower:
            continue
        if any(domain in lower for domain in ("github.com", "about.me", "angel.co", "wellfound.com")):
            return url.rstrip(").,;\"'")
    for url in urls:
        lower = url.lower()
        if "google.com/search" in lower or "bing.com/search" in lower or "linkedin.com" in lower:
            continue
        if url != linkedin_url:
            return url.rstrip(").,;\"'")
    return None


def _extract_email(text: str) -> Optional[str]:
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else None


def _candidate_name_from_text(text: str) -> Optional[str]:
    # Basic "Firstname Lastname" detector with titlecase words.
    patterns = [
        r"\b([A-Z][a-z]{1,20}\s+[A-Z][a-z]{1,25})\b",
        r"\b([A-Z][a-z]{1,20}\s+[A-Z]\.\s*[A-Z][a-z]{1,25})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        candidate = match.group(1).strip()
        tokens = candidate.lower().split()
        if any(token in NAME_STOPWORDS for token in tokens):
            continue
        return candidate
    return None


def _extract_role(text: str, fallback_role: str) -> str:
    role_patterns = [
        r"\b(recruiter|talent acquisition(?: specialist| manager)?|hr(?: manager)?|hiring manager|engineering manager|team lead|director)\b",
        r"\b(senior|lead|principal)?\s*(software engineer|backend engineer|data engineer|developer)\b",
    ]
    lowered = text.lower()
    for pattern in role_patterns:
        match = re.search(pattern, lowered, flags=re.IGNORECASE)
        if match:
            return re.sub(r"\s+", " ", match.group(0)).strip().title()
    return fallback_role


def _is_real_person(name: str) -> bool:
    parts = [p for p in name.split() if p]
    if len(parts) < 2 or len(parts) > 4:
        return False
    if any(not p[0].isalpha() for p in parts):
        return False
    return True


def _role_relevance_score(role_text: str, target_role: str) -> float:
    role_tokens = set(re.findall(r"[a-z]+", role_text.lower()))
    target_tokens = set(re.findall(r"[a-z]+", target_role.lower()))
    overlap = len(role_tokens & target_tokens)
    keyword_bonus = 1 if role_tokens & RELEVANT_ROLE_WORDS else 0
    score = min(1.0, 0.4 + 0.15 * overlap + 0.15 * keyword_bonus) if role_tokens else 0.0
    return score


def _source_reliability(source_url: str) -> float:
    lower = source_url.lower()
    if "google.com/search" in lower or "bing.com/search" in lower:
        return 0.7
    return 0.55


def _confidence(
    company_match: bool,
    role_relevance: float,
    has_linkedin: bool,
    source_reliability: float,
) -> float:
    score = 0.0
    score += 0.30 if company_match else 0.10
    score += 0.35 * max(0.0, min(role_relevance, 1.0))
    score += 0.20 if has_linkedin else 0.05
    score += 0.15 * max(0.0, min(source_reliability, 1.0))
    return round(min(score, 1.0), 4)


def _extract_candidates_from_html(
    html: str,
    source_url: str,
    company: str,
    role: str,
) -> List[Dict[str, Any]]:
    if not html:
        return []

    text = _strip_tags(html)
    snippets = re.split(r"\s{2,}|(?:\.\s+)", text)
    urls = _extract_urls(html)
    linkedin_url = _extract_linkedin_url(urls)
    profile_url = _extract_profile_url(urls, linkedin_url)
    email = _extract_email(text)

    candidates: List[Dict[str, Any]] = []
    for snippet in snippets:
        snippet = snippet.strip()
        if len(snippet) < 30:
            continue
        name = _candidate_name_from_text(snippet)
        if not name or not _is_real_person(name):
            continue

        inferred_role = _extract_role(snippet, role)
        company_match = company.lower() in snippet.lower()
        relevance = _role_relevance_score(inferred_role, role)
        if relevance < 0.35 and not company_match:
            continue

        source_rel = _source_reliability(source_url)
        confidence = _confidence(
            company_match=company_match,
            role_relevance=relevance,
            has_linkedin=linkedin_url is not None,
            source_reliability=source_rel,
        )

        candidate = {
            "name": name,
            "role": inferred_role,
            "company": company if company_match else "Unknown",
            "source": source_url,
            "profile_url": profile_url,
            "linkedin_url": linkedin_url,
            "email": email,
            "confidence": confidence,
            "search_hint": f"{name} {company} {role} LinkedIn",
        }
        candidates.append(candidate)

    return candidates


def _dedupe_contacts(contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for item in contacts:
        key = (
            (item.get("name") or "").lower(),
            (item.get("linkedin_url") or "").lower(),
            (item.get("profile_url") or "").lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def find_contacts(company: str, role: str) -> List[Dict[str, Any]]:
    """Discover 5-10 contacts from public search result pages via TinyFish."""
    safe_company = (company or "Unknown").strip() or "Unknown"
    safe_role = (role or "Unknown").strip() or "Unknown"

    queries = _build_queries(safe_company, safe_role)
    contacts: List[Dict[str, Any]] = []

    for query in queries:
        encoded = quote(query)
        for template in SEARCH_ENGINES:
            source_url = template.format(query=encoded)
            html = _tinyfish_fetch_html(source_url)
            extracted = _extract_candidates_from_html(
                html=html,
                source_url=source_url,
                company=safe_company,
                role=safe_role,
            )
            contacts.extend(extracted)

    cleaned = _dedupe_contacts(contacts)
    cleaned.sort(key=lambda item: float(item.get("confidence", 0.0)), reverse=True)

    # Fail-safe: even if no linkedin_url exists, return best candidates with search hints.
    return cleaned[:10]
