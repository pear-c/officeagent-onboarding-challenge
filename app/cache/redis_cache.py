"""Redis 캐시 클라이언트 — 비동기 (redis.asyncio)."""

import logging

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Redis 키 프리픽스
_DOC_HASH_PREFIX = "doc:hash:"


class RedisCache:
    """Redis 연결 + 문서 해시 CRUD.

    02-ingestion: 문서 해시 저장/조회/삭제만 구현.
    03-query: 캐시 조회/저장 메서드 추가 예정.
    """

    def __init__(self, host: str, port: int, db: int = 0):
        self._client = aioredis.Redis(
            host=host, port=port, db=db, decode_responses=True,
        )
        logger.info("Redis 연결: %s:%d (db=%d)", host, port, db)

    async def get_document_hash(self, filename: str) -> str | None:
        """문서의 SHA-256 해시 조회."""
        return await self._client.get(f"{_DOC_HASH_PREFIX}{filename}")

    async def set_document_hash(self, filename: str, content_hash: str) -> None:
        """문서의 SHA-256 해시 저장 (TTL 없음 — 문서가 삭제될 때까지 유지)."""
        await self._client.set(f"{_DOC_HASH_PREFIX}{filename}", content_hash)

    async def delete_document_hash(self, filename: str) -> None:
        """문서의 SHA-256 해시 삭제."""
        await self._client.delete(f"{_DOC_HASH_PREFIX}{filename}")

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
