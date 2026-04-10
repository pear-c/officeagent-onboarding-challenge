# 02-ingestion — CONTEXT (결정 이력 + 제약 + 참고)

## 결정 이력

### D12. 텍스트 추출 모듈 분리 (2026-04-10)

- **결정**: IngestService에서 추출 로직을 `app/extraction/` 모듈로 분리
- **이유**: 리뷰 피드백 — pymupdf4llm 교체 가능성 대비 (AGPL 라이선스 인지). 추출기만 교체하면 나머지 파이프라인 영향 없음 (Open-Closed)
- **구현**: TextExtractor ABC + TxtExtractor + MdExtractor + PdfExtractor + 팩토리 함수

### D13. 청킹 파일 분리 (2026-04-10)

- **결정**: `recursive.py` 단일 파일 → `recursive.py` + `markdown.py` + `router.py` 3파일 분리
- **이유**: 리뷰 피드백 — 단일 파일 400줄 초과 가능. CLAUDE.md 규칙 "파일 800줄 이하" + 단일 책임
- **Chunk dataclass**: `recursive.py`에 유지 (다른 모듈에서 import)

### D14. Redis 비동기 클라이언트 (2026-04-10)

- **결정**: `redis.asyncio.Redis` 사용
- **이유**: FastAPI async 엔드포인트와 일관. 동기 클라이언트 사용 시 이벤트 루프 블로킹 위험
- **Lifespan**: 종료 시 `close()` 필수 호출

### D15. 에러 응답 일관성 (2026-04-10)

- **결정**: 커스텀 exception handler 등록 → `ErrorResponse` 포맷 통일
- **이유**: 리뷰 피드백 — `HTTPException`의 기본 응답이 `schemas.py`의 `ErrorResponse`와 불일치
- **구현**: `main.py`에 `@app.exception_handler(HTTPException)` 등록

### D16. 파일 크기 검증 개선 (2026-04-10)

- **결정**: Content-Length 헤더 사전 확인 + 스트리밍 읽기 시 누적 크기 체크
- **이유**: 리뷰 피드백 — 현재 `await file.read()`로 10MB를 메모리에 다 올린 후 거부하는 문제
- **구현**: 청크 단위 읽기 + 누적 바이트 체크 → 초과 시 즉시 중단

### D17. 파이프라인 로깅 (2026-04-10)

- **결정**: 각 파이프라인 단계별 INFO 로그 추가
- **이유**: 리뷰 피드백 — 임베딩 소요시간, 청크 수 등 운영 시 디버깅에 필수
- **구현**: `logging.getLogger(__name__)`, 각 단계 시작/완료 + 소요시간

## 제약 조건 (01-architecture 계승 + 추가)

| # | 제약 | 영향 |
|---|------|------|
| C9 | ARCHITECTURE.md 수치는 검증 가능한 출처 or 자체 측정만 | 추정 수치 단언 금지 |
| C10 | 스트리밍 응답 필수 (PRD 평가 항목) | 03-query에서 SSE 구현 |
| C11 | 임베딩 모델(2.3GB) 앱 시작 시 1회 로딩 | `app.state.embedder`에 저장 |
| C12 | Redis 비동기 필수 | `redis.asyncio` 사용 |
| C13 | 에러 응답 `ErrorResponse` 포맷 통일 | exception handler 필수 |

## 01-architecture 리뷰 피드백 중 02-ingestion 관련

| 피드백 | 반영 |
|--------|------|
| pymupdf4llm 검토 (AGPL 주의) | D12: 추출 모듈 분리로 교체 용이하게 설계. 현재는 pypdf 사용 |
| chunk_size=400 → 200~300 검토 | 기본값 400 유지. 평가 하네스에서 비교 측정 예정 (04단계) |
| DI 컨테이너 부재 → deps.py 팩토리 | 02에서 get_embedder, get_chroma_store 등 추가 |
| 업로드 파일 제한 | D16: 스트리밍 읽기로 개선 |

### D18. ChromaStore 동기 호출 유지 (2026-04-10)

- **결정**: ChromaStore 메서드는 동기(sync)로 유지. `asyncio.to_thread()` 래핑하지 않음
- **이유**: `chromadb.HttpClient`가 동기 클라이언트만 지원. 이 과제 규모(동시 요청 적음)에서 이벤트 루프 블로킹이 실질적 문제가 되지 않음
- **대안**: 대규모 서비스라면 `asyncio.to_thread(self._chroma.add, ...)` 래핑 필요
- **참고**: RedisCache는 `redis.asyncio` 사용 — Redis는 공식 비동기 클라이언트 제공

### D19. chunk start_char 중복 매칭 방지 (2026-04-10)

- **결정**: `original_text.find(chunk_text, search_from)` — 이전 검색 위치 이후부터 find
- **이유**: 리뷰 피드백 — 동일 텍스트가 문서 내 반복될 때 항상 첫 번째 위치를 반환하는 버그
- **영향**: start_char/end_char 정확도 향상. 03-query에서 출처 표시에 활용 가능

## 참고 스킬

| 스킬 | 적용 부분 |
|------|----------|
| `python-patterns` | 프로젝트 구조, ABC 패턴, 팩토리 |
| `api-design` | 에러 응답 포맷, exception handler |
| `content-hash-cache-pattern` | SHA-256 해시 기반 중복 감지 + 캐시 무효화 |

## 참고 파일

| 파일 | 용도 |
|------|------|
| `app/config.py` | 설정값 (chunk_size, chroma_host 등) |
| `app/schemas.py` | Pydantic 모델 (DocumentInfo, ErrorResponse) |
| `sample-docs/company-policy.txt` | 테스트용 TXT (27줄) |
| `sample-docs/development-guide.md` | 테스트용 MD (37줄) |
| `docker-compose.yml` | Chroma(8100), Redis(6379) |
