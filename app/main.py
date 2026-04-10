"""Document Q&A API — FastAPI 진입점."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers import health, ingest, query
from app.cache.redis_cache import RedisCache
from app.config import settings
from app.embedding.embedder import Embedder
from app.vectorstore.chroma_store import ChromaStore

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 리소스 관리."""
    # ── startup ──
    logger.info("=== 앱 시작 ===")

    # 1) 임베딩 모델 로딩 (bge-m3, ~10초)
    app.state.embedder = Embedder(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
    )

    # 2) Chroma 연결
    app.state.chroma = ChromaStore(
        host=settings.chroma_host,
        port=settings.chroma_port,
        collection_name=settings.chroma_collection,
    )

    # 3) Redis 연결
    app.state.redis = RedisCache(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
    )

    # 4) Chroma 캐시 collection (유사 질문 캐시용)
    app.state.chroma_cache = ChromaStore(
        host=settings.chroma_host,
        port=settings.chroma_port,
        collection_name=settings.chroma_cache_collection,
    )

    # 5) CacheService (Redis + Chroma cache + Embedder)
    from app.services.cache_service import CacheService

    app.state.cache_service = CacheService(
        redis=app.state.redis,
        chroma_cache=app.state.chroma_cache,
        embedder=app.state.embedder,
    )

    # 6) IngestService (Embedder + Chroma + Redis + CacheService)
    from app.services.ingest_service import IngestService

    app.state.ingest_service = IngestService(
        embedder=app.state.embedder,
        chroma=app.state.chroma,
        redis=app.state.redis,
        cache_service=app.state.cache_service,
    )

    # 7) RAGService (CacheService + Chroma + Embedder + LLM)
    from app.api.deps import get_answer_llm
    from app.services.rag_service import RAGService

    app.state.rag_service = RAGService(
        cache_service=app.state.cache_service,
        chroma=app.state.chroma,
        embedder=app.state.embedder,
        answer_llm=get_answer_llm(),
    )

    logger.info("=== 리소스 초기화 완료 ===")
    yield

    # ── shutdown ──
    logger.info("=== 앱 종료 ===")
    await app.state.redis.close()


app = FastAPI(
    title="Document Q&A API",
    description="문서 기반 질의응답 REST API (RAG + LLM)",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTPException → ErrorResponse 포맷으로 통일."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": _status_to_code(exc.status_code),
                "message": exc.detail,
                "details": [],
            }
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """ValueError → 400 에러로 변환."""
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(exc),
                "details": [],
            }
        },
    )


def _status_to_code(status_code: int) -> str:
    """HTTP 상태 코드 → 에러 코드 문자열."""
    mapping = {
        400: "BAD_REQUEST",
        404: "NOT_FOUND",
        413: "FILE_TOO_LARGE",
        415: "UNSUPPORTED_MEDIA_TYPE",
        500: "INTERNAL_ERROR",
    }
    return mapping.get(status_code, f"HTTP_{status_code}")


app.include_router(health.router)
app.include_router(ingest.router, prefix="/api/v1", tags=["documents"])
app.include_router(query.router, prefix="/api/v1", tags=["query"])

# 정적 파일 (테스트 UI)
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    @app.get("/")
    async def root():
        """루트 → 테스트 UI."""
        return FileResponse(str(_STATIC_DIR / "index.html"))
