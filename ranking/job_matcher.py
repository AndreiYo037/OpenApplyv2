"""Job-to-profile fit scoring."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, Iterable


def _normalize_tokens(text: str) -> Counter:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9\+\#\.]{1,}", text.lower())
    return Counter(tokens)


def _jaccard_similarity(a: Iterable[str], b: Iterable[str]) -> float:
    set_a = set(a)
    set_b = set(b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def _cosine_similarity(text_a: str, text_b: str) -> float:
    vec_a = _normalize_tokens(text_a)
    vec_b = _normalize_tokens(text_b)
    if not vec_a or not vec_b:
        return 0.0

    common = set(vec_a.keys()) & set(vec_b.keys())
    numerator = sum(vec_a[token] * vec_b[token] for token in common)
    denom_a = math.sqrt(sum(value * value for value in vec_a.values()))
    denom_b = math.sqrt(sum(value * value for value in vec_b.values()))
    if denom_a == 0 or denom_b == 0:
        return 0.0
    return numerator / (denom_a * denom_b)


def _build_profile_text(user_profile: Dict[str, object]) -> str:
    skills = " ".join(str(item) for item in user_profile.get("skills", []))
    experience = str(user_profile.get("experience", ""))
    education = str(user_profile.get("education", ""))
    projects = " ".join(str(item) for item in user_profile.get("projects", []))
    return " ".join([skills, experience, education, projects]).strip()


def compute_job_fit(job: Dict[str, object], user_profile: Dict[str, object]) -> float:
    """Compute a normalized fit score between one job and one user profile."""
    job_skills = [str(skill).lower() for skill in job.get("skills", [])]
    user_skills = [str(skill).lower() for skill in user_profile.get("skills", [])]
    keyword_overlap = _jaccard_similarity(job_skills, user_skills)

    job_description = str(job.get("description", ""))
    user_profile_text = _build_profile_text(user_profile)
    semantic_similarity = _cosine_similarity(job_description, user_profile_text)

    score = 0.6 * keyword_overlap + 0.4 * semantic_similarity
    return max(0.0, min(score, 1.0))
