"""Job fit scoring service."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Set

SKILL_PATTERNS = {
    "python": r"\bpython\b",
    "pandas": r"\bpandas\b",
    "numpy": r"\bnumpy\b",
    "scikit-learn": r"\bscikit(?:-|\s)?learn\b",
    "machine learning": r"\bmachine learning\b",
    "sql": r"\bsql\b",
    "java": r"\bjava\b",
    "javascript": r"\bjavascript\b",
    "typescript": r"\btypescript\b",
    "react": r"\breact\b",
    "node.js": r"\bnode(?:\.js)?\b",
    "aws": r"\baws\b|\bamazon web services\b",
    "docker": r"\bdocker\b",
    "kubernetes": r"\bkubernetes\b",
}

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "your",
    "our",
    "you",
    "are",
    "role",
    "team",
    "will",
    "have",
    "has",
    "job",
    "work",
}


def _normalize_terms(values: Iterable[str]) -> Set[str]:
    return {str(v).strip().lower() for v in values if str(v).strip()}


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9\+\#\.]{1,}", (text or "").lower())


def _jaccard_similarity(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _cosine_similarity(text_a: str, text_b: str) -> float:
    tokens_a = Counter(_tokenize(text_a))
    tokens_b = Counter(_tokenize(text_b))
    if not tokens_a or not tokens_b:
        return 0.0

    common = set(tokens_a) & set(tokens_b)
    numerator = sum(tokens_a[token] * tokens_b[token] for token in common)
    norm_a = math.sqrt(sum(value * value for value in tokens_a.values()))
    norm_b = math.sqrt(sum(value * value for value in tokens_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return numerator / (norm_a * norm_b)


def _extract_hard_requirements(description: str) -> Set[str]:
    lines = [line.strip() for line in (description or "").splitlines() if line.strip()]
    hard_lines = [
        line
        for line in lines
        if re.search(r"\b(must|required|requirement|mandatory|minimum)\b", line, flags=re.IGNORECASE)
    ]

    extracted: Set[str] = set()
    for line in hard_lines:
        chunks = re.split(r"[,;•\-]", line)
        for chunk in chunks:
            normalized = " ".join(chunk.lower().split())
            # Keep concise requirement phrases, skip long prose lines.
            if 2 <= len(normalized.split()) <= 8:
                extracted.add(normalized)
    return extracted


def _build_profile_text(profile: Dict[str, Any]) -> str:
    return " ".join(
        [
            " ".join(str(item) for item in profile.get("skills", [])),
            str(profile.get("experience_summary", "")),
            " ".join(str(item) for item in profile.get("projects", [])),
            " ".join(str(item) for item in profile.get("roles", [])),
            str(profile.get("seniority_level", "")),
        ]
    ).strip()


def _extract_skills_from_text(text: str) -> Set[str]:
    lowered = (text or "").lower()
    matches: Set[str] = set()
    for normalized, pattern in SKILL_PATTERNS.items():
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            matches.add(normalized)
    return matches


def _weak_text_overlap_score(a: str, b: str) -> float:
    tokens_a = {t for t in _tokenize(a) if len(t) > 2 and t not in STOPWORDS}
    tokens_b = {t for t in _tokenize(b) if len(t) > 2 and t not in STOPWORDS}
    return _jaccard_similarity(tokens_a, tokens_b)


def compute_job_fit(job: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    description = str(job.get("description", ""))
    profile_text = _build_profile_text(profile)

    hard_requirements = _normalize_terms(job.get("hard_requirements", []))
    job_skills = _normalize_terms(job.get("skills", []))
    profile_skills = _normalize_terms(profile.get("skills", []))
    # Treat hard requirements as primary job skills for overlap scoring.
    job_skills |= hard_requirements
    job_skills |= _extract_skills_from_text(" ".join(hard_requirements))
    job_skills |= _extract_skills_from_text(description)
    profile_skills |= _extract_skills_from_text(profile_text)
    overlap = job_skills & profile_skills
    missing_skills = job_skills - profile_skills

    job_keywords = _normalize_terms(job.get("keywords", []))
    profile_tokens = set(_tokenize(profile_text))
    profile_tokens |= _extract_skills_from_text(profile_text)

    skill_overlap_score = _jaccard_similarity(job_skills, profile_skills)
    keyword_similarity = _jaccard_similarity(job_keywords, profile_tokens)
    lexical_similarity = _cosine_similarity(description, profile_text)
    weak_overlap = _weak_text_overlap_score(description, profile_text)

    # Weighted score that still returns a signal even when parser output is partial.
    base_score = 0.45 * skill_overlap_score + 0.20 * keyword_similarity + 0.25 * lexical_similarity + 0.10 * weak_overlap

    inferred_hard_requirements = _extract_hard_requirements(description)
    hard_requirements |= inferred_hard_requirements
    missing_hard_count = 0
    for requirement in hard_requirements:
        req_tokens = set(_tokenize(requirement))
        if req_tokens and req_tokens.isdisjoint(profile_tokens):
            missing_hard_count += 1

    hard_penalty = min(0.20, 0.06 * missing_hard_count)
    final = max(0.0, min(1.0, base_score - hard_penalty))
    if weak_overlap > 0.0:
        # Prevent false-zero or near-zero results when raw text clearly overlaps.
        final = max(final, 0.08)

    gaps = sorted(missing_skills)[:8]
    if missing_hard_count > 0:
        gaps.append(f"missing_hard_requirements:{missing_hard_count}")

    return {
        "job_fit_score": round(final, 4),
        "strengths": sorted(overlap)[:8],
        "gaps": gaps,
    }
