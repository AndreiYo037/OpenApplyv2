"""Evaluation route definitions."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import FinalOutput, JobInput
from app.services.decision_engine import evaluate_job

router = APIRouter()


@router.post("/evaluate", response_model=FinalOutput)
def evaluate(payload: JobInput) -> FinalOutput:
    """Evaluate one job and return final decision output."""
    try:
        result = evaluate_job(
            job_text=payload.job_text,
            user_profile=payload.user_profile.model_dump(),
        )
        return FinalOutput.model_validate(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid input: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {exc}") from exc
