"""Final score combiner for continuous scoring engine."""

from __future__ import annotations


def combine_final_score(cv_score: float, contact_quality: float) -> float:
    """Combine CV and contact quality into FINAL_SCORE (0-100)."""
    score = 0.55 * float(cv_score or 0.0) + 0.45 * float(contact_quality or 0.0)
    return round(max(0.0, min(score, 100.0)), 2)
