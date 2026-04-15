"""Job fit scoring service."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List, Set


def _normalize_terms(values: List[str]) -> Set[str]:
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
    numerator = sum(tokens_a[t] * tokens_b[t] for t in common)
    norm_a = math.sqrt(sum(v * v for v in tokens_a.values()))
    norm_b = math.sqrt(sum(v * v for v in tokens_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return numerator / (norm_a * norm_b)


def _extract_hard_requirements(job_description: str) -> Set[str]:
    """Extract likely hard requirements from required/must-have statements."""
    desc = job_description or ""
    lines = [line.strip() for line in desc.splitlines() if line.strip()]
    hard_lines = [
        line
        for line in lines
        if re.search(r"\b(must|required|requirement|mandatory|minimum)\b", line, flags=re.IGNORECASE)
    ]

    extracted: Set[str] = set()
    for line in hard_lines:
        # split by commas/bullets to keep only concise requirement phrases
        chunks = re.split(r"[,;•\-]", line)
        for chunk in chunks:
            cleaned = chunk.strip().lower()
            if 2 <= len(cleaned.split()) <= 8:
                extracted.add(cleaned)
    return extracted


def _build_profile_text(user_profile: Dict[str, object]) -> str:
    skills = " ".join(str(x) for x in user_profile.get("skills", []))
    experience = str(user_profile.get("experience", ""))
    education = str(user_profile.get("education", ""))
    projects = " ".join(str(x) for x in user_profile.get("projects", []))
    return " ".join([skills, experience, education, projects]).strip()


def _embedding_similarity(_job_text: str, _profile_text: str) -> float:
    """Optional embedding similarity hook.

    Return 0.0 by default; replace with embedding provider integration if needed.
    """
    return 0.0


def compute_job_fit(job: Dict[str, object], user_profile: Dict[str, object]) -> Dict[str, object]:
    """Compute job fit score with strengths and gaps."""
    job_skills = _normalize_terms(list(job.get("skills", [])))
    profile_skills = _normalize_terms(list(user_profile.get("skills", [])))
    overlap = job_skills & profile_skills
    missing = job_skills - profile_skills

    skill_overlap_score = _jaccard_similarity(job_skills, profile_skills)

    job_keywords = _normalize_terms(list(job.get("keywords", [])))
    profile_text = _build_profile_text(user_profile)
    profile_keywords = set(_tokenize(profile_text))
    keyword_similarity = _jaccard_similarity(job_keywords, profile_keywords)

    description = str(job.get("description", ""))
    lexical_similarity = _cosine_similarity(description, profile_text)
    embed_similarity = _embedding_similarity(description, profile_text)
    semantic_similarity = 0.7 * lexical_similarity + 0.3 * embed_similarity

    base_score = 0.45 * skill_overlap_score + 0.25 * keyword_similarity + 0.30 * semantic_similarity

    # Penalize missing hard requirements.
    hard_requirements = _extract_hard_requirements(description)
    missing_hard_count = 0
    for req in hard_requirements:
        req_tokens = set(_tokenize(req))
        if req_tokens and not req_tokens.intersection(profile_keywords):
            missing_hard_count += 1

    hard_penalty = min(0.30, 0.08 * missing_hard_count)
    final_score = max(0.0, min(1.0, base_score - hard_penalty))

    strengths = sorted(overlap)[:10]
    gaps = sorted(missing)[:10]
    if missing_hard_count > 0:
        gaps.append(f"missing_hard_requirements:{missing_hard_count}")

    return {
        "job_fit_score": round(final_score, 4),
        "strengths": strengths,
        "gaps": gaps,
    }
