"""Codex CLI 어댑터 — subprocess + JSONL 파싱."""

import asyncio
import json
import logging
import time
from typing import AsyncIterator

from app.llm.provider import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class CodexProvider(LLMProvider):
    """Codex CLI (subprocess)를 통한 OpenAI 모델 호출.

    `codex exec --json` 명령으로 JSONL 출력을 파싱한다.
    ChatGPT 계정 기반이라 별도 모델 지정 없이 기본 모델 사용.
    """

    def __init__(self, model: str = "codex"):
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
        """Codex CLI subprocess로 단일 응답 생성."""
        start = time.time()
        prompt = self._build_prompt(system, user, json_mode)

        try:
            proc = await asyncio.create_subprocess_exec(
                "codex", "exec", "--json", prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=60,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Codex CLI를 찾을 수 없습니다. "
                "'codex' 명령이 PATH에 있는지 확인하세요."
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError("Codex CLI 응답 시간 초과 (60초)")

        if proc.returncode != 0:
            err_msg = stderr.decode().strip() if stderr else "알 수 없는 오류"
            raise RuntimeError(f"Codex CLI 오류 (exit={proc.returncode}): {err_msg}")

        result_text = self._parse_jsonl(stdout.decode())
        latency_ms = int((time.time() - start) * 1000)
        logger.info("Codex generate 완료: %d자, %dms", len(result_text), latency_ms)

        return LLMResponse(
            text=result_text,
            model=self._model,
            latency_ms=latency_ms,
        )

    async def stream(
        self,
        system: str,
        user: str,
    ) -> AsyncIterator[str]:
        """Codex CLI subprocess stdout을 line 단위로 스트리밍."""
        prompt = self._build_prompt(system, user, json_mode=False)

        try:
            proc = await asyncio.create_subprocess_exec(
                "codex", "exec", "--json", prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Codex CLI를 찾을 수 없습니다. "
                "'codex' 명령이 PATH에 있는지 확인하세요."
            )

        assert proc.stdout is not None
        async for line_bytes in proc.stdout:
            line = line_bytes.decode().strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            # item.completed 이벤트에서 텍스트 추출
            if event.get("type") == "item.completed":
                item = event.get("item", {})
                text = item.get("text", "")
                if text:
                    yield text

            # 에러 이벤트 처리
            if event.get("type") == "error":
                msg = event.get("message", "알 수 없는 오류")
                raise RuntimeError(f"Codex 스트리밍 오류: {msg}")

        await proc.wait()

    @staticmethod
    def _build_prompt(system: str, user: str, json_mode: bool) -> str:
        """system + user를 하나의 프롬프트로 합성."""
        parts = [f"[시스템 지시]\n{system}"]
        if json_mode:
            parts.append("\n반드시 JSON 형식으로만 응답하세요.")
        parts.append(f"\n[질문]\n{user}")
        return "\n".join(parts)

    @staticmethod
    def _parse_jsonl(output: str) -> str:
        """JSONL 출력에서 item.completed 텍스트 추출."""
        result_parts = []
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("type") == "item.completed":
                item = event.get("item", {})
                text = item.get("text", "")
                if text:
                    result_parts.append(text)

            if event.get("type") == "error":
                msg = event.get("message", "알 수 없는 오류")
                raise RuntimeError(f"Codex 응답 오류: {msg}")

        return "\n".join(result_parts)
