# 01-architecture — 시스템 아키텍처 설계

## 목표

RAG Q&A API의 **전체 아키텍처를 확정**하고, 프로젝트 스켈레톤 + `ARCHITECTURE.md` 초안을 만든다.

## 핵심 설계 원칙 (사용자 확정)

> **"정확도에는 최고를, 속도에는 캐시를, 체감 대기에는 스트리밍을."**

- 정확도를 가장 높일 수 있는 곳(임베딩 모델, 답변 LLM)에는 **최고 품질 모델** 사용
- 시간 절감은 **캐시**(LLM 호출 자체를 회피)와 **스트리밍**(체감 대기시간 ↓)으로 달성
- 보조 작업(쿼리 재작성, 정규화)에는 **빠른 모델**로 비용/시간 절약

## 확정된 기술 스택

| 항목 | 선택 | 이유 |
|---|---|---|
| 임베딩 모델 | **BAAI/bge-m3** (1024차원, 2.3GB) | MTEB 한국어 Retrieval 최상위. 정확도 우선 원칙 |
| 벡터 DB | **Chroma** (Docker 서버 모드) | 이 규모에서 성능 차이 무의미. 셋업/코드 단순성 압도 |
| 캐시 DB | **Redis** | 캐시 표준. 유사 질문 매칭 + 문서 해시 기반 무효화 |
| 청킹 전략 | **하이브리드** (재귀 분할 + 마크다운 인식) | .txt/.pdf는 재귀, .md는 헤더 분할 → 재귀 fallback |
| LLM (답변) | **Claude Sonnet 4.6** (claude-agent-sdk) | 정확도 최고 투자 영역. 환각 억제 + 출처 인용 |
| LLM (보조) | **Codex GPT-5 mini** (codex CLI) | 시간 절감 영역. 쿼리 재작성, 정규화 |
| ↳ 역할 확정 | **4단계 평가 하네스로 측정 후 확정** | 잠정 가설. 데이터로 결정 |
| 프레임워크 | **FastAPI + uvicorn** | 비동기 + Pydantic + OpenAPI |
| 평가 하네스 | 골든 20케이스, 6메트릭 | Retrieval Hit / Citation / Refusal / JSON Parse / Latency |

## 산출물

| 산출물 | 위치 |
|---|---|
| PLAN / CONTEXT / CHECKLIST | `.claude/tasks/01-architecture/` |
| 기술 결정 문서 5개 | `.claude/knowledge/decisions/03~07` |
| **`ARCHITECTURE.md` 초안** (필수 제출) | 리포 루트 |
| 프로젝트 스켈레톤 | `app/`, `eval/`, `tests/`, `scripts/` |
| `docker-compose.yml` | 리포 루트 |
| `pyproject.toml` + `.env.example` | 리포 루트 |
| `Dockerfile` | 리포 루트 |

## 아키텍처 흐름도

```
[클라이언트]
    │
    ▼ POST /api/v1/documents (파일 업로드)
┌─────────────────────────────────────────────┐
│  FastAPI (uvicorn)                          │
│                                             │
│  IngestRouter ──► IngestService             │
│    ① 텍스트 추출 (pypdf/pdfplumber)         │
│    ② 청킹 (하이브리드: 재귀+마크다운)        │
│    ③ 임베딩 (bge-m3 via sentence-transformers)│
│    ④ 벡터 DB 저장 ──────────────► [Chroma]  │
│    ⑤ 문서 해시 저장 ────────────► [Redis]   │
│                                             │
│  QueryRouter ──► RAGService                 │
│    ① 캐시 확인 ◄────────────────── [Redis]  │
│    ② (miss) 질문 임베딩 (bge-m3)            │
│    ③ 벡터 검색 ◄────────────────── [Chroma] │
│    ④ 프롬프트 조립                           │
│    ⑤ LLM 호출 ──► LLMProvider               │
│       ├─ ClaudeProvider (답변 생성)         │
│       └─ CodexProvider (보조 작업)          │
│    ⑥ 캐시 저장 ─────────────────► [Redis]   │
│    ⑦ 응답 반환 (JSON or SSE 스트리밍)       │
└─────────────────────────────────────────────┘
```

## API 엔드포인트

| Method | Path | 역할 |
|---|---|---|
| `POST` | `/api/v1/documents` | 문서 업로드 (multipart/form-data) |
| `GET` | `/api/v1/documents` | 업로드된 문서 목록 |
| `POST` | `/api/v1/query` | 질의응답 (JSON 응답) |
| `POST` | `/api/v1/query/stream` | 질의응답 (SSE 스트리밍) |
| `GET` | `/health` | 헬스체크 |

## 다음 단계

`02-ingestion` — 문서 수집 파이프라인 구현
- 텍스트 추출 (PDF, TXT, MD)
- 청킹 (하이브리드)
- 임베딩 + Chroma 저장
- POST /api/v1/documents 엔드포인트
