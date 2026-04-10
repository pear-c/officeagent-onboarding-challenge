"""Claude Agent SDK 어댑터."""

from typing import AsyncIterator

from app.llm.provider import LLMProvider, LLMResponse


class ClaudeProvider(LLMProvider):
    """claude-agent-sdk를 통한 Claude 모델 호출.

    사용 패턴:
        from claude_agent_sdk import query, ClaudeAgentOptions
        async for msg in query(prompt=..., options=ClaudeAgentOptions(...)):
            ...
    """

    def __init__(self, model: str = "claude-sonnet-4-6"):
        self._model = model

    async def generate(
        self,
        system: str,
        user: str,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Claude Agent SDK로 단일 응답 생성."""
        # TODO: claude_agent_sdk.query() 호출 구현
        # json_mode=True 시 ClaudeAgentOptions에 output_format 설정
        raise NotImplementedError("03-query 단계에서 구현")

    async def stream(
        self,
        system: str,
        user: str,
    ) -> AsyncIterator[str]:
        """Claude Agent SDK로 스트리밍 생성."""
        # TODO: claude_agent_sdk.query() async for 구현
        raise NotImplementedError("03-query 단계에서 구현")
        yield  # AsyncIterator 타입 힌트 충족용
