"""Redis 캐시 클라이언트 — 비동기 (redis.asyncio)."""

import logging

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Redis 키 프리픽스
_DOC_HASH_PREFIX = "doc:hash:"
_CACHE_EXACT_PREFIX = "cache:exact:"
_CACHE_META_PREFIX = "cache:meta:"


class RedisCache:
    """Redis 연결 + 문서 해시 CRUD + 캐시 답변 CRUD.

    02-ingestion: 문서 해시 저장/조회/삭제.
    03-query: 캐시 답변 저장/조회/삭제 + 문서별 무효화.
    """

    def __init__(self, host: str, port: int, db: int = 0):
        self._client = aioredis.Redis(
            host=host, port=port, db=db, decode_responses=True,
        )
        logger.info("Redis 연결: %s:%d (db=%d)", host, port, db)

    # ===== 문서 해시 (02-ingestion) =====

    async def get_document_hash(self, filename: str) -> str | None:
        """문서의 SHA-256 해시 조회."""
        return await self._client.get(f"{_DOC_HASH_PREFIX}{filename}")

    async def set_document_hash(self, filename: str, content_hash: str) -> None:
        """문서의 SHA-256 해시 저장 (TTL 없음 — 문서가 삭제될 때까지 유지)."""
        await self._client.set(f"{_DOC_HASH_PREFIX}{filename}", content_hash)

    async def delete_document_hash(self, filename: str) -> None:
        """문서의 SHA-256 해시 삭제."""
        await self._client.delete(f"{_DOC_HASH_PREFIX}{filename}")

    # ===== 캐시 답변 (03-query) =====

    async def get_cache(self, question_hash: str) -> str | None:
        """정확 일치 캐시 조회 (답변 JSON 문자열)."""
        return await self._client.get(f"{_CACHE_EXACT_PREFIX}{question_hash}")

    async def set_cache(
        self, question_hash: str, answer_json: str, source_files: list[str], ttl: int,
    ) -> None:
        """캐시 답변 저장 + 출처 문서 메타데이터 (무효화용)."""
        key = f"{_CACHE_EXACT_PREFIX}{question_hash}"
        await self._client.set(key, answer_json, ex=ttl)
        # 무효화를 위해 이 캐시가 참조하는 소스 파일 목록 저장
        if source_files:
            meta_key = f"{_CACHE_META_PREFIX}{question_hash}"
            await self._client.set(meta_key, ",".join(source_files), ex=ttl)

    async def delete_cache(self, question_hash: str) -> None:
        """특정 캐시 삭제."""
        await self._client.delete(
            f"{_CACHE_EXACT_PREFIX}{question_hash}",
            f"{_CACHE_META_PREFIX}{question_hash}",
        )

    async def delete_caches_by_source(self, filename: str) -> int:
        """특정 문서를 참조하는 모든 캐시 삭제 (MGET 배치 조회)."""
        deleted = 0
        cursor = 0
        while True:
            cursor, keys = await self._client.scan(
                cursor=cursor, match=f"{_CACHE_META_PREFIX}*", count=100,
            )
            if not keys:
                if cursor == 0:
                    break
                continue

            # MGET으로 배치 조회 (N+1 방지)
            values = await self._client.mget(keys)
            for meta_key, sources in zip(keys, values):
                if sources and filename in sources.split(","):
                    q_hash = meta_key.removeprefix(_CACHE_META_PREFIX)
                    await self.delete_cache(q_hash)
                    deleted += 1

            if cursor == 0:
                break

        if deleted > 0:
            logger.info("캐시 무효화: %s 참조 %d건 삭제", filename, deleted)
        return deleted

    async def delete_all_caches(self) -> int:
        """전체 QA 캐시 삭제 (문서 해시는 유지)."""
        deleted = 0
        for prefix in (_CACHE_EXACT_PREFIX, _CACHE_META_PREFIX):
            cursor = 0
            while True:
                cursor, keys = await self._client.scan(
                    cursor=cursor, match=f"{prefix}*", count=100,
                )
                if keys:
                    await self._client.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break
        logger.info("전체 QA 캐시 삭제: %d건", deleted)
        return deleted

    # ===== 공통 =====

    async def ping(self) -> bool:
        """Redis 서버 healthcheck."""
        try:
            return await self._client.ping()
        except Exception:
            return False

    async def close(self) -> None:
        """연결 종료."""
        await self._client.aclose()
        logger.info("Redis 연결 종료")
