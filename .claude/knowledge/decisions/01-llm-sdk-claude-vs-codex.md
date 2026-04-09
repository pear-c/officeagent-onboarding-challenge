# Decision 01. LLM SDK 선택 — Claude Code SDK vs Codex CLI

> **결정**: 둘 다 설치하고 `LLMProvider`로 추상화. 역할 분할은 평가 하네스로 측정 후 확정.
> **잠정 가설**: Claude=답변 생성 / Codex=보조 작업.

## 1. 두 SDK가 무엇인가

PRD가 허용한 LLM 옵션은 둘 뿐:

| SDK | 패키지 | 모델 제공처 | 구독 |
|---|---|---|---|
| **Claude Code SDK** | `pip install claude-code-sdk` (Python) | Anthropic Claude | Claude Pro/Max |
| **Codex CLI** | `npm install -g @openai/codex` (Node) | OpenAI GPT | ChatGPT Pro |

**중요한 공통 특성**:
- 둘 다 **API 키를 사용하지 않음** (구독 기반)
- 둘 다 **로컬에 설치된 CLI 도구를 프로그래밍 방식으로 호출**하는 형태
  - Claude Code SDK = `claude` CLI를 Python에서 spawn
  - Codex CLI = 그 자체가 CLI, 다른 언어에서 부르려면 subprocess
- 둘 다 **임베딩 함수 제공 X** (텍스트→텍스트 전용)
- 둘 다 **첫 실행 시 OAuth 로그인** 필요

## 2. 모델 라인업

각 SDK 뒤에 있는 모델 (2026-04 시점):

### Claude (Anthropic)

| 모델 | 강점 | 약점 | 우리 과제 적합성 |
|---|---|---|---|
| **Opus 4.6** | 최고 추론, 1M 컨텍스트 | 느림, 토큰 비용 ↑ | 답변 생성 |
| **Sonnet 4.6** | 균형, 1M 컨텍스트 | — | **답변 생성 (1순위)** |
| **Haiku 4.5** | 빠름, 저렴 | 복잡한 추론 약함 | 보조 작업, 분류, 정규화 |

### OpenAI (Codex 경유)

| 모델 | 강점 | 약점 | 우리 과제 적합성 |
|---|---|---|---|
| **GPT-5** | 최신 플래그십 | 느림 | 답변 생성 후보 |
| **GPT-5 mini** | 빠름, 저렴 | 약간의 정확도 손실 | **보조 작업 (1순위)** |

> 모델 버전과 라인업은 자주 바뀜. 실제 SDK가 어떤 모델을 노출하는지는 1단계에서 검증.

## 3. 작동 방식 비교

### 3-A. Claude Code SDK (Python)

```python
import asyncio
from claude_code_sdk import query, ClaudeCodeOptions

async def ask_claude(prompt: str) -> str:
    chunks = []
    async for msg in query(
        prompt=prompt,
        options=ClaudeCodeOptions(max_turns=1, model="claude-sonnet-4-6"),
    ):
        chunks.append(msg)
    return chunks[-1].text  # 단순화

asyncio.run(ask_claude("연차는 며칠?"))
```

**특징**:
- 네이티브 Python async 지원
- `claude` CLI를 백그라운드에서 띄우고 stdin/stdout으로 통신
- streaming 지원 (`async for`)
- `ClaudeCodeOptions`로 모델, max_turns, allowedTools 등 조절

### 3-B. Codex CLI (Node 기반)

```python
import asyncio

async def ask_codex(prompt: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        "codex", "--quiet", prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    return stdout.decode()
```

**특징**:
- 별도 Python SDK 없음 → `subprocess`로 호출
- streaming 어려움 (line 단위로 읽으면 됨)
- `--quiet` 옵션으로 노이즈 제거

## 4. 각 SDK의 장단점

### Claude Code SDK

**장점**:
- ✅ Python 네이티브 SDK 존재 → async 통합 매끄러움
- ✅ Anthropic이 RAG 친화적 (XML 태그 사용 권장 등 가이드 풍부)
- ✅ 1M 컨텍스트 → 매우 큰 문서도 한 번에 처리 가능
- ✅ 출력 안정성 평판 우수 (지시 추종 강함)
- ✅ Sonnet은 균형이 좋아 응답 시간/품질 모두 무난

**단점**:
- ❌ Codex보다 응답 속도 약간 느림 (Sonnet 기준)
- ❌ Opus는 비싸고 느림 → 답변 생성 외에는 부적합
- ❌ Windows 네이티브 환경에서 가끔 경로/권한 이슈 (WSL/Mac 권장)
- ❌ Python SDK가 비교적 신생 → API가 바뀔 가능성

### Codex CLI

**장점**:
- ✅ 응답 속도 빠름 (특히 GPT-5 mini)
- ✅ ChatGPT Pro 구독자라면 별도 비용 없음
- ✅ JSON 모드 강력 (구조화 출력 안정적)
- ✅ Function calling 패러다임 익숙

**단점**:
- ❌ Python 네이티브 SDK 부재 → subprocess로만 호출 가능 (boilerplate 많음)
- ❌ streaming 처리 까다로움
- ❌ Codex CLI는 본래 코드 작업용 → 일반 Q&A 사용 사례 문서가 적음
- ❌ 시스템 메시지 주입이 SDK보다 명시적이지 않을 수 있음
- ❌ stdout 파싱 시 색상 코드/프롬프트 노이즈 처리 필요

## 5. 역할 분할 — 잠정 가설 (옵션 B)

**가설**: 답변 생성은 정확도 우선, 보조 작업은 속도 우선이다. 이 가설이 맞으면:

| 단계 | 모델 | 이유 (가설) |
|---|---|---|
| 쿼리 재작성 (HyDE 등) | Codex (GPT-5 mini) | 짧고 빠름. 정확도가 검색 품질에 약간만 영향 |
| 캐시 키 정규화 (선택) | Codex (GPT-5 mini) | bulk 처리, 속도 중요 |
| 검색 결과 reranking | Claude (Haiku) 또는 Codex | 짧은 입력 + 판단력 |
| **최종 답변 생성** | **Claude (Sonnet 4.6)** | 환각 억제 + 출처 인용 + 지시 추종 |
| (선택) Self-check | Claude (Sonnet) | 답변 검증, 동일 모델로 자기 검증 |

→ **이 표는 가설이지 결정이 아닙니다.** 4단계에서 평가 하네스로 측정하면 다음 가능성도 있습니다:
- (a) 둘 다 비슷함 → 더 빠른 Codex로 통일 (시간 단축)
- (b) Claude가 모든 작업에서 우월 → Claude로 통일 (단순화)
- (c) 가설대로 → 옵션 B 확정
- (d) 반대로 Codex가 답변 생성에 더 좋음 → Codex가 메인

## 6. 추상화 설계 — `LLMProvider` 인터페이스

두 SDK를 같은 인터페이스로 감싸 코드에서는 1줄 변경으로 swap 가능하게 만든다.

```python
# app/llm/provider.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator

@dataclass
class LLMResponse:
    text: str
    model: str
    latency_ms: int
    raw: dict | None = None

class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        system: str,
        user: str,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> LLMResponse: ...

    @abstractmethod
    async def stream(
        self,
        system: str,
        user: str,
    ) -> AsyncIterator[str]: ...

# app/llm/claude_provider.py
class ClaudeProvider(LLMProvider):
    async def generate(self, system, user, max_tokens=1024, json_mode=False):
        # claude_code_sdk.query(...) 호출
        ...

# app/llm/codex_provider.py
class CodexProvider(LLMProvider):
    async def generate(self, system, user, max_tokens=1024, json_mode=False):
        # subprocess로 codex 호출
        ...
```

**사용**:

```python
# 환경변수 또는 설정으로 swap
PROVIDERS = {
    "answer": ClaudeProvider(model="sonnet"),
    "auxiliary": CodexProvider(model="gpt-5-mini"),
}

# 호출 코드는 어느 모델인지 모름
answer = await PROVIDERS["answer"].generate(system=..., user=...)
```

이 추상화의 이점:
1. **swap 비용 0** — 평가 하네스가 단순히 provider만 바꿔서 두 모델 모두 측정
2. **테스트 용이** — Mock provider로 단위 테스트 가능
3. **로깅/메트릭 일원화** — provider 안에서 latency, token 사용량 기록

## 7. 평가 하네스 측정 계획 (4단계)

골든 케이스 ~20개를 두 모델에 던져 다음을 측정:

| 메트릭 | 측정 방법 |
|---|---|
| Retrieval Hit Rate | (모델과 무관, 검색 단계) |
| **Citation Accuracy** | 답변이 인용한 chunk_id가 정답 chunk_id와 일치하는가 |
| **Refusal Accuracy** | answerable=false 케이스에서 정확히 거절했는가 |
| **Answer Similarity** | 답변 텍스트가 정답 키워드를 포함하는가 (rough) |
| **Latency p50/p95** | 응답 시간 분포 |
| **JSON Parse Rate** | 구조화 출력이 깨지지 않은 비율 |

→ 측정 결과 표를 `PROMPT_DESIGN.md`에 첨부하면 면접에서 "왜 이 모델 골랐어요?" 답이 자동으로 나옴.

## 8. 위험 요소

| 위험 | 가능성 | 완화 |
|---|---|---|
| 두 SDK 모두 환경 설정에 시간 많이 듦 | 중 | 사전준비 단계에서 hello world 검증 (CHECKLIST) |
| Codex CLI의 한국어 처리 의외로 약함 | 저 | 측정으로 확인. 약하면 옵션 B 가설 강화 |
| Claude SDK가 Python 3.12에서 일부 API deprecated | 저 | 1단계에서 버전 호환성 확인 |
| 구독 쿼터 초과 | 저 | 평가 하네스 케이스 수 제한 (20개), 캐시 활용 |
| 두 모델 모두 비슷한 결과 → 차별화 못 함 | 중 | 결과가 비슷하면 그 자체를 데이터로 활용 ("측정 결과 차이 미미해 비용/속도로 결정") |

## 9. 검토했으나 탈락한 옵션

### 옵션 A. Claude 단독 사용
- ✅ 단순. 어댑터 1개만 구현
- ❌ "왜 Claude만?"에 답이 약함 (인상론에 의존)
- ❌ Codex 비교 가산점 못 받음
- → 시간이 진짜 부족하면 fallback으로 가능

### 옵션 C. 완전 이중화 (모든 호출을 두 모델에)
- ✅ 답변 품질 비교 가능, A/B 테스트 가능
- ❌ 토큰 비용/시간 2배
- ❌ 응답 시간 느려짐 (둘 다 기다림 또는 병렬 + 결과 합치기)
- ❌ 8일에 과한 엔지니어링
- → 면접 어필용으로 매력적이지만 ROI 낮음

### 옵션 D. SDK 1개만 쓰되 모델만 다중화
- 예: Claude만 쓰되 Sonnet/Haiku 두 모델로 역할 분할
- ✅ 어댑터 1개로 충분
- ❌ "두 SDK 다 써봤다"는 실험 가치 상실
- ❌ 사용자 의도(둘 다 활용)에 부합 X

## 10. 최종 결정 (현 시점)

| 항목 | 결정 |
|---|---|
| 어떤 SDK를 설치할 것인가? | **둘 다** |
| 코드에서 어떻게 부를 것인가? | `LLMProvider` 인터페이스 + Claude/Codex 어댑터 2개 |
| 어느 모델을 어디에 쓸 것인가? | **잠정**: 답변=Claude Sonnet, 보조=Codex GPT-5 mini. **확정은 4단계 평가 하네스 결과 후** |
| 어디까지 평가할 것인가? | 골든 20케이스, 6가지 메트릭, 1회 측정 후 프롬프트 1~2회 튜닝 |
| 폴백 시나리오는? | 측정 결과 차이 미미 → Claude 단독으로 단순화 |

## 11. ARCHITECTURE.md 반영 항목

이 결정은 최종 산출물 `ARCHITECTURE.md`에 다음과 같이 들어갑니다:

- **LLM SDK 선택 이유** 섹션: 위 6장의 설계 배경
- **`LLMProvider` 인터페이스 다이어그램**: 클래스 관계도
- **모델 역할 분할 표**: 4단계 측정 결과 반영 후 최종 표
- **평가 하네스 결과 요약**: PROMPT_DESIGN.md에 상세, ARCHITECTURE에는 한 줄 요약 + 링크

## 12. 한 줄 요약

> **두 SDK 다 설치, `LLMProvider`로 추상화, 역할 분할은 측정 결과로 결정.**
> 인상론으로 모델 고르지 말고 데이터로 골라라.
