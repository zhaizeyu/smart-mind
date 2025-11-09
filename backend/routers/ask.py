from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from services.ai_client import AIClient, get_ai_client

router = APIRouter(prefix="/ask", tags=["ask"])


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="需要发送给模型的问题")


class AskResponse(BaseModel):
    answer: str


@router.post("", response_model=AskResponse)
async def ask_ai(payload: AskRequest, client: AIClient = Depends(get_ai_client)):
    answer = await client.ask(payload.question)
    return AskResponse(answer=answer)
