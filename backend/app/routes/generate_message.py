"""On-demand outreach message endpoint."""

from fastapi import APIRouter, HTTPException

from app.models.schemas import GenerateMessageInput, GenerateMessageOutput
from app.services.strategy_generator import generate_on_demand_message

router = APIRouter()


@router.post("/generate_message", response_model=GenerateMessageOutput)
def generate_message(payload: GenerateMessageInput) -> GenerateMessageOutput:
    try:
        result = generate_on_demand_message(
            contact_id=payload.contact_id,
            cv=payload.cv,
            job=payload.job,
            company_intel=payload.company_intel,
            contact=payload.contact,
            user_preferences=payload.user_preferences,
        )
        return GenerateMessageOutput.model_validate(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid input: {exc}") from exc
    except Exception:
        raise HTTPException(status_code=500, detail="Message generation failed.")
