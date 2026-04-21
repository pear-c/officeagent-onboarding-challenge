# Agentic RAG vs 구독형 SDK 기반 RAG — 개념 정리

> 면접 전 개념 명확화용. 두 용어는 **서로 다른 축**이라 그대로 비교하면 안 됨.

---

## 0. 핵심 요약 — 두 축은 직교(orthogonal)한다

둘은 "vs" 관계가 아니라 **다른 차원**에 있습니다.

| 축 | 질문 | 선택지 |
|----|------|--------|
| **① RAG 파이프라인 아키텍처** | "검색·답변을 어떻게 조립하는가?" | Naive RAG ↔ Advanced RAG ↔ **Agentic RAG** |
| **② LLM 조달 방식** | "LLM을 어떻게 부르는가?" | 구독형 SDK ↔ API 직접 호출 ↔ 오픈소스 로컬 호출 |

두 축은 독립적이라 **조합이 가능**합니다:

|  | Naive RAG | Agentic RAG |
|----|-----------|-------------|
| **구독 SDK** | ← 내 과제 | 가능 (드묾) |
| **API 직접** | 전형적 RAG 튜토리얼 | **대부분의 프로덕션** |
| **로컬 LLM** | 오프라인 RAG | ← **오피스에이전트 추정** |

따라서 "Agentic RAG vs 구독 SDK RAG"는 **"자동차 세단 vs 디젤 자동차"** 같은 비교입니다. 진짜 질문은 두 가지를 분리해서 봐야 합니다.

---

## 1. 축 ① — RAG 파이프라인 아키텍처

### 1.1 Naive RAG (내 과제의 방식)

```
질문 → embed → top-K retrieve → LLM 1회 호출 → 답변
```

**특징:**
- 단일 패스. LLM은 최종 답변 생성 단 한 번만 호출
- 검색 품질이 **질문 표현에 민감** (짧은 질문, 동의어 처리 약함)
- 복합 질문(multi-hop)에 약함 ("A와 B를 비교하면?")
- 속도 빠름, 비용 낮음

**내 과제에서 구현한 부분:**
- [app/services/rag_service.py](../app/services/rag_service.py) — `embed → Chroma 검색 → LLM 호출 → 캐시 저장`

### 1.2 Advanced RAG (중간 단계)

LLM을 에이전트로 쓰지 않지만, 파이프라인을 다단계로 고도화한 형태.

**주요 기법:**
- **Query Expansion**: 질문을 embedding 전에 동의어/유사어로 확장
- **Reranking**: 벡터 검색 top-K 결과를 cross-encoder로 재정렬
- **HyDE**: LLM이 "가상 답변"을 먼저 만들고, 그 답변의 임베딩으로 검색
- **Hybrid Search**: 벡터 검색 + BM25 키워드 검색 결합

**특징:** 파이프라인은 고정(결정론적). LLM은 보조 역할.

### 1.3 Agentic RAG (오피스에이전트가 주장하는 것)

```
질문 도착
  ↓
[LLM: 의도 분석] "이게 단순 질문인가, 복합 질문인가?"
  ↓
[LLM: 질문 재작성] "검색에 쓸 쿼리로 바꿔라"
  ↓
retrieve (1차)
  ↓
[LLM: 충분성 판단] "이 청크들로 답할 수 있나?"
  ├─ No → 쿼리 변형 후 재검색 (반복)
  └─ Yes ↓
[LLM: 답변 생성]
  ↓
[LLM: 자가 검증] "내 답변이 문서에 근거 있나?"
  ├─ No → 거절하거나 다시 답변
  └─ Yes → 최종 반환
```

**핵심 차이점:**
- LLM이 **파이프라인을 조율(orchestrate)** 한다
- LLM이 **의사결정 분기**를 한다 (재검색? 거절? 재시도?)
- LLM이 여러 번 호출된다 (3~10회)
- 동적 제어 흐름 (입력에 따라 경로가 바뀜)

**구현 프레임워크:**
- **LangGraph** (LangChain) — 상태 그래프로 에이전트 흐름 정의
- **LlamaIndex Agent** — ReAct, Plan-and-Execute 패턴
- **Haystack Agents** — 파이프라인 내 분기

### 1.4 Naive vs Agentic 비교표

| 항목 | Naive RAG | Agentic RAG |
|------|-----------|-------------|
| LLM 호출 수 | 1회 | 3~10회 |
| 검색 단계 | 1회 | 1~N회 (반복) |
| 복합 질문 처리 | 약함 | 분해해서 처리 |
| 검색 품질 보정 | 없음 | Query rewriting으로 보정 |
| 환각 억제 | 프롬프트 의존 | 자가 검증 단계 있음 |
| 지연(latency) | 낮음 (3~15초) | 높음 (10~60초) |
| 비용 | 낮음 (토큰 1~2x) | 높음 (토큰 5~15x) |
| 구현 복잡도 | 낮음 | 높음 |
| 결정론성 | 높음 (경로 고정) | 낮음 (LLM이 분기) |
| 디버깅 난이도 | 낮음 | 높음 (LLM 결정 추적) |
| 실패 패턴 | 검색 실패 | 무한 루프, 잘못된 분기 |

### 1.5 Agentic RAG의 세부 기법 (면접 키워드)

| 기법 | 설명 | 효과 |
|------|------|------|
| **Query Rewriting** | 원 질문을 검색 친화적 쿼리로 변환 | 짧은/모호한 질문의 검색 품질 개선 |
| **Query Decomposition** | "A와 B의 차이는?" → ["A는?", "B는?"] | Multi-hop 질문 대응 |
| **Iterative Retrieval** | 검색 결과 부족하면 쿼리 변형 후 재검색 | Recall 보강 |
| **Self-Reflection** | 답변 후 "근거가 문서에 있나?" 재검증 | 환각 이중 억제 |
| **Tool Use** | 벡터 검색 외 DB/API/계산기 등 호출 | RAG의 한계 극복 |
| **Multi-Agent** | Retriever/Writer/Critic 등 역할별 에이전트 | 전문화로 품질↑ |
| **Planning** | LLM이 전체 단계를 먼저 계획 | 복합 작업 처리 |

---

## 2. 축 ② — LLM 조달 방식

### 2.1 구독형 SDK (내 과제: Claude Code SDK, Codex CLI)

**동작 방식:**
```python
# 내 과제의 ClaudeProvider 내부
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async with ClaudeSDKClient(options=options) as client:
    await client.query(prompt)
    async for message in client.receive_response():
        ...
```

**특징:**
- 로컬에 설치된 **CLI 도구**(`claude`, `codex`)를 SDK로 프로그램이 호출
- 인증: 사용자 **구독 계정** (Claude Pro/Max, ChatGPT Pro) — 별도 API 키 없음
- 비용: **월정액** (사용량 무관)
- 모델 제어: 제한적 (`temperature`, `top_p`, `seed` 등 직접 제어 어려움)
- 스트리밍: 지원 (토큰 단위)

**장점:**
- API 키 관리 불필요
- 과제/개인 실험에서 비용 예측 가능

**단점:**
- **온프레미스 배포 불가** (계정 인증 + CLI 설치 필요)
- 서버리스/컨테이너 배포 시 CLI 번들링 필요
- 파라미터 제어 제한적
- 서비스 안정성이 구독 유지에 의존

### 2.2 API 직접 호출 (Anthropic API, OpenAI API)

**동작 방식:**
```python
import anthropic
client = anthropic.Anthropic(api_key="sk-ant-...")
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    temperature=0.2,
    messages=[...],
)
```

**특징:**
- HTTPS API 직접 호출
- 인증: **API 키** (프로젝트별 발급)
- 비용: **토큰당 종량제** (input/output 토큰 × 단가)
- 모델 제어: **완전 제어** (temperature, top_p, seed, stop sequences, JSON mode, tool use)
- 스트리밍, 배치, prompt caching 등 기능 풍부

**장점:**
- 프로덕션 표준
- 완전한 파라미터 제어
- 배포 제약 없음
- 사용량에 비례한 정확한 비용 관리

**단점:**
- 사용량 많으면 비용 급증
- API 키 유출 리스크 관리 필요
- 여전히 **외부 API** (온프레미스 규제 환경에서 제약)

### 2.3 오픈소스 LLM 로컬 호출 (Ollama, vLLM, llama.cpp)

**동작 방식:**
```python
# OpenAI 호환 API로 로컬 서버 호출
import openai
client = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
response = client.chat.completions.create(
    model="llama-3.1-70b",
    messages=[...],
)
```

**특징:**
- 로컬/내부 서버에서 모델 직접 실행
- 모델: Llama, Qwen, Mistral, Gemma 등 오픈소스
- 비용: **인프라 비용** (GPU 감가상각 + 전력)
- 모델 제어: 완전 + 모델 자체 fine-tuning 가능
- 데이터가 **절대 외부로 나가지 않음**

**장점:**
- **완전한 데이터 주권** (온프레미스, 에어갭 환경 가능)
- 사용량 무관 고정 비용
- 모델/프롬프트/가중치 모두 통제

**단점:**
- 오픈소스 모델 품질이 Claude/GPT 최고급 대비 낮음
- GPU 인프라 필요 (70B급은 A100 2장 이상)
- 운영 복잡도 높음 (모델 업데이트, 스케일링)

### 2.4 세 방식 비교표

| 항목 | 구독 SDK | API 직접 | 오픈소스 로컬 |
|------|---------|----------|--------------|
| 인증 | 구독 계정 | API 키 | 없음 |
| 비용 구조 | 월정액 | 종량제 | 인프라 고정비 |
| 모델 품질 | 최상급 | 최상급 | 중상급 |
| 파라미터 제어 | 제한적 | 완전 | 완전 |
| 외부 데이터 전송 | 있음 | 있음 | **없음** |
| 온프레미스 | ❌ | ❌ (또는 프록시) | ✅ |
| 실무 적합성 | 개인/PoC | 프로덕션 표준 | 규제 산업 |

---

## 3. 내 과제와 오피스에이전트의 정확한 차이

|  | 내 과제 | 오피스에이전트 (추정) |
|----|--------|-------------------|
| **축 ① (RAG)** | Naive RAG | Agentic RAG |
| **축 ② (LLM 조달)** | 구독형 SDK (Claude, Codex) | 오픈소스 LLM 로컬 호출 |

즉, 두 축에서 모두 다릅니다. 하지만 **각 축은 독립적으로 디벨롭 가능**합니다:

- **축 ① 개선**: `rag_service.py`에 Query Rewriting + Self-Reflection 추가 → Agentic RAG로 진화
- **축 ② 개선**: `LLMProvider` 어댑터에 `OllamaProvider` 추가 → 로컬 LLM 지원

**핵심 메시지:** 내 설계가 **두 축 모두에서 확장 가능하게 되어 있다**는 것이 강점.

---

## 4. 면접에서 이 질문이 나왔을 때 답변 스크립트

### Q. "귀사의 Agentic RAG와 본인 과제의 SDK 기반 RAG 차이가 뭐라고 생각하세요?"

**A. (90초)**

> "두 용어는 사실 **다른 축**입니다.
>
> 제 과제는 두 가지 축에서 볼 수 있는데요,
> **RAG 파이프라인 축**에서는 Naive RAG — 한 번 검색하고 한 번 LLM 호출해서 답변하는 구조입니다.
> **LLM 조달 축**에서는 구독형 SDK — Claude Code SDK와 Codex CLI를 썼습니다. 과제에서 별도 API 키 없이 구독으로 쓰라는 제약이 있었거든요.
>
> 오피스에이전트는 제가 공개 자료로 파악한 범위에서, **RAG 축은 Agentic RAG** — 질문 의도 분석, 멀티스텝 검색, 자가 검증 같은 단계가 추가됐을 것으로 이해했습니다.
> **LLM 축은 오픈소스 LLM을 직접 호출** — 온프레미스 배포하려면 이게 필수니까요.
>
> 중요한 건 이 두 축이 **직교한다**는 점입니다. 제 과제의 `LLMProvider` 추상화 덕분에 축 ②(로컬 LLM 어댑터 추가)는 코드 변경 없이 가능하고, 축 ①(Agentic RAG 확장)은 `rag_service.py`에 Query Rewriting과 Self-Reflection 같은 단계를 끼워 넣으면 되는 문제입니다.
>
> 두 축을 각각 분리해서 볼 수 있다는 게 제가 이번 과제에서 배운 중요한 설계 원칙이었습니다."

### Q. "그럼 본인 과제에 Agentic RAG 추가하는 게 얼마나 걸릴까요?"

**A. (60초)**

> "가장 가치 있는 두 가지를 먼저 꼽으면:
> - **Self-Reflection** — 답변 후 '근거가 문서에 있는가?' LLM 재검증. 이건 제가 이미 만든 **이중 방어(프롬프트 + 서버 패턴 매칭)** 의 3차 방어로 자연스럽게 확장됩니다. 반나절.
> - **Query Rewriting** — 짧은 질문을 검색 친화적으로 재작성. `rag_service.py`의 검색 전에 LLM 호출 한 번 더. 반나절.
>
> 다만 추가할 때마다 **측정**해야 합니다. 지연이 2배 되고 비용도 2배 되는데, 그게 정확도 개선으로 상쇄되는지. 제 평가 하네스로 v2→v3 개선 측정했던 방식 그대로, **Agentic 단계별로 효과를 수치로 검증**하는 게 올바른 접근이라고 생각합니다."

---

## 5. 헷갈리지 말아야 할 용어들

| 용어 | 정확한 뜻 | 자주 하는 오해 |
|------|---------|--------------|
| **Agentic RAG** | RAG 파이프라인에 LLM의 의사결정/루프를 넣은 것 | "에이전트를 여러 개 만드는 것" (그건 Multi-Agent) |
| **AI Agent** | 도구 사용 + 목표 지향적 행동을 하는 LLM 시스템 | Agentic RAG와 같음 (Agent는 더 넓은 개념) |
| **Claude Code SDK** | CLI 기반 구독형 Claude 클라이언트 | Anthropic API와 동일 (다름) |
| **Agentic RAG ↔ Naive RAG** | 같은 축 (RAG 복잡도) | 다른 축 비교로 쓰면 혼란 |
| **SDK ↔ API** | 조달 방식 (축 ②) | 아키텍처와 혼동 |

---

## 6. 한 줄 요약

> **"Agentic RAG"는 RAG 파이프라인 복잡도 축이고, "구독형 SDK"는 LLM 조달 방식 축이다. 둘은 서로 독립적이며, 내 과제는 두 축 모두에서 확장 가능한 구조로 설계되어 있다.**
