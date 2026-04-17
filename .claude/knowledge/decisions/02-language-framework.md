# Decision 02. 언어 / 웹 프레임워크 선택 — Python + FastAPI

> **결정**: Python 3.11+ / FastAPI / uvicorn
> **이유 한 줄**: RAG 생태계가 Python에 압도적으로 집중되어 있고, FastAPI는 비동기 LLM 호출에 최적, 8일 기한에 가장 빠르게 동작 가능.

## 1. 평가 기준

채용 과제의 제약과 평가 항목으로부터 도출한 선정 기준:

| # | 기준 | 가중치 | 이유 |
|---|---|---|---|
| K1 | RAG 라이브러리 생태계 | 매우 높음 | 임베딩, 벡터 DB, PDF 추출 등이 풍부해야 8일 안에 동작 가능 |
| K2 | LLM SDK 통합 용이성 | 높음 | claude-agent-sdk와 codex CLI를 자연스럽게 부를 수 있어야 |
| K3 | 비동기 I/O 지원 | 높음 | LLM 호출은 느림 → 한 요청이 다른 요청 막으면 안 됨 |
| K4 | 채점자 친숙도 | 중간 | PRD가 "FastAPI 서버 설계"를 명시. 채점자 Python 친화적 가능성 |
| K5 | 사용자 친숙도 | 중간 | 사용자는 Java 메인이지만 Python 가능 |
| K6 | 학습 곡선 | 중간 | 8일 안에 처음 보는 언어/프레임워크는 위험 |
| K7 | 멀티 머신 (Win + Mac) 호환 | 높음 | 회사↔집 작업 환경이 다름 |
| K8 | 차별화 효과 | 낮음 | 채점은 설계 품질로 받음. 언어 자체로 가산점은 작음 |

## 2. 후보 비교

| 후보 | K1 생태계 | K2 LLM | K3 async | K4 채점자 | K5 사용자 | K6 학습 | K7 멀티OS | K8 차별화 | 종합 |
|---|---|---|---|---|---|---|---|---|---|
| **Python + FastAPI** ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | **최고** |
| Python + Flask | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ (sync) | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | 중상 |
| Java + Spring Boot | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ (사용자 한정) | ⭐⭐⭐⭐ | ⭐⭐⭐ | 중 |
| Node + NestJS | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | 중 |
| Rust + Axum | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 하 |
| Go + Gin/Echo | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 중하 |

## 3. 후보별 상세 평가

### 3-A. Python + FastAPI ⭐ 선택

#### 장점
- **K1 생태계 압도적**: `sentence-transformers`, `chromadb`, `qdrant-client`, `redis-py`, `pypdf`, `pdfplumber`, `langchain`, `llama-index` 등 핵심 라이브러리가 모두 Python 1순위 지원
- **K2 LLM SDK**: `claude-agent-sdk`는 **공식 Python SDK**가 있음 (네이티브 async). Codex CLI는 subprocess로 부르면 됨
- **K3 async**: FastAPI는 ASGI 기반, `async def` 네이티브. LLM 호출 동안 다른 요청 처리 가능
- **K4 채점자**: PRD가 "FastAPI 서버 설계, 레이어 분리, 비동기 처리"를 콕 집어 언급 → Python 친화적 채점 가능성 매우 높음
- **K7 멀티 OS**: Python + Docker 조합은 Win/Mac/Linux 모두 동일 동작
- **부가**: Pydantic으로 자동 입력 검증, OpenAPI 문서 자동 생성, dependency injection 깔끔

#### 단점
- 사용자가 Java가 메인이므로 일부 관례(`pyproject.toml`, `venv`, `__init__.py`) 학습 필요
- 타입 체킹이 Java만큼 엄격하지 않음 → mypy + Pydantic으로 보강

#### 실제 코드 인상

```python
# app/api/routers/query.py
from fastapi import APIRouter, Depends
from app.services.rag_service import RAGService
from app.schemas import QueryRequest, QueryResponse

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query(
    req: QueryRequest,
    rag: RAGService = Depends(),
) -> QueryResponse:
    return await rag.answer(req.question)
```

→ 30줄로 검증 + 라우팅 + DI + OpenAPI 문서까지. Spring Boot보다 boilerplate 작음.

### 3-B. Python + Flask

#### 장점
- 생태계 동일
- 매우 단순, 학습 비용 0

#### 단점
- **async가 1급 시민이 아님**. Flask 2.x에서 async 지원이 추가됐으나 미들웨어/확장이 sync 가정
- LLM 호출이 늦으면 워커가 블로킹됨 → 동시성 한계
- Pydantic 통합 불완전, 입력 검증 직접 작성
- 채용 과제의 "비동기 처리" 평가 항목에서 불리

→ FastAPI 대비 굳이 선택할 이유 없음.

### 3-C. Java + Spring Boot

#### 장점
- 사용자가 가장 익숙
- 엔터프라이즈 패턴 (DI, 트랜잭션, 레이어 분리) 깊은 경험
- JVM 안정성, 성숙한 생태계 (HTTP, JSON, 비동기)

#### 단점
- **K1 치명적**: RAG 라이브러리 부재
  - 임베딩: ❌ sentence-transformers 같은 게 없음. DJL(Deep Java Library)로 ONNX 모델 직접 로드해야 함 → 8일에 무리
  - PDF 추출: Apache PDFBox 가능하지만 한국어 처리 약함
  - 벡터 DB 클라이언트: Chroma는 공식 Java 클라이언트 없음, REST 직접 호출
  - LangChain4j 존재하지만 Python 대비 미성숙
- **K2 LLM SDK**: claude-agent-sdk는 Python 패키지. Java에서 부르려면 ProcessBuilder로 `claude` CLI 직접 spawn → 결과 파싱 직접 구현 필요. Codex도 동일
- **K6 학습**: 사용자에게는 익숙하지만 RAG 라이브러리 부재 보충에 시간 듦 → 결과적으로 학습 비용 큼
- **K8 차별화**: 채점자가 Spring을 모르거나 평가에 시간 더 걸림

#### 결론
사용자가 익숙해서 끌릴 수 있지만, **RAG 생태계 부재가 결정적**. 8일 안에 기본 동작도 위험.

### 3-D. Node.js + NestJS

#### 장점
- TypeScript 타입 안전
- async/await 네이티브
- Codex CLI는 npm 패키지 → 동일 환경
- LangChain.js 존재

#### 단점
- **K1 부족**:
  - 임베딩: `transformers.js`, `xenova` 등 있으나 Python 대비 모델 선택지 좁음, 한국어 모델 부족
  - 벡터 DB 클라이언트: Chroma JS 클라이언트 있으나 Python 대비 문서 빈약
  - PDF 추출: pdf.js, pdf-parse 있으나 한국어/표 처리 약함
- **K2**: claude-agent-sdk는 Python 전용. Node에서 쓰려면 subprocess
- **K6**: 사용자가 Node 메인이 아님

#### 결론
Python 다음 후보. 단 RAG 라이브러리 격차로 Python에 밀림.

### 3-E. Rust + Axum

#### 검토 동기
- 성능, 메모리 안전성, 차별화 효과
- 사용자가 호기심으로 질문함

#### 장점
- 비동기 I/O 최강 (Tokio)
- 차별화 어필 가능 (Rust 사용 지원자가 드물 것)

#### 단점
- **K1 치명적**:
  - **임베딩이 가장 큰 벽**: `sentence-transformers` 등가물 없음. 대안:
    - `fastembed-rs`: 모델 선택지 좁음, 한국어 모델 부족
    - `candle` (HF Rust ML): 강력하지만 셋업 복잡, 학습 곡선 가파름
    - ONNX Runtime + 직접 변환: 동작은 하나 변환 파이프라인 자체가 작업
  - PDF 텍스트 추출: `lopdf`, `pdf-extract` — 한국어/표/레이아웃 약함
  - 벡터 DB: Qdrant 클라이언트는 Rust 네이티브 (이건 OK)
- **K6 학습**: 라이프타임/Send+Sync/비동기 트레이트 등으로 8일에 압박
- **K2 LLM SDK**: subprocess 호출 가능하나 Python보다 boilerplate 많음
- **K5 사용자 미경험**

#### 검토한 변형: Rust + Python 사이드카 하이브리드
- Rust(API 서버) + Python(임베딩 사이드카 컨테이너 via gRPC/HTTP)
- ✅ 양쪽 장점 결합
- ❌ 컨테이너 2개 + 통신 프로토콜 + 8일 기한 → 과함

#### 결론
**탈락**. 매력은 있으나 RAG 영역에서 Python 대비 모든 면에서 불리. 사용자도 Python 유지에 동의.

### 3-F. Go + Gin/Echo

#### 장점
- 단순한 언어, 빠른 컴파일
- 비동기 I/O 우수 (goroutine)

#### 단점
- RAG 라이브러리 빈약 (Rust보다도 적음)
- 사용자 미경험
- 차별화 효과는 Rust보다 작음

#### 결론
**탈락**. 검토 가치 낮음.

## 4. 선택: Python + FastAPI

**최종 결정**:

```
언어:        Python 3.11+
웹 프레임워크: FastAPI
ASGI 서버:   uvicorn
검증/직렬화: Pydantic v2
의존성 관리: pyproject.toml + uv 또는 pip + venv
타입 체크:   mypy (개발 시)
포매터:      ruff
테스트:      pytest + pytest-asyncio
```

## 5. 사용 예정 주요 라이브러리 (잠정)

> 1단계에서 최종 확정. 여기 적은 건 가설.

| 영역 | 라이브러리 | 후보/대안 |
|---|---|---|
| 웹 프레임워크 | `fastapi` | — |
| ASGI 서버 | `uvicorn[standard]` | — |
| 입력 검증 | `pydantic` v2 | — |
| LLM (메인) | `claude-agent-sdk` | — |
| LLM (보조) | `subprocess` (codex CLI) | — |
| 임베딩 | `sentence-transformers` | `transformers`, `fastembed` |
| 벡터 DB | `chromadb` | `qdrant-client`, `pgvector` |
| 캐시 | `redis` | `valkey-py` |
| PDF 추출 | `pypdf` | `pdfplumber`, `pymupdf` |
| 텍스트 청킹 | 자체 구현 또는 `langchain-text-splitters` | — |
| 평가 하네스 | 자체 구현 | `ragas` (선택) |
| 로깅 | `structlog` | 표준 `logging` |
| 테스트 | `pytest` + `pytest-asyncio` + `httpx` | — |

## 6. 프로젝트 구조 (잠정)

```
officeagent-onboarding-challenge/
├── app/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── api/
│   │   ├── routers/         # 라우터 (ingest, query, health)
│   │   └── deps.py          # FastAPI Depends
│   ├── services/
│   │   ├── ingest_service.py
│   │   ├── rag_service.py
│   │   └── cache_service.py
│   ├── llm/
│   │   ├── provider.py      # LLMProvider 추상
│   │   ├── claude_provider.py
│   │   └── codex_provider.py
│   ├── chunking/            # 청킹 전략
│   ├── embedding/           # 임베딩 wrapper
│   ├── vectorstore/         # 벡터 DB 어댑터
│   ├── prompts/             # 프롬프트 템플릿
│   ├── schemas.py           # Pydantic 모델
│   └── config.py            # 설정 로드
├── eval/                    # 평가 하네스
│   ├── golden_dataset.json
│   ├── run.py
│   └── metrics.py
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/
│   └── seed.sh              # 샘플 문서 시드
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
└── README.md
```

→ 1단계에서 다듬을 것. 여기 적은 건 윤곽.

## 7. 비동기 처리 — FastAPI를 고른 결정적 이유

PRD 평가 항목 "BE 설계 — **비동기 처리**" 20%.

FastAPI/asyncio를 쓰면 자연스럽게 만족:

```python
# 동기 (Flask 스타일) - 안 좋음
@router.post("/query")
def query(req):
    answer = call_llm(req.question)  # ← 5초 동안 워커 블로킹
    return answer

# 비동기 (FastAPI) - 좋음
@router.post("/query")
async def query(req):
    answer = await call_llm_async(req.question)  # ← 워커는 다른 요청 처리 가능
    return answer
```

LLM 호출은 5~30초까지 걸릴 수 있어 비동기 없이는 동시 요청 처리 불가.

## 8. 학습 곡선 완화 — 사용자가 Java 메인이므로

Java/Spring 경험이 Python/FastAPI에 매핑되는 부분:

| Spring | FastAPI 상응 | 비고 |
|---|---|---|
| `@RestController` | `@router.get/post` | 더 간단 |
| `@Service` | 일반 클래스 + DI | DI는 `Depends()` |
| `@Repository` | 일반 클래스 | ORM은 SQLAlchemy 또는 직접 |
| `@Autowired` | `Depends(get_xxx)` | 명시적 주입 |
| Bean Validation | Pydantic | 더 강력 |
| `application.yml` | `pydantic-settings` | 환경변수 자동 로드 |
| `@Transactional` | 컨텍스트 매니저 | 명시적 |
| Spring Profile | `.env` 파일 | 머신별 분리 |

→ 패러다임이 거의 같음. 문법만 다름. 1~2일이면 적응.

## 9. 위험 요소

| 위험 | 가능성 | 완화 |
|---|---|---|
| 사용자가 Python 관례 (venv, pyproject) 헷갈림 | 중 | CHECKLIST에 명시적 절차 |
| async와 sync 코드 섞여서 deadlock | 중 | "모든 I/O는 async" 규칙, sync 함수 호출 시 `run_in_executor` |
| Pydantic v1↔v2 API 차이 | 저 | 처음부터 v2 사용 |
| FastAPI dependency injection 과사용으로 가독성 ↓ | 저 | 단순 패턴 유지 |
| Mac과 Win에서 동일 코드가 다르게 동작 (path, 인코딩) | 중 | 절대경로 금지, UTF-8 강제, Docker로 런타임 통일 |

## 10. ARCHITECTURE.md 반영

이 결정은 `ARCHITECTURE.md`의 **"기술 스택 선택 이유"** 섹션의 핵심:

- 언어/프레임워크 선택 표 (위 2장)
- Python을 고른 결정적 이유 3가지: 생태계 / async / 채점 친화성
- 검토했으나 탈락한 후보 요약 (Java, Rust, Node)
- FastAPI vs Flask 비교 (비동기 처리 요구사항 충족)

## 11. 한 줄 요약

> **Python + FastAPI**. RAG 생태계가 Python에 집중되어 있고, FastAPI의 async가 LLM 호출에 최적이며, 8일 기한 안에 가장 빠르게 동작 가능한 조합. 사용자의 Java 경험은 패러다임이 거의 같아 1~2일이면 적응.
