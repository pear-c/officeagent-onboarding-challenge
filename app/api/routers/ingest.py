"""문서 업로드 라우터."""

from fastapi import APIRouter, HTTPException, UploadFile

from app.schemas import DocumentListResponse, DocumentUploadResponse

router = APIRouter()

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile) -> DocumentUploadResponse:
    """문서 파일 업로드 → 텍스트 추출 → 청킹 → 임베딩 → 저장."""
    # 파일 타입 검증
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 파일 크기 검증
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기가 10MB를 초과합니다.")
    await file.seek(0)

    # TODO: IngestService 호출
    raise NotImplementedError("02-ingestion 단계에서 구현")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    """업로드된 문서 목록 조회."""
    # TODO: 저장된 문서 메타데이터 조회
    raise NotImplementedError("02-ingestion 단계에서 구현")
