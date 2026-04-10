# 00-prep — CONTEXT (결정 이력 + 제약 + 참고)

## 사용자 프로필

- AI/RAG 영역은 처음 접함 → 모든 결정에 "왜 이걸 골랐는지" 학습 문서 동반
- 평소 스택: Java/Spring (Poseidon, cross-platform 프로젝트). Python은 가능하나 메인은 아님
- 구독 보유: Claude Max + ChatGPT Pro (둘 다 사용 가능)
- **작업 환경**: 회사(Windows + WSL2) ↔ 집(Mac M2) 멀티 머신

## 결정 이력

### D1. LLM SDK는 Claude + Codex **둘 다 설치**, 역할 분할은 **데이터로 결정**

- **결정**: 두 SDK 모두 설치하고, `LLMProvider` 인터페이스로 추상화. 어느 모델을 어디에 쓸지는 **평가 하네스로 측정한 후 결정**한다.
- **잠정 가설**: 옵션 B (Claude=답변 생성, Codex=쿼리 재작성/요약 등 보조)
- **이유**:
  - 환각 억제·지시 추종에서 어느 모델이 우월한지에 대한 **신뢰할 만한 RAG 벤치마크가 없음** (인상론은 있으나 모델 버전마다 순위가 자주 바뀜)
  - 인상론으로 모델을 고르면 면접에서 약함 → "측정해서 결정했다"가 훨씬 강함
  - **평가 하네스 자체가 채점 항목**과 직결: "RAG 파이프라인 25%" + "프롬프트 엔지니어링 15%" + "LLM API 활용 20%"
  - `LLMProvider` 추상화는 1회 설계로 두 어댑터 swap 가능 → 추가 비용 작음
- **탈락 후보**:
  - 옵션 A (Claude 단독) — 안전하지만 차별화 부족
  - 옵션 C (완전 이중화) — 8일 일정에 과한 엔지니어링
- **다음 단계 액션**:
  - 1단계(아키텍처): `LLMProvider` 인터페이스 + 평가 하네스 **설계**
  - 4단계(RAG): 평가 하네스 **실행** → 데이터 기반 확정
- **상세 비교**: `.claude/knowledge/decisions/01-llm-sdk-claude-vs-codex.md`

### D2. 언어/프레임워크는 Python + FastAPI

- **결정**: Python 3.11+, FastAPI, uvicorn
- **이유**:
  - RAG 생태계가 Python에 압도적으로 집중 (sentence-transformers, chromadb, langchain, llama-index)
  - PRD가 FastAPI를 예시로 언급 ("BE 설계 — FastAPI 서버 설계")
  - 비동기 I/O 네이티브 지원 (LLM CLI 호출은 subprocess + async가 필수)
  - 사용자가 평소 Java를 쓰지만 학습 비용 < 생태계 이점
- **검토했으나 탈락한 후보**:
  - **Java + Spring** — 익숙하지만 RAG 라이브러리 부족, LLM CLI 통합 사례 적음
  - **Node + NestJS** — 가능하지만 임베딩/벡터 라이브러리 빈약
  - **Rust + Axum** — 성능과 차별화 매력은 있으나 ① `sentence-transformers` 등가물 부재(임베딩이 가장 큰 벽), ② PDF 텍스트 추출 라이브러리 약함, ③ 8일 기한 압박, ④ 사용자 미경험. 하이브리드(Rust+Python 사이드카)도 검토했으나 일정 대비 과함
- **상세**: `.claude/knowledge/decisions/02-language-framework.md`

### D3. 멀티 머신 (회사 Win + 집 Mac M2)

- **결정**:
  - 회사: WSL2 + **Ubuntu 24.04 신규 설치** (기존 20.04는 미사용)
  - 집: **macOS 네이티브** (Apple Silicon M2, Homebrew 사용)
- **이유**:
  - Ubuntu 20.04는 표준 지원 종료(2025-04), 기본 Python 3.8 → RAG 라이브러리 비호환
  - macOS는 Unix 계열 → claude-agent-sdk / codex CLI가 1순위 지원
  - Python 3.11+ + FastAPI는 두 환경에서 코드 변경 없이 동일하게 동작
- **공통 원칙**:
  - 모든 경로는 **상대경로**만 사용 (절대경로 금지)
  - 줄바꿈은 **LF 강제** (`.gitattributes`로 통일)
  - 환경변수는 `.env` 파일로 분리, 머신별 오버라이드는 `.env.local`

### D4. 임베딩 모델은 로컬 (sentence-transformers 유력)

- **결정**: 임베딩은 SDK가 아닌 별도 라이브러리. 기본 후보 `sentence-transformers`의 한국어 지원 모델
- **이유**:
  - claude-agent-sdk와 codex CLI 모두 **임베딩 엔드포인트를 제공하지 않음** (텍스트→텍스트만 지원)
  - PRD가 "오픈소스 임베딩 모델 자유 활용" 명시
  - 로컬 모델은 API 키 불요, 오프라인 동작
  - Mac M2 (Apple Silicon)에서는 Metal 가속도 가능
- **확정은 다음 단계** (`01-architecture`)에서 모델별 비교 후 결정

### D5. 벡터 DB / 캐시 DB는 다음 단계에서 결정

- 현 시점 **유력 후보**: Chroma (벡터), Redis (캐시)
- 이유는 다음 단계 아키텍처 문서에서 본격 비교

### N1. `.claude/` 폴더 git 추적 + 최종 제출 직전 히스토리에서 제거

- **결정**:
  - 작업 중에는 `.claude/` 전체를 **git 추적** (회사↔맥 자동 동기화)
  - 최종 제출 직전 **`git filter-repo --path .claude/ --invert-paths`** 로 히스토리 전체에서 제거 후 force push
- **이유**:
  - 멀티 머신 작업 → 동기화 필요. 별도 동기화 도구는 번거로움
  - 단순 `rm -rf .claude/` + commit은 **이전 커밋에 흔적이 그대로 남음** → 채점자가 GitHub에서 옛 커밋 열면 학습 노트가 다 보임
  - `git filter-repo`는 작업 흐름은 보존하면서 특정 경로만 히스토리에서 제거 가능 → 가장 깔끔
- **CHECKLIST에 "최종 제출 절차" 섹션으로 박아둠** — 잊지 말 것
- **검토했으나 탈락한 옵션**:
  - (가) `.claude/` ignore — 멀티 머신 동기화 안 됨
  - (나) 추적 + 그대로 둠 — 채점자에게 노이즈
  - (라) 별도 private 리포로 분리 — 리포 2개 관리 부담

### N2. Retrobot은 수동 실행만

- **결정**: `git config core.hooksPath .githooks` 실행하지 **않음**. 필요할 때만 `claude -p "$(cat retrobot/SKILL.md)"` 수동 호출
- **이유**:
  - Retrobot은 채점 항목이 아닌 부가 도구
  - 자동 회고 커밋이 git history에 섞이면 채점자가 진짜 작업 흐름을 보기 어려움
  - 매 커밋마다 LLM 호출 → 구독 쿼터 소비 + 커밋 속도 저하
  - 수동으로 두면 "보여주고 싶을 때만" 활용 가능
- **나중에 번복 가능**: 마지막에 어필 가치가 있다고 판단되면 활성화

### N3. `.gitattributes`로 LF 강제

- **결정**: 모든 텍스트 파일 LF, 셸 스크립트는 무조건 LF, Windows 전용 스크립트(`.bat`, `.ps1`)만 CRLF
- **이유**:
  - Windows는 CRLF, Mac은 LF가 기본 → 멀티 머신에서 충돌 빈발
  - 셸 스크립트가 CRLF면 Mac/WSL에서 실행 불가
  - git의 자동 변환에 의존하면 로컬마다 동작이 달라져 디버깅 어려움
- **파일**: `.gitattributes` (작성 완료 ✅)

## 새 리포지토리 변경사항 (Use this template)

이전 README는 "포크" 방식이었으나, 새 안내는 **GitHub "Use this template"** 방식. 이미 사용자가 GitHub UI에서 신규 리포 생성 + clone 완료한 상태. 우리 작업은 이 clone된 디렉토리(`D:\workspace-bsh\officeagent-onboarding-challenge`) 안에서 진행.

새 리포에서 함께 들어온 파일:
- `CLAUDE.md` / `AGENTS.md` — Claude/Codex용 프로젝트 지침. 우리 워크플로우와 충돌 X (서로 다른 층)
- `retrobot/` + `.githooks/post-commit` — 자동 회고 시스템. **N2에 따라 비활성**
- `docs/PRD.md` — 본문 동일
- `docs/TEMPLATE_GUIDE.md` — 디렉토리 구조 가이드 (참고용)
- `sample-docs/company-policy.txt`, `sample-docs/development-guide.md` — 골든 데이터셋 만들 원본

**중요**: `ARCHITECTURE.md`가 새 안내에서 **필수 산출물로 명시**됨 (이전 PRD에서는 권장 수준). 1단계(아키텍처) 산출물로 확정.

## 제약 조건

| # | 제약 | 영향 |
|---|---|---|
| C1 | 기한 2026-04-17 23:59 KST (8일) | 옵션 B 이상의 복잡도 회피 |
| C2 | `docker compose up` 한 줄 실행 필수 | 외부 SDK 의존성 처리 방식 신중 |
| C3 | API 키 사용 금지 (구독 기반만) | 임베딩은 로컬 모델로 강제 |
| C4 | LLM/에이전트 SDK 호출 필수 (불합격 기준) | 하드코딩 응답 금지 |
| C5 | 벡터 검색 + 캐시 DB 둘 다 필수 | 어느 하나 빠뜨리면 불합격 |
| C6 | "기존 OSS 통째 복사" 금지 | langchain/llama-index 등은 부분 활용만 |
| C7 | **필수 산출물 3개**: README, ARCHITECTURE, PROMPT_DESIGN | 단계별로 분산 작성 |
| C8 | **멀티 머신** 작업 (Win + Mac) | 절대경로 금지, LF 강제, 환경변수 분리 |

## 참고 자료

- 과제 PRD: [docs/PRD.md](../../../docs/PRD.md)
- 템플릿 가이드: [docs/TEMPLATE_GUIDE.md](../../../docs/TEMPLATE_GUIDE.md)
- 새 리포 README: [README.md](../../../README.md)
- 프로젝트 CLAUDE.md: [CLAUDE.md](../../../CLAUDE.md) (Claude/Codex가 읽는 프로젝트 지침)
- 학습 문서: `.claude/knowledge/`

## 주의

- 본 문서의 결정은 **이번 단계 시점의 결정**. 다음 단계에서 새 정보가 나오면 해당 단계의 CONTEXT.md에서 갱신/번복 가능
- 결정 번복 시 본 문서에 "**[갱신 YYYY-MM-DD]**" 표기로 흔적 남기기
