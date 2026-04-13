# Document Q&A API

문서를 업로드하면 텍스트를 분석하고, 사용자 질문에 대해 **문서 근거 기반 답변**을 생성하는 RAG REST API 서버.

## 빠른 시작

```bash
# 1. 클론
git clone <repo-url> && cd officeagent-onboarding-challenge

# 2. 실행 (Docker만 있으면 됨)
docker compose up -d

# 3. 샘플 문서 업로드 (서버 준비될 때까지 자동 대기)
chmod +x scripts/seed.sh && ./scripts/seed.sh

# 4. 브라우저에서 테스트
open http://localhost:8000
```

> 첫 실행 시 임베딩 모델(bge-m3, 2.3GB) 다운로드로 2~3분 소요됩니다.
> `docker compose logs -f app`으로 "리소스 초기화 완료" 메시지를 확인하세요.

## 데모 시나리오

### 웹 UI (`http://localhost:8000`)

1. 문서 업로드 (드래그 앤 드롭)
2. 질문 입력 → **출처가 먼저 표시** → 답변이 실시간 스트리밍
3. 같은 질문 재입력 → **캐시 히트** (지연시간 대폭 감소)

### API 직접 호출

```bash
# 문서 업로드
curl -X POST http://localhost:8000/api/v1/documents \
  -F "file=@sample-docs/company-policy.txt"

# 질의응답 (JSON)
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "교육비 지원 한도는 얼마인가요?"}'

# 질의응답 (SSE 스트리밍)
curl -N -X POST http://localhost:8000/api/v1/query/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "재택근무 조건이 어떻게 되나요?"}'
```

## 기술 스택

| 영역 | 선택 |
|------|------|
| 프레임워크 | Python 3.12 + FastAPI |
| 임베딩 | BAAI/bge-m3 (sentence-transformers) |
| 벡터 DB | Chroma |
| 캐시 | Redis 7 |
| LLM (기본) | Codex (OpenAI, codex CLI) |
| LLM (fallback) | Claude Sonnet 4.6 (claude-agent-sdk) |
| 컨테이너 | Docker Compose |

> LLM 역할 분할은 50케이스 평가 하네스 측정 결과로 확정.
> 자세한 내용: [PROMPT_DESIGN.md](./PROMPT_DESIGN.md)

## API 엔드포인트

| Method | Path | 역할 |
|--------|------|------|
| `POST` | `/api/v1/documents` | 문서 업로드 (.txt, .md, .pdf) |
| `GET` | `/api/v1/documents` | 업로드된 문서 목록 |
| `POST` | `/api/v1/query` | 질의응답 (JSON) |
| `POST` | `/api/v1/query/stream` | 질의응답 (SSE 스트리밍) |
| `GET` | `/health` | 헬스체크 |
| `GET` | `/docs` | OpenAPI (Swagger) 문서 |

## 평가 하네스

```bash
# 서버 실행 상태에서 별도 터미널
python eval/run.py run --provider claude     # Claude 측정 (~12분)
python eval/run.py run --provider codex      # Codex 측정 (~12분)
python eval/run.py compare eval/results/*.json   # 비교 표 출력
```

50케이스 (7난이도) x 7메트릭으로 LLM 성능을 비교 측정합니다.

## 주요 설계 문서

| 문서 | 내용 |
|------|------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 시스템 아키텍처 + 기술 선택 근거 + 측정 결과 |
| [PROMPT_DESIGN.md](./PROMPT_DESIGN.md) | 프롬프트 설계 + Claude vs Codex 비교 분석 |
| [docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) | 트러블슈팅 기록 + 면접 포인트 |

## 개발 모드 (Docker 없이)

```bash
# DB만 Docker
docker compose up -d chroma redis

# Python 환경
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # 필요 시 수정

# 서버 실행
uvicorn app.main:app --reload --port 8000

# 테스트
pytest tests/ -v
```
