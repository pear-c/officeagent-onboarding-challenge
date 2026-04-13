# 05-pdf-llamaparse — PDF 추출 고도화 (LlamaParse)

## 목표

PDF 추출을 `pypdf`(텍스트만) → `LlamaParse`(PDF→Markdown 변환)로 교체하여,
표/목록/헤더 구조가 보존된 마크다운을 생성하고 기존 마크다운 인식 청킹을 재활용한다.
**변경 전후 품질을 수치로 비교 측정**한다.

## 배경 — 현재 문제점

현재 `PdfExtractor`는 `pypdf`로 단순 텍스트 추출만 수행:
- **표(table)**: 셀 구분이 사라지고 텍스트가 연결되어 의미 손실
- **목록**: 들여쓰기/번호가 유실될 수 있음
- **헤더**: PDF의 폰트 크기 기반 구조가 평문으로 변환되어 섹션 구분 불가
- **결과**: 재귀 청킹이 적용되어 마크다운 인식 청킹의 이점을 못 받음

## LlamaParse 선택 이유

| 항목 | pypdf (현재) | LlamaParse | pymupdf4llm (대안) |
|------|-------------|------------|-------------------|
| 표 추출 | 텍스트만 (구조 손실) | 마크다운 표로 변환 | 마크다운 변환 가능 |
| 헤더 인식 | 없음 | `#`, `##` 마크다운 헤더 | 가능 |
| 라이선스 | MIT | 클라우드 API (무료 10k/월) | AGPL (주의) |
| 청킹 연계 | 재귀 분할만 가능 | **마크다운 인식 청킹 재활용** | 동일 |
| API 키 | 불필요 | 필요 (LLAMA_CLOUD_API_KEY) | 불필요 |
| 설치 | pypdf (이미 있음) | `pip install llama-parse` | `pip install pymupdf4llm` |

**LlamaParse 선택**: 표 추출 품질이 가장 높고, 마크다운 출력이 기존 `.md` 파이프라인과 자연스럽게 연결됨.
D12(추출 모듈 분리)에서 교체 가능하게 설계해둔 덕분에 `PdfExtractor` 내부만 변경하면 됨.

## 구현 범위

### 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `app/extraction/text_extractor.py` | `PdfExtractor.extract()` 내부를 LlamaParse 호출로 교체 |
| `app/config.py` | `llama_cloud_api_key` 설정 추가 |
| `.env.example` | `LLAMA_CLOUD_API_KEY` 추가 |
| `pyproject.toml` | `llama-parse` 의존성 추가 |
| `sample-docs/security-policy.pdf` | 테스트용 PDF (표 포함) — 이미 생성됨 |
| `eval/golden_dataset.json` | PDF 관련 테스트케이스 추가 |

### 변경하지 않는 파일

- `chunking/` — 마크다운 인식 청킹 그대로 사용 (PDF→MD 변환되므로)
- `ingest_service.py` — 파이프라인 변경 없음
- `rag_service.py` — 변경 없음

### 구현 순서

| 순서 | 작업 |
|------|------|
| 1 | LlamaParse API 키 발급 (cloud.llamaindex.ai) |
| 2 | `PdfExtractor` 수정 (LlamaParse 호출 → 마크다운 반환) |
| 3 | `config.py` + `.env.example` 업데이트 |
| 4 | `pyproject.toml`에 `llama-parse` 추가 |
| 5 | security-policy.pdf 업로드 테스트 |
| 6 | 품질 비교 측정 (Before/After) |
| 7 | golden_dataset에 PDF 케이스 추가 + 재측정 |

## LlamaParse 사용법

```python
from llama_parse import LlamaParse

parser = LlamaParse(
    api_key=settings.llama_cloud_api_key,
    result_type="markdown",
)
documents = parser.load_data(file_path)  # 동기
# 또는
documents = await parser.aload_data(file_path)  # 비동기
markdown_text = documents[0].text
```

**PdfExtractor 수정 후 흐름**:
```
PDF 업로드 → PdfExtractor.extract()
  ① LlamaParse API 호출 (PDF → Markdown)
  ② 마크다운 텍스트 반환
  → chunk_document()에서 .md로 인식 → 마크다운 인식 청킹 적용
```

주의: `chunk_document()`의 `router.py`에서 확장자 기반으로 `.pdf`는 재귀 분할로 분기됨.
→ **LlamaParse 적용 시 `.pdf`도 마크다운 청킹으로 분기하도록 수정 필요** (`router.py`)

## 산출물

| 산출물 | 위치 |
|--------|------|
| PdfExtractor 수정 | `app/extraction/text_extractor.py` |
| 청킹 라우터 수정 | `app/chunking/router.py` |
| 설정 추가 | `app/config.py`, `.env.example` |
| PDF 샘플 | `sample-docs/security-policy.pdf` |
| 품질 비교 결과 | `docs/TROUBLESHOOTING.md` 또는 별도 문서 |
