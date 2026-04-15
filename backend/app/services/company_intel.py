"""Company intelligence extraction with Singapore-localized signals."""

from __future__ import annotations

import os
import re
from typing import Dict, List

from app.utils.llm import run_openai_json


def _fallback_signals(company: str, title: str, snippets: List[str]) -> Dict[str, List[str] | str]:
    # Keep a deterministic fallback so strategy generation still has context.
    shortlist = [snippet.strip() for snippet in snippets if snippet.strip()][:3]
    if not shortlist:
        shortlist = [
            f"{company} appears active in Singapore hiring for {title}.",
            f"Look for recent {company} product and partnership announcements in Singapore.",
        ]
    return {
        "market": "Singapore",
        "signals": shortlist,
    }


def _fetch_search_snippets(company: str, title: str) -> List[str]:
    api_key = os.getenv("TINYFISH_API_KEY", "").strip()
    if not api_key:
        return []
    try:
        from tinyfish import TinyFish  # type: ignore

        client = TinyFish(api_key=api_key)
        snippets: List[str] = []
        try:
            query = f"{company} Singapore internship {title} product initiative hiring"
            response = client.search.query(query=query, location="Singapore", language="en")
            for result in response.results or []:
                text = " ".join(
                    [
                        str(result.title or "").strip(),
                        str(result.snippet or "").strip(),
                    ]
                ).strip()
                text = re.sub(r"\s+", " ", text)
                if text:
                    snippets.append(text)
        finally:
            client.close()
        return snippets[:8]
    except Exception:
        return []


def get_company_intel(company: str, title: str) -> Dict[str, List[str] | str]:
    safe_company = (company or "Unknown").strip() or "Unknown"
    safe_title = (title or "role").strip() or "role"
    snippets = _fetch_search_snippets(safe_company, safe_title)
    fallback = _fallback_signals(safe_company, safe_title, snippets)

    system_prompt = """You extract company intelligence for outreach.
Return STRICT JSON:
{
  "market": "Singapore",
  "signals": [string]
}
Rules:
- Focus on recent initiatives, products, hiring momentum, partnerships, or strategic themes.
- Keep each signal under 160 characters.
- Do not invent facts not implied by snippets.
- Return 2-4 signals.
"""
    user_prompt = str(
        {
            "company": safe_company,
            "target_role": safe_title,
            "market": "Singapore",
            "snippets": snippets,
        }
    )
    try:
        parsed = run_openai_json(system_prompt, user_prompt)
        signals = [str(item).strip() for item in parsed.get("signals", []) if str(item).strip()]
        if not signals:
            return fallback
        return {
            "market": "Singapore",
            "signals": signals[:4],
        }
    except Exception:
        return fallback
