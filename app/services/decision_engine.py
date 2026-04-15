"""Decision engine service wrapper."""

from __future__ import annotations

from typing import Any, Dict

from app.services.orchestrator import run_pipeline


def evaluate_job(job_text: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate one CV + job into continuous winnability score output."""
    return run_pipeline(
        {
            "job_text": job_text,
            "user_profile": user_profile if isinstance(user_profile, dict) else {},
        }
    )
