# 03-query — CHECKLIST

## 0. 사전 준비

- [x] [AI] feature/02-ingestion → develop 머지 확인
- [x] [AI] feature/03-query 브랜치 생성
- [x] [AI] PLAN.md / CONTEXT.md / CHECKLIST.md 작성

## 1. ClaudeProvider 구현

- [x] [AI] `claude-agent-sdk` import 검증 (WSL)
- [x] [AI] `generate()` — query() 호출 + output_format JSON 스키마 + 메시지 타입 분기
- [x] [AI] `stream()` — async for + TextBlock 텍스트 추출 + yield
- [x] [AI] 예외 처리 — CLINotFoundError, ProcessError, 타임아웃
- [x] [AI] `ANSWER_JSON_SCHEMA` 상수 정의

## 2. CodexProvider 구현

- [x] [AI] `codex --help` 실행하여 실제 플래그 확인 (codex exec --json)
- [x] [AI] `generate()` — subprocess + JSONL stdout 파싱
- [x] [AI] `stream()` — subprocess stdout line 단위 yield
- [x] [AI] system prompt fallback (프롬프트 합성 방식 채택)

## 3. RedisCache 확장

- [x] [AI] `get_cache(question_hash)` 추가
- [x] [AI] `set_cache(question_hash, answer_json, source_files, ttl)` 추가
- [x] [AI] `delete_cache(question_hash)` 추가
- [x] [AI] `delete_caches_by_source(filename)` 추가 (MGET 배치)

## 4. CacheService 구현

- [x] [AI] `__init__` — RedisCache + ChromaStore(cache) + Embedder DI
- [x] [AI] `get_exact(question_hash)` — Redis 정확일치
- [x] [AI] `get_similar(question_embedding, threshold)` — Chroma cache collection
- [x] [AI] `save(question, question_hash, question_embedding, answer_json, sources_meta)` — Redis + Chroma
- [x] [AI] `invalidate_by_document(filename)` — Redis + Chroma cache 삭제

## 5. RAGService 구현

- [x] [AI] `__init__` — CacheService + ChromaStore + Embedder + LLMProvider DI
- [x] [AI] `answer(question)` — 캐시 확인 → 검색 → 프롬프트 → LLM → 캐시 저장 → QueryAnswer
- [x] [AI] `answer_stream(question)` — sources 먼저 → 토큰 스트리밍 → done 이벤트
- [x] [AI] JSON 파싱 + 검증 (LLM 응답 → QueryAnswer 변환)
- [x] [AI] 로깅 (각 단계 소요시간)

## 6. Query Router 완성

- [x] [AI] `POST /query` — RAGService.answer() + QueryResponse
- [x] [AI] `POST /query/stream` — RAGService.answer_stream() + StreamingResponse

## 7. DI + Lifespan 확장

- [x] [AI] `deps.py` — get_cache_service, get_rag_service 추가
- [x] [AI] `main.py` Lifespan — Chroma cache collection + CacheService + RAGService 초기화
- [x] [AI] `main.py` Lifespan — IngestService 생성자에 CacheService 전달

## 8. IngestService 무효화 연결

- [x] [AI] `ingest_service.py` — 생성자에 CacheService 추가
- [x] [AI] `ingest()` — 문서 변경 감지 시 `cache_service.invalidate_by_document()` 호출

## 9. 파이프라인 5단계 (검증)

- [x] [AI] Python 파일 문법 검사 — 10개 전체 통과
- [x] [AI] 보안 패턴 검사 — 시크릿 없음

## 10. 파이프라인 6단계 (리뷰)

- [x] [AI] 설계 리뷰 — D22~D26 반영 확인
- [x] [AI] 코드 품질 리뷰 — HIGH 4건 수정 (SyntaxError, 캡슐화, N+1, 함수 분리)
- [x] [AI] 보안 리뷰 — 통과
- [x] [AI] 성능 리뷰 — MGET 배치 적용
- [x] [AI] 테스트 리뷰 — 수동 테스트로 대체

## 10.1. 리뷰에서 남은 이슈

- [ ] `tests/unit/test_cache_service.py` — Mock 단위 테스트 (04-eval에서 추가)
- [ ] `tests/unit/test_rag_service.py` — Mock 단위 테스트 (04-eval에서 추가)
- [x] CacheService.get_similar() 동기 메서드 — 수용 (D18 ChromaStore 동기 유지 결정과 일관)
- [x] CacheService._collection 직접 접근 — 수용 (시간 대비 이점 적음)

## 11. 테스트

- [x] [USER] 전체 파이프라인 테스트 (문서 업로드 → 질문 → 답변 → 캐시 히트)
- [x] [USER] SSE 스트리밍 테스트 (sources 먼저 → 토큰 → done)

## 12. 추가 작업

- [x] [AI] SSE 스트리밍 원시 JSON 출력 버그 수정 (TS-004, SYSTEM_PROMPT_STREAM 분리)
- [x] [AI] 테스트 UI 스트리밍 피드백 추가 (단계 배지 + 스피너 + 타이핑 커서)

## 13. 커밋 + push

- [x] [AI] feature/03-query 커밋 + push (3건)
- [x] [AI] develop 머지 + 브랜치 정리 완료
