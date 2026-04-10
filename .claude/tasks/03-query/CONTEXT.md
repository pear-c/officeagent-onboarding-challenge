# 03-query — CONTEXT (결정 이력 + 제약 + 참고)

## 결정 이력

### D22. ClaudeProvider — output_format JSON 스키마 강제 (2026-04-10)

- **결정**: `json_mode=True` 시 `ClaudeAgentOptions.output_format`에 JSON 스키마 전달 + 프롬프트 포맷 지시 유지 (이중 안전)
- **이유**: 분석 에이전트 피드백 — 프롬프트만으로 JSON 강제하는 것보다 output_format이 파싱 실패율 낮음 (평가 항목 "구조화된 출력")
- **구현**: `ANSWER_JSON_SCHEMA` 상수 정의 → `output_format={"type": "json_schema", "schema": ANSWER_JSON_SCHEMA}`
- **추가**: 메시지 타입 분기 (AssistantMessage → TextBlock.text), CLINotFoundError/ProcessError 예외 처리

### D23. CodexProvider — CLI 플래그 사전 확인 필수 (2026-04-10)

- **결정**: 구현 전 `codex --help`로 실제 플래그 확인 후 코딩. system prompt 미지원 시 프롬프트 합성 fallback
- **이유**: 분석 에이전트 피드백 — 계획의 `--quiet`, `--model codex-mini` 플래그가 실제와 다를 수 있음
- **fallback**: `f"[시스템 지시]\n{system}\n\n[질문]\n{user}"`

### D24. CacheService 책임 범위 — 문서 해시 제거 (2026-04-10)

- **결정**: CacheService에서 `get_document_hash()` / `save_document_hash()` 제거. 문서 해시는 RedisCache 전담
- **이유**: 분석 에이전트 피드백 — RedisCache에 이미 구현된 기능과 책임 중복
- **CacheService 범위**: 캐시 답변 관련만 (exact/similar/invalidate)

### D25. SSE sources 먼저 전송 (2026-04-10)

- **결정**: SSE 스트리밍에서 sources를 LLM 토큰보다 먼저 전송 (옵션 A)
- **이유**: 벡터 검색은 즉시 완료되므로 출처를 먼저 보여주면 UX 개선. 구현 복잡도 차이 거의 없음
- **포맷**: `sources` → `token` (반복) → `done`

### D26. IngestService에 CacheService DI 추가 (2026-04-10)

- **결정**: IngestService 생성자에 CacheService 추가. 문서 변경 감지 시 `invalidate_by_document()` 호출
- **이유**: 분석 에이전트 피드백 — 계획에 무효화 흐름은 있었으나 IngestService ↔ CacheService 연결이 누락
- **위치**: `ingest()` 메서드의 `if existing_hash is not None:` 분기 내부

## 제약 조건 (01-architecture + 02-ingestion 계승 + 추가)

| # | 제약 | 영향 |
|---|------|------|
| C9 | ARCHITECTURE.md 수치는 검증 가능한 출처 or 자체 측정만 | 추정 수치 단언 금지 |
| C10 | 스트리밍 응답 필수 (PRD 평가 항목) | SSE 구현 |
| C11 | 임베딩 모델(2.3GB) 앱 시작 시 1회 로딩 | `app.state.embedder` |
| C12 | Redis 비동기 필수 | `redis.asyncio` 사용 |
| C13 | 에러 응답 `ErrorResponse` 포맷 통일 | exception handler |
| C14 | LLM 역할 분할은 잠정 가설 (04-eval에서 확정) | config.py 기본값만 설정 |
| C15 | Chroma cache collection은 documents와 별도 | `cache_questions` collection |

## 02-ingestion 이연 항목 처리

| 항목 | 이번 단계 포함? | 비고 |
|------|--------------|------|
| IngestService Mock 단위 테스트 | ✅ | RAGService 테스트와 함께 |
| 통합 테스트 (Docker) | ❌ | 04-eval에서 |
| PdfExtractor 테스트 | ❌ | 별도 |
| 페이지네이션 | ❌ | 불필요 |

## 참고 스킬

| 스킬 | 적용 부분 |
|------|----------|
| `python-patterns` | ABC 패턴, DI, 팩토리 |
| `api-design` | SSE 스트리밍, 에러 응답 |
| `content-hash-cache-pattern` | 캐시 무효화 전략 |

## 참고 파일

| 파일 | 용도 |
|------|------|
| `app/config.py` | 설정값 (cache_ttl, search_top_k, threshold) |
| `app/schemas.py` | QueryRequest, QueryAnswer, SourceInfo |
| `app/prompts/templates.py` | 프롬프트 템플릿 (이미 구현) |
| `app/llm/provider.py` | LLMProvider ABC (이미 구현) |
| `.claude/knowledge/decisions/01-llm-sdk-claude-vs-codex.md` | LLM SDK 결정 |
| `.claude/knowledge/decisions/05-cache-db.md` | 캐시 설계 |
| `.claude/knowledge/decisions/07-eval-harness.md` | 평가 하네스 설계 |
