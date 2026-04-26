from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.chat_service import create_session, process_step

router = APIRouter()


class StepRequest(BaseModel):
    session_id: str
    step: int
    answer: str


@router.post("/start")
async def start_chat():
    """Initialize a new chat session and return the first question."""
    return create_session()


@router.post("/step")
async def chat_step(body: StepRequest):
    """Accept the user's answer for the current step and return the next."""
    try:
        return process_step(body.session_id, body.step, body.answer)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
