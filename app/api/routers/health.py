"""헬스체크 라우터."""

from fastapi import APIRouter

from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """서버 상태 확인."""
    return HealthResponse()
