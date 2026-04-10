# 01-architecture — CHECKLIST

## 1. 기술 결정 문서

- [ ] [AI] `decisions/03-embedding-model.md` — bge-m3 선택 근거
- [ ] [AI] `decisions/04-vector-db.md` — Chroma 선택 근거
- [ ] [AI] `decisions/05-cache-db.md` — Redis 선택 근거
- [ ] [AI] `decisions/06-chunking-strategy.md` — 하이브리드 전략 근거
- [ ] [AI] `decisions/07-eval-harness.md` — 평가 하네스 설계

## 2. ARCHITECTURE.md

- [ ] [AI] 틀 작성 (섹션 구조 + 빈칸 표시)
- [ ] [USER] MTEB Leaderboard 스크린샷 캡처 → `docs/images/`
- [ ] [USER] bge-m3 모델 카드 스크린샷 캡처 → `docs/images/`
- [ ] [USER] 스크린샷을 ARCHITECTURE.md에 링크
- [ ] [측정 후] 평가 하네스 결과 표 채우기 (4단계 이후)
- [ ] [측정 후] Latency 수치 채우기 (4단계 이후)
- [ ] [측정 후] 청킹 전략 비교 수치 채우기 (4단계 이후)

## 3. 프로젝트 스켈레톤

- [ ] [AI] `app/` 디렉토리 구조 생성
- [ ] [AI] `app/main.py` (FastAPI 진입점)
- [ ] [AI] `app/config.py` (pydantic-settings)
- [ ] [AI] `app/schemas.py` (Pydantic 모델)
- [ ] [AI] `app/api/routers/` (ingest, query, health)
- [ ] [AI] `app/llm/provider.py` (LLMProvider ABC)
- [ ] [AI] `app/llm/claude_provider.py`
- [ ] [AI] `app/llm/codex_provider.py`
- [ ] [AI] `app/services/` (ingest, rag, cache)
- [ ] [AI] `app/chunking/` (recursive, markdown)
- [ ] [AI] `app/embedding/` (embedder)
- [ ] [AI] `app/vectorstore/` (chroma_store)
- [ ] [AI] `app/cache/` (redis_cache)
- [ ] [AI] `app/prompts/` (templates)
- [ ] [AI] `eval/` (golden_dataset, run, metrics)
- [ ] [AI] `tests/` (unit, integration)
- [ ] [AI] `scripts/seed.sh`

## 4. 인프라 파일

- [ ] [AI] `docker-compose.yml` (app + chroma + redis)
- [ ] [AI] `Dockerfile` (multi-stage)
- [ ] [AI] `pyproject.toml`
- [ ] [AI] `.env.example`
- [ ] [AI] `.dockerignore`

## 5. 파이프라인 5단계 (검증)

- [ ] [AI] Python 파일 문법 검사 (`python -m py_compile`)
- [ ] [AI] 보안 패턴 검사 (시크릿 하드코딩 등)
- [ ] 오류 수에 따라 수정

## 6. 파이프라인 6단계 (리뷰)

- [ ] [AI] 설계 리뷰 (PLAN.md 반영 여부)
- [ ] [AI] 코드 품질 리뷰
- [ ] [AI] 보안 리뷰
- [ ] HIGH 이슈 수정 시 5단계 재실행

## 7. 커밋 + push

- [ ] [AI] feature/01-architecture 커밋
- [ ] [AI] push
- [ ] [AI] feature/01-architecture → develop 머지
