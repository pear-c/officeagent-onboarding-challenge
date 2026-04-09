# 00-prep — CHECKLIST

> 사용자가 직접 수행해야 하는 항목은 **[USER]**, AI(Claude)가 수행 가능한 항목은 **[AI]** 표시.

## 0. 리포지토리 설정 (회사 1회)

- [x] [AI] `.gitattributes` 생성 (LF 강제)
- [x] [AI] `.claude/tasks/00-prep/{PLAN,CONTEXT,CHECKLIST}.md` 작성
- [x] [AI] `.claude/knowledge/{concepts,decisions}/` 디렉토리 생성
- [ ] [AI] 학습 문서 4종 작성 (concepts 2개 + decisions 2개)
- [ ] [USER] 첫 커밋 + push (`.gitattributes`, `.claude/` 포함)

## 1. 회사(Windows) 환경 셋업

### 1-A. Ubuntu 24.04 신규 설치

- [ ] [USER] 관리자 권한 PowerShell에서 `wsl --install -d Ubuntu-24.04`
- [ ] [USER] 재부팅 (필요 시)
- [ ] [USER] Ubuntu 24.04 첫 실행 → username/password 설정
- [ ] [USER] `wsl -l -v`로 Ubuntu-24.04가 VERSION 2로 설치됐는지 확인
- [ ] [USER] (기본 배포판 변경 원하면) `wsl --set-default Ubuntu-24.04`

### 1-B. WSL 안에서 기본 패키지

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl build-essential
python3 --version  # 3.12.x 확인
```

- [ ] [USER] 위 명령 실행 → Python 3.12 확인

### 1-C. Docker Desktop WSL Integration

- [ ] [USER] Docker Desktop → Settings → Resources → WSL Integration → Ubuntu-24.04 토글 ON
- [ ] [USER] WSL 안에서 `docker --version` 동작 확인

### 1-D. Node.js 설치 (Codex CLI용)

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version  # v20.x 확인
```

- [ ] [USER] 위 명령 실행 → Node 20 확인

### 1-E. Claude Code SDK 설치

```bash
# CLI 먼저 설치 (Anthropic 공식 가이드 참조)
npm install -g @anthropic-ai/claude-code
claude --version

# Python SDK
pip install claude-code-sdk
```

- [ ] [USER] `claude` CLI 설치 + 첫 실행 시 Claude Max 계정으로 로그인
- [ ] [USER] `pip install claude-code-sdk` (혹은 venv 안에서)

### 1-F. Codex CLI 설치

```bash
npm install -g @openai/codex
codex --version
```

- [ ] [USER] `codex` 설치 + 첫 실행 시 ChatGPT Pro 계정으로 로그인

### 1-G. 작업 환경 전환 (사전준비 마무리 후)

> **결정**: 본격 개발은 **WSL Linux 측**에서 진행 (I/O 성능, 패키지 호환성). 사전준비 단계 문서/학습 문서는 **현재 Windows 측 폴더**에서 마무리하고 push 후, WSL 측에 새로 clone해서 1단계부터 WSL에서 작업.

- [ ] [USER] 사전준비 모든 작업이 끝났는지 확인 (이 CHECKLIST 1~5장)
- [ ] [USER] 회사 Windows 측에서 마지막 push 완료 (`git push`)
- [ ] [USER] WSL Ubuntu-24.04 안에서 새 디렉토리 + clone:
  ```bash
  mkdir -p ~/projects && cd ~/projects
  git clone https://github.com/<your-id>/officeagent-onboarding-challenge.git
  cd officeagent-onboarding-challenge
  python3 -m venv .venv && source .venv/bin/activate
  ```
- [ ] [USER] VSCode에 `Remote - WSL` 확장 설치
- [ ] [USER] WSL 터미널에서 `code .` 실행 → VSCode가 WSL 모드로 열리는지 확인
- [ ] [USER] 이후 모든 작업은 WSL 측 폴더(`~/projects/officeagent-onboarding-challenge`)에서 진행
- [ ] [USER] (선택) Windows 측 폴더(`D:\workspace-bsh\officeagent-onboarding-challenge`)는 백업 용도로 두거나 삭제

## 2. 집(Mac M2) 환경 셋업

### 2-A. macOS 버전 확인

```bash
sw_vers
```

- [ ] [USER] 결과 확인 (참고용, 거의 어떤 버전이든 OK)

### 2-B. Python 3.11+ 설치

```bash
brew install python@3.11
python3.11 --version
```

- [ ] [USER] Python 3.11+ 설치

### 2-C. Docker Desktop for Mac

- [ ] [USER] https://www.docker.com/products/docker-desktop/ 에서 Apple Silicon 버전 다운로드
- [ ] [USER] 설치 후 `docker --version` 확인

### 2-D. Node.js + Claude Code SDK + Codex CLI

```bash
brew install node
node --version

npm install -g @anthropic-ai/claude-code
claude --version
# 첫 실행 시 Claude Max 로그인

npm install -g @openai/codex
codex --version
# 첫 실행 시 ChatGPT Pro 로그인

pip install claude-code-sdk
```

- [ ] [USER] 위 명령 실행

### 2-E. git clone + 의존성 설치

```bash
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/<your-id>/officeagent-onboarding-challenge.git
cd officeagent-onboarding-challenge
python3.11 -m venv .venv && source .venv/bin/activate
# pip install -r requirements.txt   # 1단계 이후
```

- [ ] [USER] clone + venv 생성
- [ ] [USER] (1단계 이후) `pip install -r requirements.txt` (또는 `pyproject.toml`)
- [ ] [USER] (1단계 이후) `cp .env.example .env` 후 Mac용 값 작성
- [ ] [USER] (1단계 이후) `docker compose up -d`로 DB/캐시 컨테이너 시작

## 3. SDK Hello World 검증

### 3-A. Claude Code SDK 호출 테스트

```python
# 임시 파일: tmp/hello_claude.py
import asyncio
from claude_code_sdk import query, ClaudeCodeOptions

async def main():
    async for msg in query(
        prompt="안녕하세요. 간단히 한국어로 인사 한 줄만 해주세요.",
        options=ClaudeCodeOptions(max_turns=1),
    ):
        print(msg)

asyncio.run(main())
```

- [ ] [AI/USER] 위 스크립트 작성 + 실행 → Claude의 응답 확인
- [ ] [USER] 회사 머신에서 검증
- [ ] [USER] 집 머신에서도 검증

### 3-B. Codex CLI 호출 테스트

```bash
codex "안녕하세요. 간단히 한국어로 인사 한 줄만 해주세요."
```

- [ ] [USER] 회사 머신에서 검증
- [ ] [USER] 집 머신에서 검증

## 4. 프로젝트 스켈레톤 (다음 단계 1-architecture 들어가기 전 최소 준비)

> 이 단계에서는 **빈 디렉토리만** 만들고, 실제 코드는 1단계 이후에 작성.

```
officeagent-onboarding-challenge/
├── app/                    # FastAPI 애플리케이션 (1단계에서 채움)
├── eval/                   # 평가 하네스 (1단계에서 설계, 4단계에서 채움)
├── tests/
├── docker-compose.yml      # 1단계에서 작성
├── pyproject.toml          # 1단계에서 작성
└── .env.example            # 1단계에서 작성
```

- [ ] [AI] 1단계 진입 시 위 스켈레톤 생성

## 5. 학습 문서 작성

- [ ] [AI] `.claude/knowledge/concepts/01-rag-overview.md` — RAG 전체 개념
- [ ] [AI] `.claude/knowledge/concepts/02-embedding-vector-search.md` — 임베딩과 벡터 검색
- [ ] [AI] `.claude/knowledge/decisions/01-llm-sdk-claude-vs-codex.md` — Claude vs Codex 비교
- [ ] [AI] `.claude/knowledge/decisions/02-language-framework.md` — Python/FastAPI 선택 이유

## 6. 사전준비 단계 완료 조건

이 단계가 끝났다고 선언하려면 아래가 모두 true여야 함:

- [ ] `.claude/tasks/00-prep/`의 PLAN/CONTEXT/CHECKLIST 모두 작성됨
- [ ] `.claude/knowledge/`의 학습 문서 4개 모두 작성됨
- [ ] 사용자가 학습 문서를 읽고 RAG 개념과 모델 비교를 이해함
- [ ] 회사 WSL Ubuntu-24.04 설치 + Python/Node/Docker 동작 확인
- [ ] 회사 머신에서 Claude/Codex hello-world 둘 다 동작
- [ ] 회사 Windows → WSL 측 디렉토리로 git clone 전환 완료 (1-G)
- [ ] git push 1회 이상 완료 (다음 단계에서 Mac 동기화 검증 가능)
- [ ] (집에서 작업할 때) Mac 셋업 + Claude/Codex hello-world 둘 다 동작 ← 집 도착 후 수행

## 7. 최종 제출 직전 절차 (잊지 말 것!) ⚠️

> 이 섹션은 **모든 작업이 끝난 후, 최종 제출 직전**에만 실행. 사전준비 단계와 직접 관련은 없지만 N1 결정에 따라 여기 명시.

### 7-A. 산출물 점검

- [ ] `README.md` 최신화 (실행 방법 + 아키텍처 요약)
- [ ] `ARCHITECTURE.md` 완성 (필수 산출물)
- [ ] `PROMPT_DESIGN.md` 완성 (필수 산출물)
- [ ] `docker compose up` 한 줄로 실행 가능한지 깨끗한 환경에서 검증

### 7-B. `.claude/` 히스토리 제거

```bash
# git filter-repo 설치 (mac)
brew install git-filter-repo
# 또는 pip
pip install git-filter-repo

# 작업 디렉토리 백업 권장
cp -r ../officeagent-onboarding-challenge ../officeagent-backup

# .claude/ 를 모든 히스토리에서 제거
git filter-repo --path .claude/ --invert-paths

# remote 재설정 (filter-repo가 origin을 지움)
git remote add origin https://github.com/<your-id>/officeagent-onboarding-challenge.git

# 강제 push
git push -f origin main
```

- [ ] [USER] 위 절차 실행
- [ ] [USER] GitHub UI에서 `.claude/` 폴더가 사라졌는지 확인
- [ ] [USER] 과거 커밋 몇 개 열어서 `.claude/` 흔적 없는지 확인

### 7-C. Collaborator 초대

- [ ] [USER] GitHub repo Settings → Collaborators → `serithemage` 초대
