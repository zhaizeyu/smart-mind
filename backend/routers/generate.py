from __future__ import annotations

import json
import logging
import re
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from services.ai_client import AIClient, get_ai_client

logger = logging.getLogger("mindflow.generate")
router = APIRouter(prefix="/generate", tags=["generate"])


class GenerateRequest(BaseModel):
    topic: str = Field(..., description="当前节点的问题")
    answer: str = Field("", description="当前节点已知的回答")
    count: int = Field(2, ge=1, le=5, description="需要生成的子问题数量")


class GeneratedNode(BaseModel):
    question: str


class GenerateResponse(BaseModel):
    questions: list[GeneratedNode]


PROMPT_TEMPLATE = (
    "你是一位善于发散的思维导图助手，请根据当前节点生成 {count} 个子问题。"
    "要求：\n"
    "1. 子问题要与当前主题紧密相关，但角度互相不同。\n"
    "2. 每个问题使用简洁的一句话，保持原语言。\n"
    "3. 最终只输出 JSON 数组，每个元素形如 {{\"question\": \"...\"}}。"
    "\n\n当前问题：{topic}\n当前回答：{answer}\n"
)


@router.post("", response_model=GenerateResponse)
async def generate_children(payload: GenerateRequest, client: AIClient = Depends(get_ai_client)):
    logger.info("Generating %s child questions for '%s'", payload.count, payload.topic)
    prompt = PROMPT_TEMPLATE.format(count=payload.count, topic=payload.topic, answer=payload.answer or "暂无")
    raw = await client.ask(prompt)
    logger.debug("Raw generation response: %s", raw)
    questions: list[GeneratedNode] = []
    try:
        data = extract_json_block(raw)
        parsed = json.loads(data)
        if isinstance(parsed, list):
            for item in parsed:
                question = item.get("question")
                if question:
                    questions.append(GeneratedNode(question=question.strip()))
    except Exception:  # noqa: BLE001
        logger.warning("Failed to parse generation response, fallback to line split")
        for line in raw.splitlines():
            line = line.strip("-*  \t")
            if line:
                questions.append(GeneratedNode(question=line))
    if len(questions) > payload.count:
        questions = questions[:payload.count]
    logger.info("Generated %s child questions", len(questions))
    return GenerateResponse(questions=questions)


def extract_json_block(text: str) -> str:
    data = text.strip()
    block = _CODE_BLOCK_PATTERN.search(data)
    if block:
        data = block.group(1).strip()
    if data.lower().startswith("json"):
        parts = data.split("\n", 1)
        if len(parts) > 1:
            data = parts[1].strip()
    return data


_CODE_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
