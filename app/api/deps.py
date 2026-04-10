"""FastAPI Depends 팩토리 — 서비스 의존성 주입."""

from fastapi import Request

from app.cache.redis_cache import RedisCache
from app.config import settings
from app.embedding.embedder import Embedder
from app.llm.claude_provider import ClaudeProvider
from app.llm.codex_provider import CodexProvider
from app.llm.provider import LLMProvider
from app.services.cache_service import CacheService
from app.services.ingest_service import IngestService
from app.services.rag_service import RAGService
from app.vectorstore.chroma_store import ChromaStore


def get_answer_llm() -> LLMProvider:
    """답변 생성용 LLM (정확도 우선)."""
    if settings.llm_answer_provider == "claude":
        return ClaudeProvider()
    return CodexProvider()


def get_auxiliary_llm() -> LLMProvider:
    """보조 작업용 LLM (속도 우선)."""
    if settings.llm_auxiliary_provider == "codex":
        return CodexProvider()
    return ClaudeProvider()


def get_embedder(request: Request) -> Embedder:
    """앱 시작 시 로딩된 임베딩 모델."""
    return request.app.state.embedder


def get_chroma_store(request: Request) -> ChromaStore:
    """Chroma 벡터 DB 클라이언트."""
    return request.app.state.chroma


def get_redis_cache(request: Request) -> RedisCache:
    """Redis 캐시 클라이언트."""
    return request.app.state.redis


def get_ingest_service(request: Request) -> IngestService:
    """앱 시작 시 생성된 IngestService."""
    return request.app.state.ingest_service


def get_cache_service(request: Request) -> CacheService:
    """앱 시작 시 생성된 CacheService."""
    return request.app.state.cache_service


def get_rag_service(request: Request) -> RAGService:
    """앱 시작 시 생성된 RAGService."""
    return request.app.state.rag_service
