"""Codex CLI 어댑터."""

from typing import AsyncIterator

from app.llm.provider import LLMProvider, LLMResponse


class CodexProvider(LLMProvider):
    """Codex CLI (subprocess)를 통한 OpenAI 모델 호출."""

    def __init__(self, model: str = "codex"):
        self._model = model

    async def generate(
        self,
        system: str,
        user: str,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Codex CLI subprocess로 단일 응답 생성."""
        # TODO: asyncio.create_subprocess_exec("codex", ...) 구현
        raise NotImplementedError("03-query 단계에서 구현")

    async def stream(
        self,
        system: str,
        user: str,
    ) -> AsyncIterator[str]:
        """Codex CLI subprocess로 스트리밍 생성."""
        # TODO: subprocess stdout을 line 단위로 yield
        raise NotImplementedError("03-query 단계에서 구현")
        yield
