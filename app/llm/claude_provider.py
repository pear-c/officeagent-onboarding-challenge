"""Claude Agent SDK 어댑터."""

import json
import logging
import time
from typing import AsyncIterator

from claude_agent_sdk import (
    AssistantMessage,
    CLINotFoundError,
    ClaudeAgentOptions,
    ProcessError,
    ResultMessage,
    StreamEvent,
    TextBlock,
    query,
)

from app.llm.provider import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

# 답변 JSON 스키마 — output_format으로 구조화 출력 강제
ANSWER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "sources": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "chunk_id": {"type": "integer"},
                },
                "required": ["file", "chunk_id"],
            },
        },
        "answerable": {"type": "boolean"},
    },
    "required": ["answer", "sources", "answerable"],
}


class ClaudeProvider(LLMProvider):
    """claude-agent-sdk를 통한 Claude 모델 호출."""

    def __init__(self, model: str = "claude-sonnet-4-6"):
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
        """Claude Agent SDK로 단일 응답 생성."""
        start = time.time()
        options = self._build_options(system, json_mode)

        try:
            result_text = ""
            async for msg in query(prompt=user, options=options):
                if isinstance(msg, AssistantMessage):
                    result_text = self._extract_text(msg)
                elif isinstance(msg, ResultMessage):
                    # structured_output이 있으면 우선 사용
                    if msg.structured_output is not None:
                        result_text = (
                            json.dumps(msg.structured_output, ensure_ascii=False)
                            if not isinstance(msg.structured_output, str)
                            else msg.structured_output
                        )
                    elif msg.result:
                        result_text = msg.result

                    # max_turns 도달은 정상 동작 (의도적으로 1턴만 요청)
                    if msg.is_error and not result_text:
                        errors = msg.errors or []
                        is_max_turns = any("maximum number of turns" in e.lower() for e in errors)
                        if not is_max_turns:
                            raise RuntimeError(f"Claude 응답 오류: {'; '.join(errors)}")

            latency_ms = int((time.time() - start) * 1000)
            logger.info("Claude generate 완료: %d자, %dms", len(result_text), latency_ms)

            return LLMResponse(
                text=result_text,
                model=self._model,
                latency_ms=latency_ms,
            )

        except CLINotFoundError:
            raise RuntimeError(
                "Claude CLI를 찾을 수 없습니다. "
                "'claude' 명령이 PATH에 있는지 확인하세요."
            )
        except ProcessError as e:
            raise RuntimeError(f"Claude 프로세스 오류: {e}")

    async def stream(
        self,
        system: str,
        user: str,
    ) -> AsyncIterator[str]:
        """Claude Agent SDK로 스트리밍 생성."""
        options = self._build_options(system, json_mode=False)

        try:
            async for msg in query(prompt=user, options=options):
                if isinstance(msg, AssistantMessage):
                    text = self._extract_text(msg)
                    if text:
                        yield text
                elif isinstance(msg, ResultMessage):
                    # max_turns 도달은 정상 동작
                    if msg.is_error:
                        errors = msg.errors or []
                        is_max_turns = any("maximum number of turns" in e.lower() for e in errors)
                        if not is_max_turns:
                            raise RuntimeError(f"Claude 스트리밍 오류: {'; '.join(errors)}")

        except CLINotFoundError:
            raise RuntimeError(
                "Claude CLI를 찾을 수 없습니다. "
                "'claude' 명령이 PATH에 있는지 확인하세요."
            )
        except ProcessError as e:
            raise RuntimeError(f"Claude 프로세스 오류: {e}")

    def _build_options(self, system: str, json_mode: bool) -> ClaudeAgentOptions:
        """공통 옵션 빌더."""
        output_format = None
        if json_mode:
            output_format = {"type": "json_schema", "schema": ANSWER_JSON_SCHEMA}

        return ClaudeAgentOptions(
            system_prompt=system,
            model=self._model,
            max_turns=2,
            allowed_tools=[],
            output_format=output_format,
            permission_mode="auto",
        )

    @staticmethod
    def _extract_text(msg: AssistantMessage) -> str:
        """AssistantMessage에서 TextBlock 텍스트 추출."""
        parts = []
        for block in msg.content:
            if isinstance(block, TextBlock):
                parts.append(block.text)
        return "".join(parts)
