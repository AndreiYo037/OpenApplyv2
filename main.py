"""Entrypoint for the single-job decision engine."""

from __future__ import annotations

from typing import Dict

from ranking.decision_engine import evaluate_job


def run_decision_engine(input_data: Dict[str, object]) -> Dict[str, object]:
    """Execute decision engine with required input schema."""
    job_text = str(input_data.get("job_text", ""))
    user_profile = input_data.get("user_profile", {})
    if not isinstance(user_profile, dict):
        user_profile = {}

    result = evaluate_job(job_text=job_text, user_profile=user_profile)
    return result
