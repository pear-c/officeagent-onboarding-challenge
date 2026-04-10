"""Document Q&A API — FastAPI 진입점."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import health, ingest, query
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 리소스 관리 (임베딩 모델 로딩, DB 연결 등)."""
    # TODO: 임베딩 모델 로딩, Chroma/Redis 연결
    yield
    # TODO: 리소스 정리


app = FastAPI(
    title="Document Q&A API",
    description="문서 기반 질의응답 REST API (RAG + LLM)",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(ingest.router, prefix="/api/v1", tags=["documents"])
app.include_router(query.router, prefix="/api/v1", tags=["query"])
