# 02-ingestion — 문서 수집 파이프라인 구현

## 목표

문서 업로드(`POST /api/v1/documents`) → 텍스트 추출 → 청킹 → 임베딩 → Chroma 저장 + Redis 해시 저장.
문서 목록 조회(`GET /api/v1/documents`) 구현.

## 핵심 설계 원칙

- **정확도 우선**: bge-m3 임베딩 모델 사용 (MTEB 한국어 Retrieval 최상위)
- **확장성**: 텍스트 추출기·청킹 전략을 독립 모듈로 분리 (새 포맷 추가 시 기존 코드 수정 불필요)
- **불변성**: `Chunk` dataclass는 `frozen=True` (이미 적용됨)
- **비동기 일관성**: Redis는 `redis.asyncio` 사용 (FastAPI async 엔드포인트와 일관)

## 구현 순서 (의존성 기반 bottom-up)

| 순서 | 모듈 | 파일 | 핵심 내용 | 예상 줄수 |
|------|------|------|----------|----------|
| 1 | 텍스트 추출 | `extraction/text_extractor.py` | TxtExtractor, MdExtractor, PdfExtractor + 팩토리 | ~80 |
| 2 | 청킹 | `chunking/recursive.py` + `markdown.py` + `router.py` | 재귀 분할 + 마크다운 인식 + 포맷별 분기 | ~260 |
| 3 | 임베딩 래퍼 | `embedding/embedder.py` | bge-m3 로딩(1회), `embed()`, `embed_query()` | ~60 |
| 4 | Chroma 클라이언트 | `vectorstore/chroma_store.py` | 연결, add, search, delete_by_document, list_documents | ~100 |
| 5 | Redis (해시만) | `cache/redis_cache.py` | 비동기 연결, get/set/delete_document_hash | ~60 |
| 6 | IngestService | `services/ingest_service.py` | 파이프라인 조율 (추출→청킹→임베딩→저장→해시) + 로깅 | ~120 |
| 7 | DI + Lifespan | `api/deps.py` + `main.py` | 팩토리 함수 + 앱 시작 시 모델 로딩/연결 + exception handler | ~80 |
| 8 | API 라우터 | `api/routers/ingest.py` | POST/GET 완성 + 파일 크기 스트리밍 검증 | ~80 |
| 9 | 테스트 | `tests/unit/test_chunking.py` + `tests/unit/test_extraction.py` | 단위 테스트 (임베딩은 Mock) | ~200 |

## 모듈별 상세 설계

### 1. 텍스트 추출 (`app/extraction/`)

**새 디렉토리 생성** — 01-architecture에서는 IngestService에 포함 예정이었으나, 추출기 교체 용이성을 위해 분리.

```python
# text_extractor.py
class TextExtractor(ABC):
    def extract(self, content: bytes, filename: str) -> str: ...

class TxtExtractor(TextExtractor): ...   # content.decode("utf-8")
class MdExtractor(TextExtractor): ...    # content.decode("utf-8")
class PdfExtractor(TextExtractor): ...   # pypdf.PdfReader → 페이지별 텍스트

def get_extractor(filename: str) -> TextExtractor:
    """파일 확장자로 추출기 선택 (팩토리)."""
```

> 향후 pymupdf4llm 교체 시 `PdfExtractor` 내부만 변경하면 됨 (CONTEXT.md D-리뷰 참조)

### 2. 청킹 (`app/chunking/`)

**파일 분리** — `recursive.py` 하나에 모두 넣으면 400줄 초과 가능.

| 파일 | 함수 | 역할 |
|------|------|------|
| `recursive.py` | `recursive_chunk(text, chunk_size, overlap)` | `\n\n` → `\n` → `.` → ` ` 우선순위 분할 |
| `markdown.py` | `markdown_aware_chunk(text, chunk_size, overlap)` | `##` 헤더 기반 섹션 분할 → 재귀 fallback |
| `router.py` | `chunk_document(text, filename, chunk_size, overlap)` | 확장자별 전략 분기 |

- `Chunk` dataclass는 `recursive.py`에 유지 (다른 모듈에서 import)
- 파라미터: `chunk_size=400`, `overlap=80` (config.py에서 로드)

### 3. 임베딩 (`app/embedding/embedder.py`)

```python
class Embedder:
    def __init__(self, model_name: str, device: str):
        self._model = SentenceTransformer(model_name, device=device)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, query: str) -> list[float]:
        return self.embed([query])[0]
```

- **앱 시작 시 1회 로딩** → `app.state.embedder`에 저장
- `normalize_embeddings=True` — cosine similarity 계산 최적화

### 4. Chroma (`app/vectorstore/chroma_store.py`)

```python
class ChromaStore:
    def __init__(self, host, port, collection_name):
        self._client = chromadb.HttpClient(host=host, port=port)
        self._collection = self._client.get_or_create_collection(collection_name)

    def add(self, ids, embeddings, documents, metadatas) -> None
    def search(self, query_embedding, top_k) -> list[SearchResult]
    def delete_by_document(self, filename) -> None
    def list_documents(self) -> list[dict]  # GET /documents용
    def count(self) -> int
```

- `list_documents()`: Chroma 메타데이터에서 고유 filename 목록 추출
- `delete_by_document()`: 문서 재업로드 시 기존 벡터 삭제

### 5. Redis — 해시 저장만 (`app/cache/redis_cache.py`)

```python
class RedisCache:
    def __init__(self, host, port, db):
        self._client = redis.asyncio.Redis(host=host, port=port, db=db)

    async def get_document_hash(self, filename) -> str | None
    async def set_document_hash(self, filename, content_hash) -> None
    async def delete_document_hash(self, filename) -> None
    async def close(self) -> None
```

- 03-query에서 캐시 조회/저장 메서드 추가 예정
- Lifespan 종료 시 `close()` 필수 호출

### 6. IngestService — 파이프라인 조율

```
ingest(filename, content) 흐름:
  ① SHA-256 해시 계산
  ② Redis에서 이전 해시 비교 → 동일하면 "이미 최신" 반환
  ③ 텍스트 추출 (ExtractorFactory)
  ④ 청킹 (chunk_document)
  ⑤ 임베딩 (Embedder.embed)
  ⑥ Chroma 기존 벡터 삭제 (재업로드 시)
  ⑦ Chroma 저장 (벡터 + 원본 텍스트 + 메타데이터)
  ⑧ Redis 해시 저장
  ⑨ DocumentInfo 반환
```

- 각 단계별 INFO 로그 (소요시간, 청크 수, 벡터 수)
- `logging.getLogger(__name__)` 사용

### 7. API + DI + Lifespan

**exception handler** (`main.py`):
```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "...", "message": exc.detail, "details": []}}
    )
```

**파일 크기 검증 개선** (`ingest.py`):
- `request.headers.get("content-length")` 먼저 확인
- 그래도 안전을 위해 스트리밍 읽기 + 크기 누적 체크

**Lifespan**:
```
startup:
  ① Embedder 로딩 (bge-m3, ~10초)
  ② ChromaStore 연결 + healthcheck
  ③ RedisCache 연결

shutdown:
  ① RedisCache.close()
```

### 8. 테스트 전략

| 구분 | 대상 | 방법 |
|------|------|------|
| 단위 | 청킹 함수 | 경계 케이스: 빈 문자열, overlap > chunk_size, 한글 분할 |
| 단위 | 텍스트 추출 | 실제 sample-docs 파일 사용 |
| 단위 | IngestService | 임베딩·Chroma·Redis 전부 Mock |
| 통합 | API 엔드포인트 | `pytest.mark.integration` + Docker 필요 |

## 산출물

| 산출물 | 위치 |
|--------|------|
| 작업 문서 3개 | `.claude/tasks/02-ingestion/` |
| 텍스트 추출 모듈 | `app/extraction/` (신규) |
| 청킹 모듈 (3파일) | `app/chunking/` |
| 임베딩 래퍼 | `app/embedding/embedder.py` |
| Chroma 클라이언트 | `app/vectorstore/chroma_store.py` |
| Redis 클라이언트 | `app/cache/redis_cache.py` |
| IngestService | `app/services/ingest_service.py` |
| DI + Lifespan | `app/api/deps.py` + `app/main.py` |
| API 라우터 | `app/api/routers/ingest.py` |
| 테스트 | `tests/unit/test_chunking.py`, `tests/unit/test_extraction.py` |

## 다음 단계

`03-query` — RAG 질의응답 파이프라인 (캐시 조회 + 벡터 검색 + LLM 호출 + 스트리밍)
