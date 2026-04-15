"""Job text parsing utilities.

This module focuses on lightweight extraction from raw job description text.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List


KNOWN_SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "go",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "machine learning",
    "deep learning",
    "data analysis",
    "nlp",
    "react",
    "django",
    "flask",
    "fastapi",
    "node.js",
    "git",
}

PHRASE_KEYWORDS = [
    "machine learning",
    "deep learning",
    "data science",
    "data analysis",
    "software engineering",
    "backend development",
    "cloud computing",
    "distributed systems",
    "product management",
]

STOPWORDS = {
    "the",
    "and",
    "with",
    "for",
    "that",
    "this",
    "will",
    "you",
    "our",
    "are",
    "from",
    "have",
    "has",
    "your",
    "their",
    "into",
    "about",
    "team",
    "work",
    "role",
    "job",
    "company",
}


def _extract_title(text: str) -> str:
    title_patterns = [
        r"(?:job\s*title|position|role)\s*[:\-]\s*([^\n|]+)",
        r"^([A-Z][A-Za-z0-9\s\-/]{4,80})\n",
    ]
    for pattern in title_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    return "Unknown"


def _extract_company(text: str) -> str:
    company_patterns = [
        r"(?:company|organization|employer)\s*[:\-]\s*([^\n|]+)",
        r"(?:at|join)\s+([A-Z][A-Za-z0-9&.,\-\s]{2,60})",
    ]
    for pattern in company_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().rstrip(".")
    return "Unknown"


def _extract_skills(text: str) -> List[str]:
    normalized = text.lower()
    found = [skill for skill in KNOWN_SKILLS if skill in normalized]
    return sorted(set(found))


def _extract_keywords(text: str, limit: int = 12) -> List[str]:
    normalized = text.lower()
    keywords = [phrase for phrase in PHRASE_KEYWORDS if phrase in normalized]

    tokens = re.findall(r"[a-zA-Z][a-zA-Z\+\#\.]{2,}", normalized)
    token_counts = Counter(token for token in tokens if token not in STOPWORDS)
    keywords.extend([token for token, _ in token_counts.most_common(limit)])

    deduped: List[str] = []
    for item in keywords:
        if item not in deduped:
            deduped.append(item)
    return deduped[:limit]


def parse_job_text(job_text: str) -> Dict[str, object]:
    """Parse raw job text into structured fields.

    Args:
        job_text: Raw text from a single job description.

    Returns:
        Structured dictionary with title, company, skills, keywords, and full text.
    """
    safe_text = (job_text or "").strip()
    if not safe_text:
        return {
            "title": "Unknown",
            "company": "Unknown",
            "skills": [],
            "keywords": [],
            "description": "",
        }

    return {
        "title": _extract_title(safe_text),
        "company": _extract_company(safe_text),
        "skills": _extract_skills(safe_text),
        "keywords": _extract_keywords(safe_text),
        "description": safe_text,
    }
