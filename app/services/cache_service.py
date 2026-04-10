"""캐시 서비스 — 정확 일치 + 유사 질문 + 무효화."""

import hashlib
import json
import logging
from dataclasses import dataclass

from app.cache.redis_cache import RedisCache
from app.config import settings
from app.embedding.embedder import Embedder
from app.vectorstore.chroma_store import ChromaStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CachedAnswer:
    """캐시에서 복원된 답변."""

    answer: str
    sources: list[dict]
    answerable: bool
    model: str
    cache_type: str  # "exact" | "similar"


class CacheService:
    """3단계 캐시 관리: 정확일치(Redis) + 유사질문(Chroma) + 무효화."""

    def __init__(
        self,
        redis: RedisCache,
        chroma_cache: ChromaStore,
        embedder: Embedder,
    ):
        self._redis = redis
        self._chroma_cache = chroma_cache  # cache_questions collection
        self._embedder = embedder

    @staticmethod
    def hash_question(question: str) -> str:
        """질문 → SHA-256 해시 (정확 일치 캐시 키)."""
        normalized = question.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()

    async def get_exact(self, question_hash: str) -> CachedAnswer | None:
        """1단계: Redis 정확 일치 캐시 조회."""
        cached = await self._redis.get_cache(question_hash)
        if cached is None:
            return None

        try:
            data = json.loads(cached)
            logger.info("캐시 HIT (정확일치): %s…", question_hash[:12])
            return CachedAnswer(
                answer=data["answer"],
                sources=data.get("sources", []),
                answerable=data.get("answerable", True),
                model=data.get("model", "cached"),
                cache_type="exact",
            )
        except (json.JSONDecodeError, KeyError):
            logger.warning("캐시 파싱 실패, 삭제: %s…", question_hash[:12])
            await self._redis.delete_cache(question_hash)
            return None

    def get_similar(
        self,
        question_embedding: list[float],
        threshold: float | None = None,
    ) -> CachedAnswer | None:
        """2단계: Chroma cache collection에서 유사 질문 검색."""
        if threshold is None:
            threshold = settings.cache_similarity_threshold

        results = self._chroma_cache.search(
            query_embedding=question_embedding, top_k=1,
        )
        if not results:
            return None

        top = results[0]
        # Chroma cosine distance: 0 = 동일, 2 = 정반대
        # similarity = 1 - distance
        similarity = 1.0 - top.distance
        if similarity < threshold:
            return None

        try:
            data = json.loads(top.metadata.get("answer_json", "{}"))
            logger.info(
                "캐시 HIT (유사질문): similarity=%.4f, threshold=%.2f",
                similarity, threshold,
            )
            return CachedAnswer(
                answer=data["answer"],
                sources=data.get("sources", []),
                answerable=data.get("answerable", True),
                model=data.get("model", "cached"),
                cache_type="similar",
            )
        except (json.JSONDecodeError, KeyError):
            return None

    async def save(
        self,
        question: str,
        question_hash: str,
        question_embedding: list[float],
        answer_json: str,
        source_files: list[str],
    ) -> None:
        """캐시 저장: Redis(정확일치) + Chroma(유사질문)."""
        # Redis 정확 일치
        await self._redis.set_cache(
            question_hash=question_hash,
            answer_json=answer_json,
            source_files=source_files,
            ttl=settings.cache_ttl_seconds,
        )

        # Chroma 유사 질문 (벡터 + 메타데이터)
        cache_id = f"cache::{question_hash}"
        self._chroma_cache.add(
            ids=[cache_id],
            embeddings=[question_embedding],
            documents=[question],
            metadatas=[{
                "question_hash": question_hash,
                "answer_json": answer_json,
                "source_files": ",".join(source_files),
            }],
        )
        logger.info("캐시 저장 완료: %s…", question_hash[:12])

    async def invalidate_by_document(self, filename: str) -> int:
        """문서 변경 시 관련 캐시 무효화 (Redis + Chroma)."""
        # Redis: source_files에 해당 문서가 포함된 캐시 삭제
        redis_deleted = await self._redis.delete_caches_by_source(filename)

        # Chroma cache: source_files 메타데이터로 필터링 삭제
        try:
            self._chroma_cache._collection.delete(
                where={"source_files": {"$contains": filename}},
            )
        except Exception:
            # Chroma $contains 미지원 시 전체 스캔 후 삭제
            all_cache = self._chroma_cache._collection.get(include=["metadatas"])
            ids_to_delete = []
            if all_cache["metadatas"]:
                for i, meta in enumerate(all_cache["metadatas"]):
                    sources = meta.get("source_files", "")
                    if filename in sources.split(","):
                        ids_to_delete.append(all_cache["ids"][i])
            if ids_to_delete:
                self._chroma_cache._collection.delete(ids=ids_to_delete)

        total = redis_deleted
        logger.info("캐시 무효화 완료: %s (Redis %d건)", filename, redis_deleted)
        return total
