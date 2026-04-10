# 03-query — CHECKLIST

## 0. 사전 준비

- [ ] [AI] feature/02-ingestion → develop 머지 확인
- [ ] [AI] feature/03-query 브랜치 생성
- [ ] [AI] PLAN.md / CONTEXT.md / CHECKLIST.md 작성

## 1. ClaudeProvider 구현

- [ ] [AI] `claude-agent-sdk` import 검증 (WSL)
- [ ] [AI] `generate()` — query() 호출 + output_format JSON 스키마 + 메시지 타입 분기
- [ ] [AI] `stream()` — async for + TextBlock 텍스트 추출 + yield
- [ ] [AI] 예외 처리 — CLINotFoundError, ProcessError, 타임아웃
- [ ] [AI] `ANSWER_JSON_SCHEMA` 상수 정의

## 2. CodexProvider 구현

- [ ] [AI] `codex --help` 실행하여 실제 플래그 확인
- [ ] [AI] `generate()` — subprocess + stdout 파싱
- [ ] [AI] `stream()` — subprocess stdout line 단위 yield
- [ ] [AI] system prompt fallback (CLI 미지원 시 프롬프트 합성)

## 3. RedisCache 확장

- [ ] [AI] `get_cache(question_hash)` 추가
- [ ] [AI] `set_cache(question_hash, answer_json, ttl)` 추가
- [ ] [AI] `delete_cache(question_hash)` 추가
- [ ] [AI] `delete_caches_by_pattern(pattern)` 추가

## 4. CacheService 구현

- [ ] [AI] `__init__` — RedisCache + ChromaStore(cache) + Embedder DI
- [ ] [AI] `get_exact(question_hash)` — Redis 정확일치
- [ ] [AI] `get_similar(question_embedding, threshold)` — Chroma cache collection
- [ ] [AI] `save(question, question_hash, question_embedding, answer_json, sources_meta)` — Redis + Chroma
- [ ] [AI] `invalidate_by_document(filename)` — Redis + Chroma cache 삭제

## 5. RAGService 구현

- [ ] [AI] `__init__` — CacheService + ChromaStore + Embedder + LLMProvider DI
- [ ] [AI] `answer(question)` — 캐시 확인 → 검색 → 프롬프트 → LLM → 캐시 저장 → QueryAnswer
- [ ] [AI] `answer_stream(question)` — sources 먼저 → 토큰 스트리밍 → done 이벤트
- [ ] [AI] JSON 파싱 + 검증 (LLM 응답 → QueryAnswer 변환)
- [ ] [AI] 로깅 (각 단계 소요시간)

## 6. Query Router 완성

- [ ] [AI] `POST /query` — RAGService.answer() + QueryResponse
- [ ] [AI] `POST /query/stream` — RAGService.answer_stream() + StreamingResponse

## 7. DI + Lifespan 확장

- [ ] [AI] `deps.py` — get_cache_service, get_rag_service 추가
- [ ] [AI] `main.py` Lifespan — Chroma cache collection + CacheService + RAGService 초기화
- [ ] [AI] `main.py` Lifespan — IngestService 생성자에 CacheService 전달

## 8. IngestService 무효화 연결

- [ ] [AI] `ingest_service.py` — 생성자에 CacheService 추가
- [ ] [AI] `ingest()` — 문서 변경 감지 시 `cache_service.invalidate_by_document()` 호출

## 9. 파이프라인 5단계 (검증)

- [ ] [AI] Python 파일 문법 검사
- [ ] [AI] 보안 패턴 검사

## 10. 파이프라인 6단계 (리뷰)

- [ ] [AI] 설계 리뷰 — PLAN.md 반영 확인
- [ ] [AI] 코드 품질 리뷰
- [ ] [AI] 보안 리뷰
- [ ] [AI] 성능 리뷰
- [ ] [AI] 테스트 리뷰

## 10.1. 리뷰에서 남은 이슈 (해당 시 기록)

(리뷰 후 업데이트)

## 11. 테스트

- [ ] [AI] `tests/unit/test_cache_service.py` — Mock 단위 테스트
- [ ] [AI] `tests/unit/test_rag_service.py` — Mock 단위 테스트
- [ ] [USER] 전체 파이프라인 테스트 (문서 업로드 → 질문 → 답변)

## 12. 커밋 + push

- [ ] [AI] feature/03-query 커밋 + push
