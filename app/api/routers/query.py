"""질의응답 라우터."""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas import QueryRequest, QueryResponse

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest) -> QueryResponse:
    """질문에 대해 문서 기반 답변 생성 (JSON 응답)."""
    # TODO: RAGService 호출
    raise NotImplementedError("03-query 단계에서 구현")


@router.post("/query/stream")
async def query_stream(req: QueryRequest) -> StreamingResponse:
    """질문에 대해 문서 기반 답변 생성 (SSE 스트리밍)."""
    # TODO: RAGService 스트리밍 호출
    raise NotImplementedError("03-query 단계에서 구현")
