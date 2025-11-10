import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from services.ai_client import AIClient, get_ai_client

logger = logging.getLogger("smartmind.ask")
router = APIRouter(prefix="/ask", tags=["ask"])


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="需要发送给模型的问题")


class AskResponse(BaseModel):
    answer: str


@router.post("", response_model=AskResponse)
async def ask_ai(payload: AskRequest, client: AIClient = Depends(get_ai_client)):
    logger.info("Received question len=%s", len(payload.question))
    answer = await client.ask(payload.question)
    logger.info("Completed question")
    return AskResponse(answer=answer)
