# Document Q&A API

문서를 업로드하면 텍스트를 분석하고, 사용자 질문에 대해 **문서 근거 기반 답변**을 생성하는 RAG REST API 서버.

## 사전 요구사항

- **Docker + Docker Compose** (Chroma, Redis 실행용)
- **Python 3.12+** (앱 실행용)
- **LLM CLI** (아래 중 하나 이상):
  - Claude Code CLI: `npm install -g @anthropic-ai/claude-code` + `claude` 로그인 완료
  - Codex CLI: `npm install -g @openai/codex` + `codex` 로그인 완료

> LLM은 Claude Pro/Max 또는 ChatGPT Pro 구독 기반입니다 (PRD 명시).
> CLI 로그인이 되어있으면 별도 API 키 없이 동작합니다.

## 빠른 시작 (한 줄 실행)

```bash
git clone <repo-url> && cd officeagent-onboarding-challenge
chmod +x start.sh && ./start.sh
```

이 스크립트가 자동으로:
1. Chroma + Redis 실행 (Docker)
2. Python 가상환경 + 의존성 설치
3. 서버 시작 (임베딩 모델 첫 로딩 시 ~2분)
4. 샘플 문서 2개 업로드 (company-policy.txt, development-guide.md)

완료되면 `http://localhost:8000`에서 바로 테스트 가능합니다.
추가 문서(PDF, MD, TXT)는 웹 UI에서 드래그 앤 드롭으로 업로드하세요.

### LLM 설정

`start.sh`가 설치된 CLI를 자동 감지하여 `.env`를 설정합니다:

- **Claude CLI + Codex CLI 모두 설치** → Claude 사용 (기본)
- **Codex CLI만 설치** → Codex로 자동 전환
- **둘 다 미설치** → 에러 메시지 + 설치 안내 후 종료

수동으로 변경하려면 `.env`를 직접 수정하세요:

```env
# Claude 사용 시 (기본값)
LLM_ANSWER_PROVIDER=claude

# Codex 사용 시
LLM_ANSWER_PROVIDER=codex
```

### 수동 실행 (단계별)

```bash
# 1. DB 실행
docker compose up -d chroma redis

# 2. Python 환경
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env

# 3. 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. (별도 터미널) 샘플 문서 업로드
chmod +x scripts/seed.sh && ./scripts/seed.sh
```

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
| LLM (기본) | Claude Sonnet 4.6 (claude-agent-sdk) |
| LLM (대안) | Codex (OpenAI, codex CLI) |
| 컨테이너 | Docker Compose |

> LLM 선택: 자동 평가(50케이스) + UI 비교로 Claude를 기본 모델로 확정.
> 자세한 내용: [ARCHITECTURE.md](./ARCHITECTURE.md) 3.6절

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
source .venv/bin/activate
python eval/run.py run --provider claude     # Claude 측정 (~12분)
python eval/run.py run --provider codex      # Codex 측정 (~12분)
python eval/run.py compare eval/results/*.json   # 비교 표 출력
```

50케이스 (7난이도) x 7메트릭으로 LLM 성능을 비교 측정합니다.

## 주요 설계 문서

| 문서 | 내용 |
|------|------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 시스템 아키텍처 + 기술 선택 근거 + LLM 비교 + 평가 하네스 |
| [PROMPT_DESIGN.md](./PROMPT_DESIGN.md) | 프롬프트 설계 (시스템 프롬프트, 스트리밍 분리, 튜닝 히스토리) |
| [docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) | 트러블슈팅 기록 + 면접 포인트 (10개) |

## 종료

```bash
# 서버 종료 (Ctrl+C 또는)
kill $(lsof -ti:8000) 2>/dev/null

# DB 종료
docker compose down

# DB + 데이터 전부 삭제 (초기화)
docker compose down -v
```
