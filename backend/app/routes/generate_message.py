"""On-demand message generation endpoint."""

from fastapi import APIRouter, HTTPException

from app.models.schemas import GenerateMessageInput, GenerateMessageOutput
from app.services.strategy_generator import generate_on_demand_message

router = APIRouter()


@router.post("/generate_message", response_model=GenerateMessageOutput)
def generate_message(payload: GenerateMessageInput) -> GenerateMessageOutput:
    try:
        result = generate_on_demand_message(
            payload.cv,
            payload.job,
            payload.company_intel,
            payload.contact.model_dump(),
            payload.user_preferences,
        )
        return GenerateMessageOutput.model_validate(result)
    except Exception:
        raise HTTPException(status_code=500, detail="Message generation failed.")

