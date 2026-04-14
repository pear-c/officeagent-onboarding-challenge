# 05-pdf-enhance — PDF 추출 + 경량 마크다운 변환

## 목표

PDF에서도 마크다운 인식 청킹의 `section` 메타데이터를 활용하도록 경량 후처리 추가.
pypdf 유지, 외부 의존성 없음, 코드 20줄 이내.

## 배경 — 현재 상태

- `PdfExtractor`: pypdf로 텍스트 추출 → **충분한 품질** (순수 텍스트 PDF)
- `router.py`: `.pdf` → 재귀 분할 → `Chunk.section=""` (섹션 정보 유실)
- 현재 Retrieval Hit Rate: **90%+** (PDF 케이스 제외 기준)

## LlamaParse 제외 결정

| 이유 | 상세 |
|------|------|
| API Key 부담 | 평가자에게 추가 가입/키 요구 → docker compose up 한 줄 실행 불가 |
| 클라우드 전송 | PDF가 외부 서버 전송, 로컬 동작 불가 |
| overkill | 2페이지 55KB 텍스트 PDF에 LLM 파싱은 과도 |

→ **pypdf 유지 + 번호 헤더만 마크다운 변환**

## 구현 범위 (최소)

### 변환 규칙 — 1가지만

```
^\d+\.\s+[가-힣]  →  ## N. 제목
```

예: `1. 비밀번호 정책` → `## 1. 비밀번호 정책`

그 외 모든 텍스트는 그대로 유지. 범용 PDF→마크다운 변환기 아님.

### 변경 파일 (3개)

| 파일 | 변경 내용 | 규모 |
|------|----------|------|
| `app/extraction/text_extractor.py` | `PdfExtractor`에 `_to_markdown()` 후처리 (~15줄) | 소 |
| `app/chunking/router.py` | `force_markdown` 파라미터 추가, PDF 분기 | 소 |
| `app/services/ingest_service.py` | PDF일 때 `force_markdown=True` 전달 | 1줄 |

### 변경하지 않는 파일

- `chunking/markdown.py`, `chunking/recursive.py` — 그대로
- `config.py`, `.env.example` — 외부 API 키 불필요
- `pyproject.toml` — 새 의존성 불필요

### 구현 순서

| 순서 | 작업 | 시간 |
|------|------|------|
| 1 | `PdfExtractor._to_markdown()` 추가 | 15분 |
| 2 | `router.py` + `ingest_service.py` 수정 | 15분 |
| 3 | security-policy.pdf 업로드 테스트 | 10분 |
| 4 | golden_dataset에 PDF 케이스 추가 (5~8개) | 20분 |
| 5 | eval 재측정 (Before/After) | 10분 |

**총 예상: ~1시간. 반나절 이내 완료.**

## 핵심 코드 스케치

```python
# text_extractor.py — PdfExtractor 내부
import re

_NUMBERED_HEADER = re.compile(r'^(\d+\.\s+[가-힣].+)$', re.MULTILINE)

def _to_markdown(self, text: str) -> str:
    """번호 헤더만 마크다운 ## 로 변환."""
    return _NUMBERED_HEADER.sub(r'## \1', text)
```

## 산출물

| 산출물 | 위치 |
|--------|------|
| PdfExtractor 후처리 | `app/extraction/text_extractor.py` |
| 청킹 라우터 수정 | `app/chunking/router.py` |
| 인제스트 연동 | `app/services/ingest_service.py` |
| PDF 테스트케이스 | `eval/golden_dataset.json` |
