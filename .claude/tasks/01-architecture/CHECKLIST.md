# 01-architecture — CHECKLIST

## 1. 기술 결정 문서

- [x] [AI] `decisions/03-embedding-model.md` — bge-m3 선택 근거
- [x] [AI] `decisions/04-vector-db.md` — Chroma 선택 근거
- [x] [AI] `decisions/05-cache-db.md` — Redis 선택 근거
- [x] [AI] `decisions/06-chunking-strategy.md` — 하이브리드 전략 근거
- [x] [AI] `decisions/07-eval-harness.md` — 평가 하네스 설계

## 2. ARCHITECTURE.md

- [x] [AI] 틀 작성 (섹션 구조 + 빈칸 표시)
- [ ] [USER] MTEB Leaderboard 스크린샷 캡처 → `docs/images/`
- [ ] [USER] bge-m3 모델 카드 스크린샷 캡처 → `docs/images/`
- [ ] [USER] 스크린샷을 ARCHITECTURE.md에 링크
- [ ] [측정 후] 평가 하네스 결과 표 채우기 (4단계 이후)
- [ ] [측정 후] Latency 수치 채우기 (4단계 이후)
- [ ] [측정 후] 청킹 전략 비교 수치 채우기 (4단계 이후)

## 3. 프로젝트 스켈레톤

- [x] [AI] `app/` 디렉토리 구조 생성
- [x] [AI] `app/main.py` (FastAPI 진입점)
- [x] [AI] `app/config.py` (pydantic-settings)
- [x] [AI] `app/schemas.py` (Pydantic 모델)
- [x] [AI] `app/api/routers/` (ingest, query, health)
- [x] [AI] `app/llm/provider.py` (LLMProvider ABC)
- [x] [AI] `app/llm/claude_provider.py`
- [x] [AI] `app/llm/codex_provider.py`
- [x] [AI] `app/services/` (ingest, rag, cache)
- [x] [AI] `app/chunking/` (recursive, markdown)
- [x] [AI] `app/embedding/` (embedder)
- [x] [AI] `app/vectorstore/` (chroma_store)
- [x] [AI] `app/cache/` (redis_cache)
- [x] [AI] `app/prompts/` (templates)
- [x] [AI] `eval/` (golden_dataset, run, metrics)
- [x] [AI] `tests/` (unit, integration, conftest.py)
- [x] [AI] `scripts/seed.sh`

## 4. 인프라 파일

- [x] [AI] `docker-compose.yml` (app + chroma + redis, healthcheck)
- [x] [AI] `Dockerfile` (multi-stage: dev/production)
- [x] [AI] `pyproject.toml` (claude-agent-sdk로 수정)
- [x] [AI] `.env.example`
- [x] [AI] `.dockerignore`

## 5. 파이프라인 5단계 (검증)

- [x] [AI] Python 파일 문법 검사 — 전체 통과
- [x] [AI] 보안 패턴 검사 — 시크릿 없음, 위험 함수 없음
- [x] 오류 0개

## 6. 파이프라인 6단계 (리뷰)

- [x] [AI] 설계 리뷰 — HIGH 2개 발견 (DI 부재, 업로드 보안)
- [x] [AI] 코드 품질 리뷰 — LOW 2개 (버전 하드코딩, 미사용 import)
- [x] [AI] 보안 리뷰 — MEDIUM (Redis 인증, Chroma healthcheck)
- [x] HIGH/MEDIUM 이슈 전부 수정 → 5단계 재실행 통과
- [x] 외부 리뷰 피드백 반영 (claude-agent-sdk 마이그레이션, pymupdf4llm 메모)

## 7. 커밋 + push

- [x] [AI] feature/01-architecture 커밋
- [x] [AI] push
- [x] [AI] feature/01-architecture → develop 머지

## 8. 문서 정합성 수정 (리뷰 피드백 후)

- [x] [AI] 전체 문서에서 `claude-code-sdk` → `claude-agent-sdk` 일괄 수정
- [x] [AI] `ClaudeCodeOptions` → `ClaudeAgentOptions` 일괄 수정
- [x] [AI] `claude_code_sdk` → `claude_agent_sdk` 일괄 수정
- [ ] [AI] 수정 커밋 + push
