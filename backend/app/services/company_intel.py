"""Company intelligence extraction with Singapore-localized signals."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List

from app.utils.llm import run_openai_json


def _fallback_signals(company: str, title: str, snippets: List[str], job: Dict[str, Any]) -> Dict[str, Any]:
    # Keep a deterministic fallback so strategy generation still has context.
    shortlist = [snippet.strip() for snippet in snippets if snippet.strip()][:3]
    if not shortlist:
        shortlist = [
            f"{company} appears active in Singapore hiring for {title}.",
            f"Look for recent {company} product and partnership announcements in Singapore.",
        ]
    skills = []
    for key in ("hard_requirements", "skills", "keywords"):
        values = job.get(key, [])
        if isinstance(values, list):
            for value in values:
                text = str(value).strip()
                if text and text.lower() not in {s.lower() for s in skills}:
                    skills.append(text)
    if not skills:
        skills = ["Python", "Machine Learning", "Communication"]

    return {
        "market": "Singapore",
        "signals": shortlist,
        "job_summary": f"{company} is hiring for {title} in Singapore with a focus on role-fit delivery and local team impact.",
        "required_skills": skills[:8],
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


def get_company_intel(company: str, title: str, job: Dict[str, Any] | None = None) -> Dict[str, Any]:
    safe_company = (company or "Unknown").strip() or "Unknown"
    safe_title = (title or "role").strip() or "role"
    safe_job = job or {}
    snippets = _fetch_search_snippets(safe_company, safe_title)
    fallback = _fallback_signals(safe_company, safe_title, snippets, safe_job)

    system_prompt = """You extract company intelligence for outreach.
Return STRICT JSON:
{
  "market": "Singapore",
  "signals": [string],
  "job_summary": string,
  "required_skills": [string]
}
Rules:
- Focus on recent initiatives, products, hiring momentum, partnerships, or strategic themes.
- Keep each signal under 160 characters.
- job_summary must summarize responsibilities + team/context grounded in job + snippets.
- required_skills must list 4-8 concrete skills/tools from the job requirements (not generic fluff).
- Do not invent facts not implied by snippets.
- Return 2-4 signals.
"""
    user_prompt = str(
        {
            "company": safe_company,
            "target_role": safe_title,
            "market": "Singapore",
            "job": safe_job,
            "snippets": snippets,
        }
    )
    try:
        parsed = run_openai_json(system_prompt, user_prompt)
        signals = [str(item).strip() for item in parsed.get("signals", []) if str(item).strip()]
        if not signals:
            return fallback
        skills = [str(item).strip() for item in parsed.get("required_skills", []) if str(item).strip()]
        if not skills:
            skills = fallback["required_skills"]
        summary = str(parsed.get("job_summary", "")).strip() or str(fallback["job_summary"])
        return {
            "market": "Singapore",
            "signals": signals[:4],
            "job_summary": summary,
            "required_skills": skills[:8],
        }
    except Exception:
        return fallback
