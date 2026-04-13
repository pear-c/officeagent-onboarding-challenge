# 05-pdf-llamaparse — CONTEXT

## 결정 이력

### D34. PDF 추출을 LlamaParse로 교체 (2026-04-13)

- **결정**: pypdf → LlamaParse (PDF→Markdown 변환)
- **이유**: pypdf는 텍스트만 추출하여 표/헤더 구조 손실. LlamaParse는 마크다운으로 변환하여 기존 마크다운 인식 청킹 재활용 가능
- **trade-off**: 클라우드 API 의존 + API 키 필요 (무료 월 10k 크레딧)
- **대안 검토**: pymupdf4llm은 로컬이지만 AGPL 라이선스 주의 (D12에서 이미 인지)

### D35. 청킹 라우터 수정 필요 (2026-04-13)

- **결정**: `router.py`에서 `.pdf`도 LlamaParse 적용 시 마크다운 청킹으로 분기
- **이유**: 현재 `.pdf`는 재귀 분할로 고정. LlamaParse가 마크다운을 반환하면 마크다운 인식 청킹이 더 정확
- **구현**: `chunk_document()`에 `use_markdown=True` 파라미터 추가 또는 PdfExtractor가 반환할 때 플래그 전달

## 맥락 복원 순서

1. **이 파일** 읽기 — 결정 이력
2. **PLAN.md** 읽기 — 구현 범위 + 순서
3. **CHECKLIST.md** 읽기 — 진행 상태
4. **`app/extraction/text_extractor.py`** 읽기 — 현재 PdfExtractor 코드
5. **`app/chunking/router.py`** 읽기 — 현재 확장자 기반 분기 로직
6. **`sample-docs/security-policy.pdf`** — 테스트용 PDF (이미 생성됨)

## 참고

- LlamaParse 공식 문서: https://developers.llamaindex.ai/python/cloud/llamaparse/getting_started/
- API 키 발급: https://cloud.llamaindex.ai/api-key
- 패키지: `pip install llama-parse`
- D12 (02-ingestion): 추출 모듈 분리 결정 — 교체 용이성 확보됨
