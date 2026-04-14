# 05-pdf-enhance — CHECKLIST

## 0. 사전 준비

- [x] [AI] PLAN.md / CONTEXT.md / CHECKLIST.md 작성
- [x] [AI] LlamaParse 제외 결정 (검증 에이전트 리뷰 반영)
- [x] [AI] sample-docs/security-policy.pdf 생성 (2페이지, 텍스트 기반)

## 1. PdfExtractor 마크다운 변환 추가

- [x] [AI] `PdfExtractor._to_markdown()` 메서드 추가 (3줄)
  - 변환 규칙: `^\d+\.\s+[가-힣]` → `## N. 제목` (1가지만)
  - 그 외 텍스트 그대로 유지
- [x] [AI] `PdfExtractor.extract()` — pypdf 추출 후 `_to_markdown()` 호출

## 2. 청킹 라우터 + 인제스트 서비스 수정

- [x] [AI] `router.py` — `chunk_document()`에 `force_markdown=False` 파라미터 추가
- [x] [AI] `router.py` — `force_markdown=True`이면 마크다운 인식 청킹 분기
- [x] [AI] `ingest_service.py` — PDF일 때 `force_markdown=True` 전달

## 3. 테스트 + 품질 측정

- [x] [USER] Before 스크린샷 확보 (eval/images/ Q1~Q5 pypdf-claude/codex)
- [ ] [USER] After 테스트 — PDF 재업로드 후 동일 질문 5개 재테스트
- [ ] [USER] Before/After 비교 수치 기록 (docs/TROUBLESHOOTING.md INT-010)

## 4. 검증 + 리뷰

- [x] [AI] Python 문법 검사 (3개 파일 통과)
- [x] [AI] 보안 패턴 검사 (경고 없음)
- [x] [AI] 코드 리뷰 (HIGH/MEDIUM 이슈 없음)

## 5. 커밋 + push

- [ ] [AI] 커밋 + push
