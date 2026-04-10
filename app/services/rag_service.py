"""RAG 파이프라인 조율 — 캐시 확인 → 검색 → 프롬프트 → LLM → 캐시 저장."""

import json
import logging
import time
from typing import AsyncIterator

from app.config import settings
from app.embedding.embedder import Embedder
from app.llm.provider import LLMProvider
from app.prompts.templates import SYSTEM_PROMPT, SYSTEM_PROMPT_STREAM, build_user_prompt
from app.schemas import QueryAnswer, SourceInfo
from app.services.cache_service import CachedAnswer, CacheService
from app.vectorstore.chroma_store import ChromaStore, SearchResult

logger = logging.getLogger(__name__)


class RAGService:
    """질의응답 파이프라인 조율."""

    def __init__(
        self,
        cache_service: CacheService,
        chroma: ChromaStore,
        embedder: Embedder,
        answer_llm: LLMProvider,
    ):
        self._cache = cache_service
        self._chroma = chroma
        self._embedder = embedder
        self._answer_llm = answer_llm

    async def answer(self, question: str) -> QueryAnswer:
        """질문 → 답변 (JSON 응답용)."""
        total_start = time.time()

        # ① 캐시 확인 (정확 → 유사)
        question_hash = CacheService.hash_question(question)
        cached = await self._check_cache(question_hash, question)
        if cached:
            return self._cached_to_answer(cached, total_start)

        # ② 질문 임베딩
        question_embedding = self._embedder.embed_query(question)

        # ③ 유사 질문 캐시
        similar = self._cache.get_similar(question_embedding)
        if similar:
            return self._cached_to_answer(similar, total_start)

        # ④ 벡터 검색
        search_results = self._chroma.search(
            query_embedding=question_embedding, top_k=settings.search_top_k,
        )
        if not search_results:
            return self._no_documents_answer(total_start)

        # ⑤ LLM 호출 + 응답 처리
        chunks = self._results_to_chunks(search_results)
        user_prompt = build_user_prompt(question, chunks)
        llm_response = await self._answer_llm.generate(
            system=SYSTEM_PROMPT, user=user_prompt, json_mode=True,
        )
        answer_data = self._parse_llm_response(llm_response.text)
        llm_model = llm_response.model
        sources = self._build_sources(answer_data, search_results)

        # ⑥ 캐시 저장
        source_files = self._extract_source_files(search_results)
        await self._save_answer_cache(
            question, question_hash, question_embedding,
            answer_data, sources, llm_model, source_files,
        )

        latency_ms = int((time.time() - total_start) * 1000)
        logger.info("RAG 답변 완료: %dms", latency_ms)

        return QueryAnswer(
            answer=answer_data.get("answer", ""),
            sources=sources,
            answerable=answer_data.get("answerable", True),
            cached=False,
            model=llm_model,
            latency_ms=latency_ms,
        )

    async def answer_stream(self, question: str) -> AsyncIterator[str]:
        """질문 → SSE 스트리밍 (sources 먼저 → 토큰 → done)."""
        total_start = time.time()

        # ① 캐시 확인
        question_hash = CacheService.hash_question(question)
        cached = await self._check_cache(question_hash, question)
        if cached:
            async for event in self._stream_cached(cached, total_start):
                yield event
            return

        # ② 질문 임베딩 + 유사 캐시
        question_embedding = self._embedder.embed_query(question)
        similar = self._cache.get_similar(question_embedding)
        if similar:
            async for event in self._stream_cached(similar, total_start):
                yield event
            return

        # ③ 벡터 검색
        search_results = self._chroma.search(
            query_embedding=question_embedding, top_k=settings.search_top_k,
        )
        if not search_results:
            async for event in self._stream_empty(total_start):
                yield event
            return

        # ④ sources 먼저 전송 (D25) + LLM 스트리밍
        chunks = self._results_to_chunks(search_results)
        yield self._sse_sources(chunks)

        accumulated_text = ""
        try:
            user_prompt = build_user_prompt(question, chunks)
            async for token in self._answer_llm.stream(
                system=SYSTEM_PROMPT_STREAM, user=user_prompt,
            ):
                accumulated_text += token
                yield self._sse_event("token", {"content": token})
        except Exception as e:
            logger.error("LLM 스트리밍 오류: %s", e)
            yield self._sse_event("error", {"message": "답변 생성 중 오류가 발생했습니다."})

        # ⑤ done 이벤트
        latency_ms = int((time.time() - total_start) * 1000)
        yield self._sse_event("done", {
            "answerable": True, "cached": False,
            "model": self._answer_llm.model_name, "latency_ms": latency_ms,
        })

        # ⑥ 캐시 저장
        source_files = self._extract_source_files(search_results)
        await self._save_stream_cache(
            question, question_hash, question_embedding,
            accumulated_text, chunks, source_files,
        )

    # ===== 스트리밍 헬퍼 (answer_stream 분리) =====

    async def _stream_cached(
        self, cached: CachedAnswer, total_start: float,
    ) -> AsyncIterator[str]:
        """캐시 히트 시 SSE 전송."""
        yield self._sse_event("sources", {"sources": cached.sources})
        yield self._sse_event("token", {"content": cached.answer})
        latency_ms = int((time.time() - total_start) * 1000)
        yield self._sse_event("done", {
            "answerable": cached.answerable, "cached": True,
            "model": cached.model, "latency_ms": latency_ms,
        })

    async def _stream_empty(self, total_start: float) -> AsyncIterator[str]:
        """문서 없을 때 SSE 전송."""
        yield self._sse_event("sources", {"sources": []})
        yield self._sse_event("token", {"content": "업로드된 문서가 없어 답변할 수 없습니다."})
        latency_ms = int((time.time() - total_start) * 1000)
        yield self._sse_event("done", {
            "answerable": False, "cached": False,
            "model": "none", "latency_ms": latency_ms,
        })

    async def _save_stream_cache(
        self, question: str, question_hash: str,
        question_embedding: list[float], accumulated_text: str,
        chunks: list[dict], source_files: list[str],
    ) -> None:
        """스트리밍 완료 후 캐시 저장 (자연어 텍스트 → answer 필드에 직접 저장)."""
        is_unanswerable = "찾을 수 없습니다" in accumulated_text
        answer_json = json.dumps({
            "answer": accumulated_text,
            "sources": [{"file": c["file"], "chunk_id": c["chunk_id"]} for c in chunks],
            "answerable": not is_unanswerable,
            "model": self._answer_llm.model_name,
        }, ensure_ascii=False)

        await self._cache.save(
            question=question, question_hash=question_hash,
            question_embedding=question_embedding,
            answer_json=answer_json, source_files=source_files,
        )

    # ===== 내부 헬퍼 =====

    async def _check_cache(
        self, question_hash: str, question: str,
    ) -> CachedAnswer | None:
        """정확 일치 캐시 확인."""
        return await self._cache.get_exact(question_hash)

    async def _save_answer_cache(
        self, question: str, question_hash: str, question_embedding: list[float],
        answer_data: dict, sources: list[SourceInfo], model: str,
        source_files: list[str],
    ) -> None:
        """JSON 응답 캐시 저장."""
        answer_json = json.dumps({
            "answer": answer_data.get("answer", ""),
            "sources": [{"file": s.file, "chunk_id": s.chunk_id} for s in sources],
            "answerable": answer_data.get("answerable", True),
            "model": model,
        }, ensure_ascii=False)
        await self._cache.save(
            question=question, question_hash=question_hash,
            question_embedding=question_embedding,
            answer_json=answer_json, source_files=source_files,
        )

    @staticmethod
    def _extract_source_files(results: list[SearchResult]) -> list[str]:
        """검색 결과에서 고유 소스 파일 목록 추출 (빈 문자열 제외)."""
        return [
            f for f in {r.metadata.get("source_file", "") for r in results} if f
        ]

    @staticmethod
    def _results_to_chunks(results: list[SearchResult]) -> list[dict]:
        """SearchResult → 프롬프트용 chunk 딕셔너리 변환."""
        return [
            {
                "file": r.metadata.get("source_file", "unknown"),
                "chunk_id": r.metadata.get("chunk_id", 0),
                "text": r.text,
            }
            for r in results
        ]

    @staticmethod
    def _parse_llm_response(text: str) -> dict:
        """LLM 응답 텍스트 → JSON 파싱."""
        text = text.strip()
        if text.startswith("```json"):
            text = text.removeprefix("```json").removesuffix("```").strip()
        elif text.startswith("```"):
            text = text.removeprefix("```").removesuffix("```").strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("LLM 응답 JSON 파싱 실패, 원본 텍스트 사용")
            return {"answer": text, "sources": [], "answerable": True}

    @staticmethod
    def _build_sources(
        answer_data: dict, search_results: list[SearchResult],
    ) -> list[SourceInfo]:
        """LLM이 인용한 출처를 SourceInfo 리스트로 변환."""
        llm_sources = answer_data.get("sources", [])
        if llm_sources:
            return [
                SourceInfo(
                    file=s.get("file", "unknown"),
                    chunk_id=s.get("chunk_id", 0),
                    text=next(
                        (r.text for r in search_results
                         if r.metadata.get("source_file") == s.get("file")
                         and r.metadata.get("chunk_id") == s.get("chunk_id")),
                        "",
                    ),
                )
                for s in llm_sources
            ]
        return [
            SourceInfo(
                file=r.metadata.get("source_file", "unknown"),
                chunk_id=r.metadata.get("chunk_id", 0),
                text=r.text[:200],
            )
            for r in search_results[:3]
        ]

    @staticmethod
    def _cached_to_answer(cached: CachedAnswer, total_start: float) -> QueryAnswer:
        """CachedAnswer → QueryAnswer 변환."""
        latency_ms = int((time.time() - total_start) * 1000)
        return QueryAnswer(
            answer=cached.answer,
            sources=[
                SourceInfo(
                    file=s.get("file", ""), chunk_id=s.get("chunk_id", 0), text="",
                )
                for s in cached.sources
            ],
            answerable=cached.answerable,
            cached=True,
            model=cached.model,
            latency_ms=latency_ms,
        )

    @staticmethod
    def _no_documents_answer(total_start: float) -> QueryAnswer:
        """문서가 없을 때 응답."""
        latency_ms = int((time.time() - total_start) * 1000)
        return QueryAnswer(
            answer="업로드된 문서가 없어 답변할 수 없습니다.",
            sources=[], answerable=False, cached=False,
            model="none", latency_ms=latency_ms,
        )

    def _sse_sources(self, chunks: list[dict]) -> str:
        """검색 결과를 SSE sources 이벤트로 변환."""
        payload = [
            {"file": c["file"], "chunk_id": c["chunk_id"], "text": c["text"][:200]}
            for c in chunks
        ]
        return self._sse_event("sources", {"sources": payload})

    @staticmethod
    def _sse_event(event_type: str, data: dict) -> str:
        """SSE 이벤트 포맷."""
        payload = {"type": event_type, **data}
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
