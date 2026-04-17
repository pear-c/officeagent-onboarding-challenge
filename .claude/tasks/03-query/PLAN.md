# 03-query — RAG 질의응답 파이프라인 구현

## 목표

`POST /api/v1/query` (JSON) + `POST /api/v1/query/stream` (SSE) 엔드포인트 완성.
캐시 확인 → 벡터 검색 → 프롬프트 조립 → LLM 호출 → 캐시 저장 → 응답 반환.

## 핵심 설계 원칙

- **정확도 우선**: 답변 LLM에 Claude Sonnet 4.6 사용 + output_format JSON 스키마 강제
- **캐시로 시간 절감**: 동일/유사 질문 → LLM 호출 자체를 건너뜀 (3~15초 → ~5ms)
- **스트리밍으로 체감 대기 절감**: SSE로 토큰 단위 실시간 전송 + sources 먼저 전송
- **LLMProvider 추상화**: Claude/Codex 1줄 swap, 04-eval에서 측정 후 역할 확정

## 구현 순서 (의존성 기반 bottom-up)

| 순서 | 모듈 | 파일 | 핵심 내용 | 예상 줄수 |
|------|------|------|----------|----------|
| 1 | ClaudeProvider | `app/llm/claude_provider.py` | claude-agent-sdk → generate(output_format) + stream | ~70 |
| 2 | CodexProvider | `app/llm/codex_provider.py` | subprocess → generate + stream (플래그 사전 확인) | ~80 |
| 3 | RedisCache 확장 | `app/cache/redis_cache.py` | 캐시 답변 get/set/delete + TTL | +40 → ~90 |
| 4 | CacheService | `app/services/cache_service.py` | 정확일치(Redis) + 유사질문(Chroma cache) + 무효화 | ~130 |
| 5 | RAGService | `app/services/rag_service.py` | 전체 파이프라인 조율 (answer + answer_stream) | ~160 |
| 6 | Query Router | `app/api/routers/query.py` | DI 연결 + SSE StreamingResponse | ~70 |
| 7 | DI + Lifespan | `deps.py` + `main.py` | CacheService + RAGService 초기화 | +35 |
| 8 | IngestService 연결 | `ingest_service.py` | CacheService DI 추가 + 무효화 호출 | +10 |
| 9 | 테스트 | `tests/unit/` | RAGService + CacheService Mock 단위 테스트 | ~200 |

## 모듈별 상세 설계

### 1. ClaudeProvider (`app/llm/claude_provider.py`)

```python
from claude_agent_sdk import query, ClaudeAgentOptions

class ClaudeProvider(LLMProvider):
    def __init__(self, model="claude-sonnet-4-6"):
        self._model = model

    async def generate(self, system, user, max_tokens=1024, json_mode=False):
        options = ClaudeAgentOptions(
            system_prompt=system,
            model=self._model,
            max_turns=1,
            allowed_tools=[],
            output_format=ANSWER_JSON_SCHEMA if json_mode else None,
        )
        # 응답 메시지 타입 분기: AssistantMessage → TextBlock 추출
        # 예외 처리: CLINotFoundError, ProcessError

    async def stream(self, system, user):
        # async for msg in query(prompt=user, options=...):
        #     TextBlock에서 텍스트 추출 후 yield
```

**설계 결정 (D22)**:
- `json_mode=True` 시 `output_format` JSON 스키마 강제 + 프롬프트 포맷 유지 (이중 안전)
- `max_turns=1` + `allowed_tools=[]` 고정 (도구 호출 없이 단발 응답)
- 메시지 타입 분기: `ResultMessage` → `AssistantMessage` → `TextBlock.text` 추출

### 2. CodexProvider (`app/llm/codex_provider.py`)

```python
class CodexProvider(LLMProvider):
    async def generate(self, system, user, max_tokens=1024, json_mode=False):
        # asyncio.create_subprocess_exec("codex", ...)
        # 플래그: 구현 전 `codex --help`로 확인 후 확정
        # system prompt: CLI 지원 시 별도 플래그, 미지원 시 프롬프트 합성 fallback

    async def stream(self, system, user):
        # subprocess stdout을 line 단위로 yield
```

**설계 결정 (D23)**:
- 구현 전 `codex --help` 실행하여 실제 플래그 확정
- system prompt fallback: `f"[시스템 지시]\n{system}\n\n[질문]\n{user}"` 형태

### 3. RedisCache 확장 (`app/cache/redis_cache.py`)

기존 문서 해시 메서드 위에 캐시 답변 메서드 추가:

```python
# 키 프리픽스
_CACHE_EXACT_PREFIX = "cache:exact:"

async def get_cache(self, question_hash: str) -> str | None
async def set_cache(self, question_hash: str, answer_json: str, ttl: int) -> None
async def delete_cache(self, question_hash: str) -> None
async def delete_caches_by_pattern(self, pattern: str) -> int
```

### 4. CacheService (`app/services/cache_service.py`)

**책임 범위** (D24 — 문서 해시 메서드 제거, RedisCache 담당 유지):
- `get_exact(question_hash)` → Redis
- `get_similar(question_embedding, threshold)` → Chroma cache_questions collection
- `save(question, question_hash, question_embedding, answer_json, sources_meta)` → Redis + Chroma cache
- `invalidate_by_document(filename)` → Redis + Chroma cache에서 해당 문서 참조 캐시 삭제

```python
class CacheService:
    def __init__(self, redis: RedisCache, chroma_cache: ChromaStore, embedder: Embedder):
        self._redis = redis
        self._chroma_cache = chroma_cache  # cache_questions collection
        self._embedder = embedder
```

### 5. RAGService (`app/services/rag_service.py`)

```
answer(question) 흐름:
  ① question_hash = SHA-256(question)
  ② 캐시 확인: exact → similar → miss
  ③ (miss) 질문 임베딩: embedder.embed_query(question)
  ④ 벡터 검색: chroma.search(query_embedding, top_k)
  ⑤ 프롬프트 조립: templates.build_user_prompt(question, chunks)
  ⑥ LLM 호출: answer_llm.generate(system, user, json_mode=True)
  ⑦ JSON 파싱 + 검증
  ⑧ 캐시 저장
  ⑨ QueryAnswer 반환

answer_stream(question) 흐름:
  ①~④ 동일
  ⑤ sources 먼저 yield (D25)
  ⑥ LLM 스트리밍: async for token in answer_llm.stream(system, user)
  ⑦ 각 토큰 yield
  ⑧ done 이벤트 yield (latency_ms, answerable, model)
  ⑨ 백그라운드: 캐시 저장 (전체 답변 누적 후)
```

### 6. Query Router (`app/api/routers/query.py`)

```python
@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest, rag: RAGService = Depends(get_rag_service)):
    answer = await rag.answer(req.question)
    return QueryResponse(data=answer)

@router.post("/query/stream")
async def query_stream(req: QueryRequest, rag: RAGService = Depends(get_rag_service)):
    return StreamingResponse(
        rag.answer_stream(req.question),
        media_type="text/event-stream",
    )
```

### 7. SSE 스트리밍 포맷 (D25)

**sources 먼저 전송** (옵션 A 선택):

```
data: {"type":"sources","sources":[{"file":"company-policy.txt","chunk_id":3,"text":"..."}]}

data: {"type":"token","content":"교육비"}
data: {"type":"token","content":" 지원"}
data: {"type":"token","content":" 한도는"}
...

data: {"type":"done","answerable":true,"cached":false,"model":"claude-sonnet-4-6","latency_ms":3200}
```

이유: 검색은 즉시 완료되므로 출처를 먼저 보여주고, LLM 토큰을 스트리밍하면 사용자가 출처를 보면서 답변 생성 과정을 볼 수 있음.

### 8. IngestService 무효화 연결 (D26)

```python
class IngestService:
    def __init__(self, embedder, chroma, redis, cache_service: CacheService):
        self._cache_service = cache_service

    async def ingest(self, filename, content):
        ...
        if existing_hash is not None:
            # 문서 변경 감지 → 관련 캐시 무효화
            await self._cache_service.invalidate_by_document(filename)
            self._chroma.delete_by_document(filename)
        ...
```

## 리스크

| 리스크 | 가능성 | 완화 |
|--------|--------|------|
| claude-agent-sdk API가 예상과 다름 | 중 | WSL에서 import 검증 후 코딩 + 메시지 타입 분기 대비 |
| Codex CLI 플래그가 예상과 다름 | 중 | `codex --help` 사전 확인, system prompt fallback 준비 |
| 유사질문 캐시가 오답 반환 | 저 | threshold 0.95 보수적 설정 (config.py에 이미 있음) |
| Chroma cache collection 초기화 타이밍 | 저 | Lifespan에서 documents + cache 두 collection 모두 생성 |

## 산출물

| 산출물 | 위치 |
|--------|------|
| 작업 문서 3개 | `.claude/tasks/03-query/` |
| ClaudeProvider 구현 | `app/llm/claude_provider.py` |
| CodexProvider 구현 | `app/llm/codex_provider.py` |
| RedisCache 확장 | `app/cache/redis_cache.py` |
| CacheService | `app/services/cache_service.py` |
| RAGService | `app/services/rag_service.py` |
| Query Router | `app/api/routers/query.py` |
| DI + Lifespan 확장 | `app/api/deps.py` + `app/main.py` |
| IngestService 연결 | `app/services/ingest_service.py` |
| 테스트 | `tests/unit/test_rag_service.py`, `tests/unit/test_cache_service.py` |

## 다음 단계

`04-eval` — 평가 하네스 구현 + Claude/Codex 비교 측정 + 프롬프트 튜닝
