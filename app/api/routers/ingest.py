"""문서 업로드 라우터."""

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.api.deps import get_ingest_service
from app.config import settings
from app.extraction.text_extractor import SUPPORTED_EXTENSIONS
from app.schemas import DocumentListResponse, DocumentUploadResponse
from app.services.ingest_service import IngestService

logger = logging.getLogger(__name__)

router = APIRouter()

_READ_CHUNK_SIZE = 64 * 1024  # 64KB 단위 스트리밍 읽기


async def _read_file_with_limit(file: UploadFile) -> bytes:
    """파일을 스트리밍으로 읽으면서 크기 제한 검사.

    메모리에 전체 파일을 올린 후 거부하는 대신,
    청크 단위로 읽으면서 초과 시 즉시 중단.
    """
    max_size = settings.max_file_size
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_READ_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"파일 크기가 {max_size // (1024 * 1024)}MB를 초과합니다.",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _validate_filename(filename: str) -> None:
    """파일명 길이 + 경로 순회 문자 검증."""
    if len(filename) > settings.max_filename_length:
        raise HTTPException(
            status_code=400,
            detail=f"파일 이름이 {settings.max_filename_length}자를 초과합니다.",
        )
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=400,
            detail="파일 이름에 경로 문자를 포함할 수 없습니다.",
        )


def _validate_extension(filename: str) -> str:
    """파일 확장자 검증 → 확장자 반환."""
    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )
    return ext


@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile,
    service: IngestService = Depends(get_ingest_service),
) -> DocumentUploadResponse:
    """문서 파일 업로드 → 텍스트 추출 → 청킹 → 임베딩 → 저장."""
    filename = file.filename or ""
    if not filename:
        raise HTTPException(status_code=400, detail="파일 이름이 비어있습니다.")

    _validate_filename(filename)
    _validate_extension(filename)
    content = await _read_file_with_limit(file)

    if not content:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")

    doc_info = await service.ingest(filename, content)
    return DocumentUploadResponse(data=doc_info)


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    service: IngestService = Depends(get_ingest_service),
) -> DocumentListResponse:
    """업로드된 문서 목록 조회."""
    docs = await service.list_documents()
    return DocumentListResponse(data=docs)
