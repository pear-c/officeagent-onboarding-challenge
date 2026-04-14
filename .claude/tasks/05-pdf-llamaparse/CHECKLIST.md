# 05-pdf-enhance — CHECKLIST

## 0. 사전 준비

- [x] [AI] PLAN.md / CONTEXT.md / CHECKLIST.md 작성
- [x] [AI] LlamaParse 제외 결정 (검증 에이전트 리뷰 반영)
- [x] [AI] sample-docs/security-policy.pdf 생성 (2페이지, 텍스트 기반)
- [ ] [AI] feature/05-pdf-enhance 브랜치 생성 (이름 변경: llamaparse → enhance)

## 1. PdfExtractor 마크다운 변환 추가

- [ ] [AI] `PdfExtractor._to_markdown()` 메서드 추가 (~15줄)
  - 변환 규칙: `^\d+\.\s+[가-힣]` → `## N. 제목` (1가지만)
  - 그 외 텍스트 그대로 유지
- [ ] [AI] `PdfExtractor.extract()` — pypdf 추출 후 `_to_markdown()` 호출

## 2. 청킹 라우터 + 인제스트 서비스 수정

- [ ] [AI] `router.py` — `chunk_document()`에 `force_markdown=False` 파라미터 추가
- [ ] [AI] `router.py` — `force_markdown=True`이면 마크다운 인식 청킹 분기
- [ ] [AI] `ingest_service.py` — PDF일 때 `force_markdown=True` 전달 (1줄)

## 3. 테스트 + 품질 측정

- [ ] [USER] security-policy.pdf 업로드 — Before (현재 코드) 스냅샷
- [ ] [AI] 코드 적용 후 security-policy.pdf 재업로드 — After 스냅샷
- [ ] [AI] golden_dataset.json에 PDF 케이스 추가 (5~8개)
- [ ] [USER] eval 재측정 — PDF 케이스 포함

### 비교 측정 항목 (Before/After)

```
[Before — pypdf + 재귀 분할]
- 청크 수: (측정)
- section 메타데이터: "" (빈 문자열)
- Retrieval Hit Rate (PDF 케이스): (측정)

[After — pypdf + 마크다운 변환 + 마크다운 청킹]
- 청크 수: (측정)
- section 메타데이터: "1. 비밀번호 정책" 등 (보존)
- Retrieval Hit Rate (PDF 케이스): (측정)
```

### PDF 테스트 질문 (golden_dataset 추가용)

- "비밀번호 최소 길이는?" → 12자
- "기밀 정보의 저장 방식은?" → AES-256 암호화
- "서버실 출입 인증 단계는?" → 3단계 (RF + 지문 + PIN)
- "생성형 AI 도구 사용 조건은?" → 보안팀 승인, 기밀/대외비 입력 금지
- "개인정보 유출 시 DPO 보고 기한은?" → 24시간
- "보안 사고 발생 시 경영진 보고 기한은?" → P1/P2 즉시

## 4. 검증 + 커밋

- [ ] [AI] Python 문법 검사
- [ ] [AI] 코드 리뷰
- [ ] [AI] 커밋 + push (feature/05-pdf-enhance)
