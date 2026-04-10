"""Ingestion 비즈니스 로직 — 텍스트 추출 → 청킹 → 임베딩 → 저장."""

from __future__ import annotations

import hashlib
import logging
import time
from typing import TYPE_CHECKING

from app.cache.redis_cache import RedisCache
from app.chunking.recursive import Chunk
from app.chunking.router import chunk_document
from app.config import settings
from app.embedding.embedder import Embedder
from app.extraction.text_extractor import get_extractor
from app.schemas import DocumentInfo
from app.vectorstore.chroma_store import ChromaStore

if TYPE_CHECKING:
    from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class IngestService:
    """문서 수집 파이프라인 조율."""

    def __init__(
        self,
        embedder: Embedder,
        chroma: ChromaStore,
        redis: RedisCache,
        cache_service: CacheService | None = None,
    ):
        self._embedder = embedder
        self._chroma = chroma
        self._redis = redis
        self._cache_service = cache_service

    async def ingest(self, filename: str, content: bytes) -> DocumentInfo:
        """문서 수집 파이프라인 실행.

        ① 해시 비교 → ② 텍스트 추출 → ③ 청킹 → ④ 임베딩 → ⑤ 저장 → ⑥ 해시 저장
        """
        total_start = time.time()

        # ① SHA-256 해시 계산 + 중복 검사
        content_hash = hashlib.sha256(content).hexdigest()
        existing_hash = await self._redis.get_document_hash(filename)

        if existing_hash == content_hash:
            logger.info("문서 변경 없음 (이미 최신): %s", filename)
            return self._build_existing_doc_info(filename, content_hash, len(content))

        logger.info("문서 수집 시작: %s (%d bytes, hash=%s…)", filename, len(content), content_hash[:12])

        # ② 텍스트 추출
        step_start = time.time()
        extractor = get_extractor(filename)
        text = extractor.extract(content, filename)
        logger.info("텍스트 추출 완료: %d자 (%.2f초)", len(text), time.time() - step_start)

        if not text.strip():
            raise ValueError("업로드된 파일에서 텍스트를 추출할 수 없습니다.")

        # ③ 청킹
        step_start = time.time()
        chunks = chunk_document(
            text, filename,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
        logger.info("청킹 완료: %d chunks (%.2f초)", len(chunks), time.time() - step_start)

        if not chunks:
            raise ValueError("업로드된 파일에서 청크를 생성할 수 없습니다.")

        # ④ 임베딩
        step_start = time.time()
        chunk_texts = [c.text for c in chunks]
        embeddings = self._embedder.embed(chunk_texts)
        logger.info("임베딩 완료: %d vectors (%.2f초)", len(embeddings), time.time() - step_start)

        # ⑤ Chroma 저장 (기존 벡터 삭제 → 새 벡터 저장)
        step_start = time.time()
        if existing_hash is not None:
            # 문서 변경 감지 → 관련 캐시 무효화 (D26)
            if self._cache_service is not None:
                await self._cache_service.invalidate_by_document(filename)
            self._chroma.delete_by_document(filename)

        ids = [f"{filename}::{c.chunk_id}" for c in chunks]
        metadatas = self._build_metadatas(chunks, content_hash, len(content))
        self._chroma.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=metadatas,
        )
        logger.info("Chroma 저장 완료 (%.2f초)", time.time() - step_start)

        # ⑥ Redis에 문서 해시 저장
        await self._redis.set_document_hash(filename, content_hash)

        total_elapsed = time.time() - total_start
        logger.info("문서 수집 완료: %s (%d chunks, %.2f초)", filename, len(chunks), total_elapsed)

        return DocumentInfo(
            filename=filename,
            content_hash=content_hash,
            chunk_count=len(chunks),
            file_size=len(content),
        )

    async def list_documents(self) -> list[DocumentInfo]:
        """업로드된 문서 목록 조회."""
        docs = self._chroma.list_documents()
        return [
            DocumentInfo(
                filename=d["filename"],
                content_hash=d["content_hash"],
                chunk_count=d["chunk_count"],
                file_size=d["file_size"],
            )
            for d in docs
        ]

    def _build_metadatas(
        self,
        chunks: list[Chunk],
        content_hash: str,
        file_size: int,
    ) -> list[dict]:
        """청크별 메타데이터 생성."""
        return [
            {
                "source_file": c.source_file,
                "chunk_id": c.chunk_id,
                "section": c.section,
                "start_char": c.start_char,
                "end_char": c.end_char,
                "content_hash": content_hash,
                "file_size": file_size,
            }
            for c in chunks
        ]

    def _build_existing_doc_info(
        self, filename: str, content_hash: str, file_size: int,
    ) -> DocumentInfo:
        """이미 최신인 문서의 DocumentInfo 생성 (해당 문서만 조회)."""
        chunk_count = self._chroma.get_document_chunk_count(filename)
        if chunk_count == 0:
            # Chroma에 없는 경우 (Redis 해시만 남아있는 비정상 상태) → 재수집 유도
            raise ValueError("Chroma에 해당 문서 벡터가 없습니다. 재업로드해주세요.")
        return DocumentInfo(
            filename=filename,
            content_hash=content_hash,
            chunk_count=chunk_count,
            file_size=file_size,
        )
