"""Ollama 어댑터 — 로컬 LLM (Qwen3 등) 호출."""

import json
import logging
import re
import time
from typing import AsyncIterator

import httpx

from app.llm.provider import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

# Qwen3 Thinking 모드 출력 제거용 패턴
_THINK_PATTERN = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


class OllamaProvider(LLMProvider):
    """Ollama REST API를 통한 로컬 LLM 호출."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3:8b",
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model

    @property
    def model_name(self) -> str:
        return self._model

    async def generate(
        self,
        system: str,
        user: str,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Ollama /api/chat 엔드포인트로 단일 응답 생성."""
        start = time.time()

        payload: dict = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user + "\n/no_think"},
            ],
            "stream": False,
            "options": {
                "num_predict": max_tokens,
            },
        }
        if json_mode:
            payload["format"] = "json"

        timeout = httpx.Timeout(timeout=300.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        text = data.get("message", {}).get("content", "")
        text = _THINK_PATTERN.sub("", text).strip()
        latency_ms = int((time.time() - start) * 1000)
        logger.info("Ollama generate 완료: %d자, %dms", len(text), latency_ms)

        return LLMResponse(
            text=text,
            model=self._model,
            latency_ms=latency_ms,
            raw=data,
        )

    async def stream(
        self,
        system: str,
        user: str,
    ) -> AsyncIterator[str]:
        """Ollama /api/chat 스트리밍."""
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user + "\n/no_think"},
            ],
            "stream": True,
        }

        timeout = httpx.Timeout(timeout=300.0, connect=10.0)
        in_think_block = False

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if "<think>" in token:
                            in_think_block = True
                        if in_think_block:
                            if "</think>" in token:
                                in_think_block = False
                            continue
                        if token:
                            yield token
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
