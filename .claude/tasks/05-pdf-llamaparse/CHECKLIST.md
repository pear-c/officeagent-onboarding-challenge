# 05-pdf-llamaparse — CHECKLIST

## 0. 사전 준비

- [x] [AI] PLAN.md / CONTEXT.md / CHECKLIST.md 작성
- [x] [AI] sample-docs/security-policy.pdf 생성 (표 포함)
- [ ] [USER] LlamaParse API 키 발급 (https://cloud.llamaindex.ai/api-key)
- [ ] [AI] feature/05-pdf-llamaparse 브랜치 생성

## 1. LlamaParse 적용

- [ ] [AI] `pyproject.toml`에 `llama-parse` 의존성 추가
- [ ] [AI] `app/config.py`에 `llama_cloud_api_key` 설정 추가
- [ ] [AI] `.env.example`에 `LLAMA_CLOUD_API_KEY` 추가
- [ ] [AI] `PdfExtractor.extract()` 수정 — LlamaParse 호출 → 마크다운 반환
- [ ] [AI] fallback: API 키 없으면 기존 pypdf로 동작 (평가자 편의)

## 2. 청킹 라우터 수정

- [ ] [AI] `app/chunking/router.py` — PDF도 마크다운 청킹 분기 (LlamaParse 사용 시)

## 3. 품질 비교 테스트

- [ ] [USER] security-policy.pdf 업로드 (pypdf 버전) — 청크 수, 내용 확인
- [ ] [USER] security-policy.pdf 업로드 (LlamaParse 버전) — 청크 수, 내용 확인
- [ ] [AI] golden_dataset.json에 PDF 관련 케이스 추가 (5~8개)
- [ ] [USER] eval 재측정 — PDF 케이스 포함

### 비교 측정 항목 (Before/After 메모)

```
[Before — pypdf]
- 청크 수: (측정)
- 표 보존 여부: (확인)
- 헤더 구조 보존: (확인)
- Retrieval Hit Rate (PDF 케이스): (측정)
- Keyword Hit Rate (PDF 케이스): (측정)

[After — LlamaParse]
- 청크 수: (측정)
- 표 보존 여부: (확인)
- 헤더 구조 보존: (확인)
- Retrieval Hit Rate (PDF 케이스): (측정)
- Keyword Hit Rate (PDF 케이스): (측정)
```

### 예상 테스트 질문 (PDF 문서 기반)

- "비밀번호 최소 길이는?" → 12자
- "기밀 정보의 저장 방식은?" → AES-256 암호화
- "보안 사고 발생 시 경영진 보고 기한은?" → P1/P2 즉시
- "서버실 출입 인증 단계는?" → 3단계 (RF + 지문 + PIN)
- "생성형 AI 도구 사용 조건은?" → 보안팀 승인, 기밀/대외비 입력 금지
- "개인정보 유출 시 DPO 보고 기한은?" → 24시간
- "정보 분류 4단계는?" → 기밀, 대외비, 일반, 공개 (표에서 추출)

## 4. 문서 업데이트

- [ ] [AI] TROUBLESHOOTING.md에 pypdf vs LlamaParse 비교 결과 기록
- [ ] [AI] ARCHITECTURE.md 청킹 전략 섹션에 PDF→MD 변환 추가

## 5. 검증 + 리뷰

- [ ] [AI] Python 문법 검사
- [ ] [AI] 코드 리뷰

## 6. 커밋 + push

- [ ] [AI] feature/05-pdf-llamaparse 커밋 + push
- [ ] [AI] develop 머지 + 브랜치 정리
