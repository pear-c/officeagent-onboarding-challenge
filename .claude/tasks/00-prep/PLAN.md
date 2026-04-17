# 00-prep — 사전준비 단계

## 목표

본격적인 RAG Q&A API 구현에 들어가기 전, **개발 환경과 기술 스택을 확정하고 검증**한다.
이 단계가 끝나면 다음을 만족해야 한다:

- WSL2 Ubuntu 24.04 환경에서 Python·Node가 동작한다
- Claude Code SDK / Codex CLI 두 도구로 hello-world 호출이 성공한다
- 기술 스택 선택 이유가 학습 문서로 정리되어 있다 (면접 대비)
- 다음 단계(아키텍처 설계)로 넘어갈 수 있는 빈 프로젝트 스켈레톤이 있다

## 범위

| 포함 | 제외 |
|---|---|
| 환경 설치, SDK 검증, 폴더 스켈레톤 | RAG 파이프라인 구현 |
| 기술 비교 학습 문서 작성 | 실제 API 엔드포인트 코드 |
| 동작하는 Python `hello world` 스크립트 | Docker Compose 작성 |
| `.gitignore`에 `.claude/` 추가 | `ARCHITECTURE.md` 작성 (1단계에서) |

## 결정된 기술 스택

| 항목 | 선택 | 이유 문서 |
|---|---|---|
| OS | WSL2 + **Ubuntu 24.04** (신규 설치) | 본 PLAN의 "환경" 섹션 |
| 언어 | **Python 3.11+** | `knowledge/decisions/02-language-framework.md` |
| 웹 프레임워크 | **FastAPI** | 동상 |
| LLM SDK | **Claude Code SDK + Codex CLI 둘 다 설치** (역할 분할은 잠정) | `knowledge/decisions/01-llm-sdk-claude-vs-codex.md` |
| ↳ 역할 분할 최종 확정 | **2단계(아키텍처)에서 평가 하네스 설계 → 4단계(RAG)에서 측정 후 결정** | — |
| 임베딩 | **sentence-transformers** (로컬) | 다음 단계(아키텍처)에서 상세화 |
| 벡터 DB | (다음 단계에서 결정 — Chroma 유력) | — |
| 캐시 DB | (다음 단계에서 결정 — Redis 유력) | — |

## 환경 (멀티 머신: 회사 Windows + 집 Mac)

작업은 두 머신에서 번갈아 진행:

### 회사 (Windows)
- WSL2 + **Ubuntu 24.04 신규 설치**
- 기존 Ubuntu-20.04는 표준 지원 종료(2025-04), Python 3.8 → 부적합
- `docker-desktop` 배포판은 직접 작업 X (Docker Desktop 내부용)
- Docker Desktop의 WSL Integration을 24.04에 활성화

### 집 (Mac, Apple Silicon M2)
- **macOS 네이티브** (WSL 불필요)
- Homebrew로 Python 3.11+ 설치
- Docker Desktop for Mac (ARM64 네이티브)
- 환경 셋업이 회사보다 간단

### 두 머신 공통 원칙
- **모든 경로는 상대경로** (절대경로 박지 말 것)
- **줄바꿈은 LF 강제** (`.gitattributes`로 통일)
- **`.claude/` 폴더 git 추적** (회사↔맥 자동 동기화) — 최종 제출 직전 `git filter-repo`로 히스토리에서 제거

## 새 리포지토리 변경사항 반영

새 안내사항(Use this template + Retrobot)에 따른 조정:

| 변경점 | 우리 작업에 미치는 영향 | 결정 |
|---|---|---|
| `Use this template`로 신규 리포 생성 | 사용자가 GitHub UI에서 직접 수행 (이미 완료됨) | — |
| `CLAUDE.md`/`AGENTS.md` 기존재 | 우리 워크플로우와 충돌 X. 그대로 둠 | 변경 없음 |
| `ARCHITECTURE.md`가 **필수 산출물**로 명시 | 1단계 산출물로 확정 | 1단계 PLAN에 반영 |
| `retrobot/` + `.githooks/` | 자동 회고 시스템 | **수동 실행만 사용** (`git config core.hooksPath .githooks` 미실행) |
| `.gitignore`에 `.claude/` 없음 | 멀티 머신 동기화 vs 채점자 노출 trade-off | **`.claude/` git 추적** + 최종 제출 직전 `git filter-repo`로 히스토리에서 완전 제거 |
| 멀티 머신 (Win + Mac) 줄바꿈 차이 | CRLF/LF 충돌 위험 | **`.gitattributes`로 LF 강제** |

## 산출물

- `.gitattributes` 생성 (LF 강제)
- `.gitignore`는 `.claude/` 추가하지 **않음** (멀티 머신 동기화)
- `.claude/tasks/00-prep/{PLAN,CONTEXT,CHECKLIST}.md`
- `.claude/knowledge/concepts/01-rag-overview.md`
- `.claude/knowledge/concepts/02-embedding-vector-search.md`
- `.claude/knowledge/decisions/01-llm-sdk-claude-vs-codex.md`
- `.claude/knowledge/decisions/02-language-framework.md`
- 동작 검증된 dev 환경 (사용자가 CHECKLIST 따라 수행)

## 다음 단계

### `01-architecture` — 시스템 아키텍처 설계
- 레이어 구조 (FastAPI 라우터/서비스/리포지토리)
- RAG 파이프라인 흐름도
- 벡터 DB·캐시 DB 최종 결정 + 비교 문서
- **`LLMProvider` 추상화 인터페이스 설계** (Claude/Codex 1줄 swap 가능하도록)
- **평가 하네스(eval harness) 설계** — 골든 데이터셋 구조, 메트릭 정의(Retrieval Hit / Citation Accuracy / Refusal Accuracy / Latency), 실행 방식
- **`ARCHITECTURE.md` 초안 작성** (필수 제출 산출물)

### `04-rag-pipeline` (예정) — RAG 최소 동작 시점에:
- 평가 하네스 **실행** → Claude vs Codex 측정
- 데이터 기반으로 모델 역할 분할 **최종 확정** (D1 결정 확정/번복)
- 결과 표를 `PROMPT_DESIGN.md`에 첨부 (면접 시 근거)

> **D1 결정의 위상**: 현재는 "**잠정 가설** = 옵션 B(역할 분할)". 평가 하네스 측정 전까지는 임시. 측정 결과가 다르면 단일 모델로 통일하거나 역할을 뒤바꿀 수 있음.
