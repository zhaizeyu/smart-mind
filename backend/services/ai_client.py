from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Literal, Optional

import httpx
import logging
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from backend.config import load_ai_config
except ModuleNotFoundError:  # running from backend/ as working dir
    from config import load_ai_config  # type: ignore


class AISettings(BaseSettings):
    provider: Literal["echo", "http", "openai", "docker"] = Field(
        default="echo",
        description="echo|http|openai|docker",
    )
    base_url: Optional[str] = Field(default=None, description="远程 HTTP 基础地址")
    api_key: Optional[str] = Field(default=None, description="接口密钥")
    model: str = Field(default="gpt-4o-mini", description="模型名称，openai 模式必填")
    headers: Dict[str, str] = Field(default_factory=dict, description="附加 HTTP 请求头")
    timeout: float = Field(default=30.0)
    history_path: Path = Field(default=Path(__file__).resolve().parents[1] / "data" / "history.json")

    model_config = SettingsConfigDict(env_prefix="SMARTMIND_", extra="allow")


logger = logging.getLogger(__name__)


class AIClient:
    def __init__(self, settings: AISettings | None = None) -> None:
        config_overrides = load_ai_config()
        self.settings = settings or AISettings(**config_overrides)
        self.history_path = self.settings.history_path
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.history_path.exists():
            self.history_path.write_text("[]", encoding="utf-8")

    async def ask(self, question: str) -> str:
        provider = self.settings.provider
        logger.info("Dispatch question to provider=%s", provider)
        try:
            if provider == "http" and self.settings.base_url:
                return await self._request_custom_http(question)
            if provider == "openai":
                return await self._request_openai(question)
            if provider == "docker":
                return await self._request_docker_runner(question)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Provider %s failed: %s", provider, exc)
            return self._fallback(question, error=str(exc))
        logger.warning("Unknown provider '%s', falling back to echo", provider)
        return self._fallback(question)

    async def _request_custom_http(self, question: str) -> str:
        assert self.settings.base_url, "base_url must be configured for http provider"
        logger.debug("Calling custom HTTP endpoint %s", self.settings.base_url)
        async with httpx.AsyncClient(timeout=self.settings.timeout) as client:
            response = await client.post(
                self.settings.base_url,
                json={"question": question},
                headers=self.settings.headers or None,
            )
            response.raise_for_status()
            data = response.json()
            answer = data.get("answer") or data.get("content")
            if not answer:
                raise ValueError("远程服务没有返回 answer / content 字段")
            self._persist(question, answer)
            logger.info("Custom HTTP provider answered successfully")
            return answer
        raise ValueError("provider=http 需要配置 base_url")

    async def _request_openai(self, question: str) -> str:
        api_key = self.settings.api_key or ""
        if not api_key:
            raise ValueError("OpenAI 模式需要配置 api_key")
        base_url = self.settings.base_url or "https://api.openai.com/v1/chat/completions"
        logger.debug("Calling OpenAI endpoint %s model=%s", base_url, self.settings.model)
        payload = {
            "model": self.settings.model,
            "messages": [{"role": "user", "content": question}],
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", **(self.settings.headers or {})}
        async with httpx.AsyncClient(timeout=self.settings.timeout) as client:
            response = await client.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                raise ValueError("OpenAI 接口未返回 choices")
            answer = choices[0]["message"]["content"]
            self._persist(question, answer)
            logger.info("OpenAI provider answered successfully")
            return answer

    async def _request_docker_runner(self, question: str) -> str:
        base_url = self.settings.base_url or "http://localhost:12434/engines/llama.cpp/v1/chat/completions"
        logger.debug("Calling docker runner %s model=%s", base_url, self.settings.model)
        payload = {
            "model": self.settings.model,
            "messages": [{"role": "user", "content": question}],
        }
        headers = {"Content-Type": "application/json", **(self.settings.headers or {})}
        async with httpx.AsyncClient(timeout=self.settings.timeout) as client:
            response = await client.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                raise ValueError("Docker model runner 未返回 choices")
            message = choices[0].get("message") or {}
            answer = message.get("content")
            if not answer:
                raise ValueError("Docker model runner choices 缺少 message.content")
            self._persist(question, answer)
            logger.info("Docker model runner answered successfully")
            return answer

    def _fallback(self, question: str, error: str | None = None) -> str:
        if error:
            logger.error("Fallback echo due to error: %s", error)
        else:
            logger.warning("Fallback echo mode triggered without remote provider")
        answer = (
            "(本地回声模式) 您的问题是："
            f"{question}\n"
            "编辑 backend/config.toml 并设置 provider/base_url 以连接真实模型。"
        )
        if error:
            answer += f"\n远程调用失败：{error}"
        self._persist(question, answer)
        return answer

    def _persist(self, question: str, answer: str) -> None:
        record = {
            "question": question,
            "answer": answer,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        payload: list[Dict[str, Any]] = []
        try:
            payload = json.loads(self.history_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = []
        payload.append(record)
        self.history_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.debug("Persisted QA record, total=%s", len(payload))


def get_ai_client() -> AIClient:
    return AIClient()
