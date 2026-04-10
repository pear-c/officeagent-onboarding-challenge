"""FastAPI Depends 팩토리 — 서비스 의존성 주입."""

from app.config import settings
from app.llm.claude_provider import ClaudeProvider
from app.llm.codex_provider import CodexProvider
from app.llm.provider import LLMProvider


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


# TODO: 02-ingestion, 03-query 단계에서 추가
# def get_embedder() -> Embedder
# def get_chroma_store() -> ChromaStore
# def get_redis_cache() -> RedisCache
# def get_ingest_service() -> IngestService
# def get_rag_service() -> RAGService
