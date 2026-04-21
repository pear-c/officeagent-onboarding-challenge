# 로컬 LLM 스택 이해 — Ollama, vLLM, 그리고 모델들

> 면접에서 "오픈소스 LLM / 온프레미스" 맥락이 나왔을 때 개념적으로 정확히 답하기 위한 레퍼런스.
> 핵심 메시지: **LLM(모델)과 실행 도구(런타임)를 구분해서 말할 수 있어야 한다.**

---

## 1. Ollama는 LLM이 아니다

### 한 줄 정의
**Ollama는 LLM이 아니라, LLM을 로컬에서 실행·서빙하는 도구(런타임)다.**
→ 비유하면 **"LLM 전용 Docker"**.

### 왜 헷갈리는가
"Ollama 쓴다"는 말은 "Docker 쓴다"와 같음. 어떤 LLM을 쓰는지는 별개로 말해야 한다.
- ❌ "Ollama로 답변했어요" → 틀림
- ✅ "Ollama 위에서 **Qwen2.5-7B**를 돌려서 답변했어요" → 정확

---

## 2. 로컬 LLM 실행 스택 (전체 그림)

```
┌────────────────────────────────────────────────┐
│  애플리케이션 (내 과제의 app/ 코드)              │
│     ↓ HTTP 호출 (OpenAI 호환 API)               │
├────────────────────────────────────────────────┤
│  런타임/서버 계층 ← ★ Ollama, vLLM, llama.cpp   │
│  - 모델 로드/언로드                             │
│  - API 서버 운영                                │
│  - 요청 큐잉, 배치                              │
│     ↓ 모델 가중치 로드                          │
├────────────────────────────────────────────────┤
│  모델 가중치 파일 ← ★ Qwen, Llama, Gemma 등     │
│  - .gguf (Ollama용 양자화 포맷)                 │
│  - .safetensors (vLLM용 원본 포맷)              │
│     ↓ 실행                                      │
├────────────────────────────────────────────────┤
│  하드웨어 (GPU / CPU / Apple Silicon)           │
└────────────────────────────────────────────────┘
```

각 계층은 **독립적으로 교체 가능**:
- 모델만 바꾸기: `ollama run qwen` → `ollama run llama3`
- 런타임 바꾸기: Ollama(개발) → vLLM(운영)
- 하드웨어 바꾸기: CPU → GPU → TPU

---

## 3. Ollama가 실제로 하는 일 4가지

| 역할 | 구체 동작 | Docker 비유 |
|------|---------|------------|
| **모델 카탈로그** | `ollama pull qwen2.5:7b` 모델 다운로드 | `docker pull` |
| **실행 런타임** | GPU/CPU에 모델 로드 + 추론 실행 | `docker run` |
| **API 서버** | `http://localhost:11434` OpenAI 호환 API 노출 | 포트 매핑 |
| **라이프사이클** | 여러 모델 동시 관리, 메모리 스왑 | `docker ps / stop` |

---

## 4. LLM vs 도구 — 헷갈리지 말기

| 이름 | 정체 | 비유 |
|------|------|------|
| **Llama, Qwen, Gemma, DeepSeek** | LLM 본체 (weights) | 영화 파일 (.mp4) |
| **Ollama, vLLM, llama.cpp** | 실행 도구 (런타임) | 미디어 플레이어 (VLC, MPV) |
| **Hugging Face** | 모델 저장소 | 영화 다운로드 사이트 |
| **Anthropic API, OpenAI API** | 호스팅형 실행 환경 | 넷플릭스 (모델 파일 없어도 사용 가능) |
| **LangChain, LlamaIndex** | RAG/에이전트 프레임워크 | 감독·편집 소프트웨어 |

---

## 5. 로컬 런타임 3강 비교

| 항목 | **Ollama** | **vLLM** | **llama.cpp** |
|------|----------|---------|--------------|
| 진입장벽 | 매우 낮음 (1줄 설치) | 중간 (Python 환경) | 중간 (빌드 필요) |
| 성능(처리량) | 낮음 | **최고** | 낮음 |
| GPU 활용 | OK | **최적** (PagedAttention, continuous batching) | 제한적 |
| CPU 지원 | O | 제한적 | **최고** (CPU-only 가능) |
| 양자화 | 자동 (Q4 기본) | 지원 (AWQ, GPTQ) | 매우 풍부 |
| 멀티 유저 | 1~수 명 | **수백~수천 명** | 단일 유저 |
| 메모리 효율 | 보통 | **최고** | 좋음 |
| OpenAI 호환 API | ✅ | ✅ | ✅ |
| 주 용도 | **개발 / PoC / 개인** | **프로덕션 서빙** | **에지 / 로우엔드 / 임베디드** |

### 2026년 업계 관행
- **개발할 때는 Ollama** — 세팅 빠르고 모델 교체 쉬움
- **배포할 때는 vLLM** — 처리량이 Ollama 대비 3~10배
- **CPU만 있거나 라즈베리파이 같은 환경은 llama.cpp**

> Ollama 내부는 사실 **llama.cpp를 래핑**한 것. llama.cpp가 엔진, Ollama가 UX/CLI/관리 레이어.

---

## 6. 실사용 예시

### Ollama (가장 쉬움)

```bash
# 설치
brew install ollama          # macOS
# 또는
curl -fsSL https://ollama.com/install.sh | sh   # Linux

# 모델 다운로드 + 실행 (대화형)
ollama run qwen2.5:7b

# 서버로 띄우기 (백그라운드)
ollama serve &

# OpenAI 호환 API로 호출
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [{"role":"user","content":"안녕"}]
  }'
```

### vLLM (프로덕션)

```bash
pip install vllm

# OpenAI 호환 서버 기동
vllm serve Qwen/Qwen2.5-7B-Instruct \
  --host 0.0.0.0 --port 8000 \
  --max-model-len 8192

# 호출 방식은 Ollama와 동일 (OpenAI 호환)
```

### 내 과제에 통합하는 경우 (가상 코드)

```python
# app/llm/local_provider.py (신규)
from openai import AsyncOpenAI

class OllamaProvider(LLMProvider):
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"  # 더미 — Ollama는 인증 없음
        )
        self.model = "qwen2.5:7b"

    async def generate(self, prompt: str) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role":"user","content":prompt}],
        )
        return resp.choices[0].message.content
```

변경 지점: [app/llm/](../app/llm/)에 파일 1개 추가. 다른 계층(`rag_service`, `ingest_service`)은 **전혀 건드리지 않음** — 어댑터 패턴의 효과.

---

## 7. 내 과제 관점에서 정리

### 현재 구조 (구독형 SDK)
```
app/services/rag_service.py
  → LLMProvider (ABC)
      → ClaudeProvider (claude-agent-sdk, 구독 인증, CLI 내부 호출)
      → CodexProvider (@openai/codex, 구독 인증, CLI 내부 호출)
```

### 온프레미스 전환 시 (로컬 LLM)
```
app/services/rag_service.py
  → LLMProvider (ABC)
      → OllamaProvider (HTTP → http://localhost:11434)
      → VLLMProvider   (HTTP → http://vllm-server:8000)
      → (기존 Claude/Codex는 SaaS 모드에서 병존)
```

→ **어댑터 추가만으로 확장 완료.** 호출자(`rag_service`) 코드는 불변.

### 면접 포인트
1. **"제 설계는 이미 이 전환에 대비되어 있다"** — `LLMProvider` ABC + 어댑터 패턴
2. **"추가 비용은 어댑터 코드가 아니라 프롬프트 재튜닝이다"** — 작은 모델은 지시 준수가 약함
3. **"평가 하네스가 있어서 전환 품질을 하루 단위로 측정 가능"** — 이게 진짜 자산

---

## 8. 면접에서 나올 수 있는 꼬리 질문과 답변

### Q1. "Ollama와 vLLM 중 어느 쪽을 프로덕션에 쓰실 건가요?"
**A.** vLLM입니다. Ollama는 개발 단계에선 세팅이 빨라서 좋지만, continuous batching이 없어서 동시 요청 처리량이 낮습니다. 월 9천원/인 가격을 유지하려면 서버 한 대당 처리 가능 인원수가 중요한데, vLLM이 Ollama 대비 3~10배 처리량이라 단위 경제가 달라집니다. 다만 Ollama가 내부적으로 **llama.cpp를 기반**으로 하는 반면 vLLM은 별도 구현체라 모델 호환성 이슈가 있을 수 있어서, **개발-Ollama / 운영-vLLM**의 이중 구성에서 모델 교체 시마다 양쪽에서 평가 하네스를 돌리는 게 안전합니다.

### Q2. "양자화(Quantization)가 뭔가요?"
**A.** 모델 가중치를 FP16/BF16 대신 INT8, INT4 같은 저정밀도로 변환해서 메모리 사용량을 줄이는 기법입니다. 예를 들어 Qwen2.5-7B 원본은 약 14GB VRAM인데, Q4 양자화하면 5GB 내외로 줄어서 일반 GPU(RTX 3090/4090)에서도 돌릴 수 있습니다. 품질은 3~5% 내외 감소가 일반적이라 실용적으로 감수 가능합니다. Ollama는 기본적으로 Q4_K_M 양자화 버전을 내려받습니다.

### Q3. "그럼 Ollama는 빠른 거예요, 느린 거예요?"
**A.** **한 명이 쓸 땐 Ollama도 충분히 빠르고, 여러 명이 동시에 쓸 땐 vLLM이 훨씬 빠릅니다.** 핵심은 *continuous batching* 유무입니다 — vLLM은 요청 여러 개를 한 GPU 배치에 자동으로 묶어서 처리하는데, Ollama는 순차 처리에 가깝습니다. 개인 개발자가 쓸 땐 차이 없지만, 사내 100명이 동시에 쓰는 시나리오에선 vLLM이 필수입니다.

### Q4. "Ollama 없이 직접 llama.cpp 쓰는 경우는 언제인가요?"
**A.** GPU 없이 CPU만으로 돌려야 할 때, 또는 Raspberry Pi 같은 임베디드 환경, 양자화 포맷을 직접 세밀하게 제어해야 할 때입니다. Ollama는 기본 Q4만 쓰지만 llama.cpp는 Q2, Q3, Q5, Q6, Q8 등 세분화된 선택지가 있습니다. 다만 CLI UX가 Ollama보다 불편해서 일반 개발자 선택지는 아닙니다.

### Q5. "Ollama/vLLM 둘 다 OpenAI 호환 API라고 했는데, 왜 호환성이 중요한가요?"
**A.** OpenAI SDK 코드가 사실상 업계 표준이 됐기 때문입니다. 기존 코드의 `base_url`과 `api_key`만 바꾸면 Ollama/vLLM/Together AI/Groq 같은 모든 서비스로 교체 가능합니다. 제 `LLMProvider` 추상화도 이 호환성을 전제로 설계하면 구현 코드 3~5줄 수준으로 새 어댑터를 추가할 수 있습니다.

---

## 9. 한 장 요약 — 면접 직전 복기용

```
Ollama = LLM ❌
Ollama = LLM을 로컬에서 실행·서빙하는 도구 ✅

스택:
  [내 앱] → HTTP → [Ollama/vLLM 런타임] → [Qwen/Llama 모델] → [GPU]

로컬 런타임 3강:
  - Ollama   : 개발/PoC용. 세팅 1줄.
  - vLLM     : 프로덕션용. 처리량 3~10배.
  - llama.cpp: CPU/저자원. Ollama의 내부 엔진이기도 함.

2026년 관행: 개발=Ollama, 운영=vLLM.

내 과제와의 연결:
  - LLMProvider 어댑터 패턴으로 Ollama/vLLM 추가 가능
  - 코드 변경 없음. 프롬프트 재튜닝이 진짜 비용
  - 평가 하네스가 전환 품질을 하루 단위로 검증
```
