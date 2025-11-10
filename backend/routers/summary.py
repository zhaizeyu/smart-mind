from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from services.ai_client import AIClient, get_ai_client

logger = logging.getLogger("mindflow.summary")
router = APIRouter(prefix="/summary", tags=["summary"])


class SummaryEntry(BaseModel):
  question: str = Field(..., description="节点问题")
  answer: str | None = Field(default=None, description="节点回答")
  depth: int = Field(default=0, ge=0, description="节点层级，根节点为 0")


class SummaryRequest(BaseModel):
  topic: str = Field(..., description="当前节点标题/问题")
  entries: list[SummaryEntry] = Field(default_factory=list, description="节点以及子节点内容")


class SummaryResponse(BaseModel):
  summary: str


def build_prompt(payload: SummaryRequest) -> str:
  lines: list[str] = []
  for entry in payload.entries:
    indent = "  " * entry.depth
    answer_text = entry.answer if entry.answer else "暂无回答"
    lines.append(f"{indent}- 问题：{entry.question}\n{indent}  回答：{answer_text}")
  context = "\n".join(lines) if lines else "（暂无内容）"
  prompt = (
    "你是一名知识整理助手，请阅读以下节点及其子节点的问题和回答，将核心信息压缩成一段摘要。"
    "摘要应保持原语言，突出关键要点，可用短段落或要点形式，长度不超过 200 字。"
    f"\n\n当前节点：{payload.topic}\n\n原始内容：\n{context}"
  )
  return prompt


@router.post("", response_model=SummaryResponse)
async def summarize_nodes(payload: SummaryRequest, client: AIClient = Depends(get_ai_client)):
    logger.info("Summarizing topic='%s' entries=%s", payload.topic, len(payload.entries))
    prompt = build_prompt(payload)
    answer = await client.ask(prompt)
    logger.info("Summary generated for topic='%s'", payload.topic)
    return SummaryResponse(summary=answer)
