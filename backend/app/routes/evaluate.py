"""Evaluation endpoint."""

from fastapi import APIRouter, HTTPException

from app.models.schemas import FinalOutput, UserInput
from app.services.decision_engine import evaluate_job

router = APIRouter()


@router.post("/evaluate", response_model=FinalOutput)
def evaluate(payload: UserInput) -> FinalOutput:
    try:
        result = evaluate_job(payload.job_text, payload.cv_text)
        return FinalOutput.model_validate(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid input: {exc}") from exc
    except Exception:
        raise HTTPException(status_code=500, detail="Evaluation failed due to internal processing error.")
