from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "mindmap.json"
DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
if not DATA_PATH.exists():
    DATA_PATH.write_text("[]", encoding="utf-8")

router = APIRouter(prefix="/mindmap", tags=["mindmap"])


class NodePosition(BaseModel):
    x: float
    y: float


class MindNode(BaseModel):
    id: str
    parentId: str | None = None
    question: str
    answer: str | None = None
    children: list["MindNode"] = Field(default_factory=list)
    position: NodePosition
    createdAt: str
    updatedAt: str


MindNode.model_rebuild()


class MindMapPayload(BaseModel):
    nodes: list[MindNode] = Field(default_factory=list)


@router.get("", response_model=MindMapPayload)
async def fetch_mindmap() -> MindMapPayload:
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="mindmap 数据损坏，请手动修复 backend/data/mindmap.json")
    return MindMapPayload(nodes=data)


@router.post("", response_model=dict)
async def save_mindmap(payload: MindMapPayload) -> dict[str, Any]:
    DATA_PATH.write_text(json.dumps([node.model_dump() for node in payload.nodes], ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "ok"}
