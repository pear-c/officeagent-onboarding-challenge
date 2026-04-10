"""질의응답 라우터."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_rag_service
from app.schemas import QueryRequest, QueryResponse
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(
    req: QueryRequest,
    rag: RAGService = Depends(get_rag_service),
) -> QueryResponse:
    """질문에 대해 문서 기반 답변 생성 (JSON 응답)."""
    answer = await rag.answer(req.question)
    return QueryResponse(data=answer)


@router.post("/query/stream")
async def query_stream(
    req: QueryRequest,
    rag: RAGService = Depends(get_rag_service),
) -> StreamingResponse:
    """질문에 대해 문서 기반 답변 생성 (SSE 스트리밍)."""
    return StreamingResponse(
        rag.answer_stream(req.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
