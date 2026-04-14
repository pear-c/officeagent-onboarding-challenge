# 05-pdf-enhance — CONTEXT

## 결정 이력

### D34. LlamaParse 제외 결정 (2026-04-14)

- **결정**: LlamaParse 사용하지 않음. pypdf 유지.
- **이유**:
  1. API Key 필수 → 평가자에게 추가 부담 (docker compose up 한 줄 실행 불가)
  2. PDF가 외부 서버로 전송 → 로컬 동작 불가
  3. 2페이지 55KB 텍스트 PDF에 LLM 파싱은 overkill
- **검증**: 검증 에이전트가 PRD의 "한 줄 실행 가능" 요구사항과 충돌 확인
- **대안**: pymupdf4llm도 AGPL + C 라이브러리 빌드 문제로 제외

### D35. 경량 마크다운 변환으로 방향 전환 (2026-04-14)

- **결정**: pypdf 출력에 번호 헤더(`^\d+\.\s+[가-힣]`) → `##` 변환만 추가
- **이유**: section 메타데이터 보존이 실질적 품질 향상 포인트. 20줄 이내로 구현 가능.
- **제약**: 범용 변환기 아님. security-policy.pdf 패턴에 맞는 수준만.
- **시간 제약**: 제출 4/17, 반나절 이상 투자 금지

### D36. router.py 수정 방식 — force_markdown 파라미터 (2026-04-14)

- **결정**: `chunk_document()`에 `force_markdown=False` 파라미터 추가
- **이유**: TextExtractor ABC 시그니처 변경 없이, ingest_service에서 확장자 판단 후 전달
- **구현**: `ingest_service.py`에서 `ext == ".pdf"` 이면 `force_markdown=True`

## 맥락 복원 순서

1. **이 파일** 읽기 — 결정 이력
2. **PLAN.md** 읽기 — 구현 범위 (최소)
3. **CHECKLIST.md** 읽기 — 진행 상태
4. **`app/extraction/text_extractor.py`** — 현재 PdfExtractor
5. **`app/chunking/router.py`** — 현재 확장자 분기
6. **`app/services/ingest_service.py`** — 인제스트 파이프라인

## 참고

- pypdf 공식 문서: https://pypdf.readthedocs.io/
- security-policy.pdf: 2페이지, 55KB, 순수 텍스트 (표/이미지 없음)
- 현재 Retrieval Hit Rate: 90%+ (PDF 케이스 미포함)
