"""LLMProvider 추상 인터페이스 — Claude/Codex 1줄 swap 가능."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass(frozen=True)
class LLMResponse:
    """LLM 응답 결과 (불변)."""
    text: str
    model: str
    latency_ms: int
    raw: dict | None = None


class LLMProvider(ABC):
    """LLM 호출 추상화. ClaudeProvider와 CodexProvider가 구현."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """모델 식별자."""
        ...

    @abstractmethod
    async def generate(
        self,
        system: str,
        user: str,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> LLMResponse:
        """단일 응답 생성."""
        ...

    @abstractmethod
    async def stream(
        self,
        system: str,
        user: str,
    ) -> AsyncIterator[str]:
        """토큰 단위 스트리밍 생성."""
        ...
