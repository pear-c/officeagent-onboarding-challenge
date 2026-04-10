"""Pydantic 요청/응답 모델."""

from pydantic import BaseModel, Field


# ===== 공통 =====

class ErrorDetail(BaseModel):
    field: str
    message: str
    code: str


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


# ===== 문서 업로드 =====

class DocumentInfo(BaseModel):
    """업로드된 문서 정보."""
    filename: str
    content_hash: str
    chunk_count: int
    file_size: int


class DocumentListResponse(BaseModel):
    data: list[DocumentInfo]


class DocumentUploadResponse(BaseModel):
    data: DocumentInfo


# ===== 질의응답 =====

class QueryRequest(BaseModel):
    """질문 요청."""
    question: str = Field(..., min_length=1, max_length=2000)


class SourceInfo(BaseModel):
    """답변 출처 정보."""
    file: str
    chunk_id: int
    text: str


class QueryAnswer(BaseModel):
    """질의응답 결과."""
    answer: str
    sources: list[SourceInfo]
    answerable: bool
    cached: bool
    model: str
    latency_ms: int


class QueryResponse(BaseModel):
    data: QueryAnswer


# ===== 헬스체크 =====

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"  # TODO: importlib.metadata에서 동적으로 가져오기
