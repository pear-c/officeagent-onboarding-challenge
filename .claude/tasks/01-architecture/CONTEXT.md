# 01-architecture — CONTEXT (결정 이력 + 제약 + 원칙)

## 핵심 설계 원칙

### 원칙 1. 정확도 우선 투자 (사용자 확정 2026-04-09)

> "엉뚱한 답변 때문에 여러번 질문하는 시간 > 한 번 오래 걸려도 정확한 답변"

- RAG 파이프라인에서 정확도 기여도 70% = **벡터 검색(30%) + LLM 호출(40%)**
- 이 두 영역에 최고 품질 모델 사용
- 나머지 영역(캐시, 보조 LLM)에서 시간 절감

### 원칙 2. 캐시로 시간 절감

- LLM 호출이 응답 시간의 99% (3~15초)
- 동일/유사 질문 캐시 hit → LLM 호출 자체를 건너뜀 (3~15초 → 5ms)
- 문서 SHA-256 해시 기반 캐시 무효화 (content-hash-cache-pattern 스킬 적용)

### 원칙 3. 스트리밍으로 체감 대기 절감

- PRD 평가 항목 "스트리밍" 명시
- SSE(Server-Sent Events) 엔드포인트 별도 제공
- 실제 시간은 동일하지만 사용자가 "답이 오고 있다"고 느낌

### 원칙 4. ARCHITECTURE.md 수치 작성 원칙 (사용자 확정 2026-04-10)

ARCHITECTURE.md에 작성하는 모든 수치는 다음 기준을 따른다:

| 구분 | 전략 | 예시 |
|---|---|---|
| **검증 가능한 외부 벤치마크** | 출처 링크 + 스크린샷 첨부 | MTEB Leaderboard, HuggingFace 모델 카드 |
| **자체 측정 수치** | 평가 하네스 실행 결과 (`eval/results/`) | Retrieval Hit Rate, Latency p50/p95 |
| **출처 없는 추정/일반론** | ARCHITECTURE.md에 수치로 단언하지 않음 | "일반적으로 ~" 표현 사용 또는 자체 측정으로 대체 |

검증 가능한 외부 출처:
- MTEB Leaderboard: https://huggingface.co/spaces/mteb/leaderboard
- bge-m3 모델 카드: https://huggingface.co/BAAI/bge-m3
- multilingual-e5-base 모델 카드: https://huggingface.co/intfloat/multilingual-e5-base
- ko-sroberta 모델 카드: https://huggingface.co/jhgan/ko-sroberta-multitask

## 결정 이력

### D6. 임베딩 모델 → BAAI/bge-m3

- **결정**: bge-m3 (1024차원, 2.3GB, 8192 토큰 입력)
- **변경 이력**: e5-base(1.1GB) → bge-m3(2.3GB) [2026-04-09 변경]
- **변경 이유**: 사용자 원칙 "정확도 우선". MTEB 한국어 Retrieval nDCG@10에서 bge-m3가 5~8% 우위
- **상세**: `.claude/knowledge/decisions/03-embedding-model.md`

### D7. 벡터 DB → Chroma

- **결정**: Chroma (Docker 서버 모드)
- **이유**: 이 규모(청크 수십~수백 개)에서 Chroma/Qdrant/pgvector 모두 <1ms. 성능 차이 무의미. 셋업 단순성으로 Chroma
- **상세**: `.claude/knowledge/decisions/04-vector-db.md`

### D8. 캐시 DB → Redis

- **결정**: Redis 7 (Docker)
- **이유**: 캐시 사실상 표준. TTL 자동 만료. 문서 해시 기반 무효화 구현 용이
- **상세**: `.claude/knowledge/decisions/05-cache-db.md`

### D9. 청킹 전략 → 하이브리드 (재귀 + 마크다운)

- **결정**: 파일 포맷별 분기. .md는 마크다운 인식, 나머지는 재귀 분할
- **이유**: PRD 요구 "어떤 문서의 어떤 부분" 출처 → 마크다운 헤더 기반 출처가 가장 정확. .txt/.pdf는 재귀로 커버
- **상세**: `.claude/knowledge/decisions/06-chunking-strategy.md`

### D10. 평가 하네스

- **결정**: 골든 20케이스 + 6메트릭 + `eval/` 디렉토리
- **이유**: LLM 모델 선택, 프롬프트 튜닝, 청킹 전략 비교를 데이터로 결정
- **상세**: `.claude/knowledge/decisions/07-eval-harness.md`

### D11. 스트리밍 응답 추가

- **결정**: `/api/v1/query/stream` SSE 엔드포인트 추가
- **이유**: PRD 평가 기준 "LLM API 활용 — 스트리밍" 명시 (20%)
- **추가 시점**: 2026-04-09 (시간 분석 과정에서 도출)

## 제약 조건

00-prep CONTEXT.md의 C1~C8 유지 + 추가:

| # | 제약 | 영향 |
|---|---|---|
| C9 | ARCHITECTURE.md 수치는 검증 가능한 출처 or 자체 측정만 | 추정 수치 단언 금지 |
| C10 | 스트리밍 응답 필수 (PRD 평가 항목) | SSE 엔드포인트 추가 |

## 리뷰 피드백 반영 (2026-04-10)

| 피드백 | 조치 |
|---|---|
| `claude-code-sdk` deprecated → `claude-agent-sdk` | ✅ 즉시 수정 (pyproject.toml + claude_provider.py) |
| chunk_size=400 → 200~300 검토 | 기록. 평가 하네스에서 측정 |
| Chroma 포트 불일치 | ✅ 이미 수정 |
| pypdf vs pymupdf4llm | 기록. 구현 단계에서 비교. pymupdf4llm은 마크다운 출력 → 청킹과 자연 연결. 단 AGPL 라이선스 인지 |
| DI 컨테이너 부재 (이전 리뷰) | ✅ deps.py에 LLM provider 팩토리 추가 |
| 업로드 파일 제한 (이전 리뷰) | ✅ ingest.py에 크기/타입 검증 추가 |

## 참고 스킬

| 스킬 | 적용 부분 |
|---|---|
| `api-design` | API 엔드포인트 + 응답 형식 |
| `docker-patterns` | docker-compose.yml 설계 |
| `cost-aware-llm-pipeline` | LLM 역할 분할 + 비용 추적 |
| `content-hash-cache-pattern` | 문서 해시 기반 캐시 무효화 |
| `eval-harness` | 평가 하네스 설계 |
| `python-patterns` | 프로젝트 구조 + 코딩 패턴 |
