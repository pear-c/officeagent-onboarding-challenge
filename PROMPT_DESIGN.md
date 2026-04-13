# PROMPT_DESIGN.md — 프롬프트 설계 문서

## 1. 개요

이 문서는 Document Q&A API의 프롬프트 설계 과정, LLM 모델 비교 측정 결과, 그리고 최종 역할 분할 결정을 기록한다.

**핵심 원칙**: 모델 선택을 인상론이 아닌 **데이터로 결정**한다.

---

## 2. 프롬프트 구조

### 2.1 JSON 응답용 (`SYSTEM_PROMPT`)

`POST /api/v1/query` 엔드포인트에서 사용. LLM이 구조화된 JSON으로 응답한다.

```
[시스템 프롬프트]
당신은 사내 문서를 기반으로 직원의 질문에 답변하는 도우미입니다.
1. 오직 <문서>에 포함된 내용만 사용
2. 문서에 없는 내용 추측/보충 금지
3. 답이 없으면 "제공된 문서에서 해당 내용을 찾을 수 없습니다." 응답
4. JSON 형식 출력: {"answer", "sources", "answerable"}
5. answerable=false → sources는 빈 배열

[사용자 프롬프트]
<문서>
[1] (file: company-policy.txt, chunk_id: 0)
임직원은 연간 최대 200만원까지...
[2] (file: company-policy.txt, chunk_id: 1)
...
</문서>

<질문>
교육비 지원 한도는 얼마인가요?
</질문>
```

**설계 의도**:
- `<문서>` / `<질문>` XML 태그로 역할 구분 명확화
- 출처 번호 `[1]`, `[2]`로 LLM이 인용할 수 있도록 유도
- JSON 스키마를 프롬프트 + `output_format` 이중으로 강제 (파싱 실패 방지)

### 2.2 스트리밍 응답용 (`SYSTEM_PROMPT_STREAM`)

`POST /api/v1/query/stream` SSE 엔드포인트에서 사용. 자연어 텍스트만 출력.

```
[시스템 프롬프트]
당신은 사내 문서를 기반으로 직원의 질문에 답변하는 도우미입니다.
1. 오직 <문서>에 포함된 내용만 사용
2. 문서에 없는 내용 추측/보충 금지
3. 답이 없으면 "제공된 문서에서 해당 내용을 찾을 수 없습니다." 응답
4. JSON이 아닌 자연어 한국어 텍스트로만 답변
5. 출처는 별도로 표시하지 마세요 (시스템이 자동 처리)
```

**프롬프트 분리 이유 (TS-004)**:
- 동일 프롬프트 사용 시 스트리밍에서 원시 JSON이 UI에 노출되는 버그 발생
- 스트리밍은 토큰 단위 전송이므로 JSON 구조가 깨져서 파싱 불가
- sources는 벡터 검색에서 이미 확보 → LLM이 중복 출력할 필요 없음

---

## 3. LLM 모델 비교 측정

### 3.1 실험 설계

| 항목 | 내용 |
|------|------|
| 평가 도구 | `eval/run.py` — RAGService 직접 호출 (HTTP API 아닌) |
| 캐시 우회 | `NoOpCacheService` — 항상 캐시 miss (순수 LLM 성능 측정) |
| 데이터셋 | `eval/golden_dataset.json` — 50케이스 |
| 문서 | 5개 (company-policy.txt, development-guide.md, hr-policy-detailed.md, tech-architecture.md, meeting-minutes.md) |
| 임베딩 | BAAI/bge-m3 (동일 조건) |
| 검색 | Chroma top_k=5 (동일 조건) |

### 3.2 데이터셋 구성

| 난이도 | 개수 | 설명 |
|--------|------|------|
| easy | 16 | 단일 청크에서 직접 추출 |
| medium | 11 | 여러 후보 중 정확한 정보 선택 |
| computation | 4 | 수치 계산 필요 (승진 연수, 연차 일수) |
| multi-hop | 2 | 여러 섹션/문서 조합 |
| edge/함정 | 6 | 미결 사항, 기각된 안건, 조건부 답변 |
| long-answer | 1 | 여러 정책 종합 요약 |
| unanswerable | 6 | 문서에 없는 질문 (거절해야 함) |
| **합계** | **50** | |

### 3.3 측정 결과

| 메트릭 | Claude Sonnet 4.6 | Codex (GPT) | 승자 |
|--------|-------------------|-------------|------|
| **Retrieval Hit Rate** | **93.18%** | 90.91% | Claude (+2.27%p) |
| **Citation Accuracy** | **93.18%** | 90.91% | Claude (+2.27%p) |
| **Refusal Accuracy** | 83.33% | **100.00%** | **Codex (+16.67%p)** |
| **Keyword Hit Rate** | 90.91% | 90.91% | 동률 |
| **JSON Parse Rate** | 100.00% | 100.00% | 동률 |
| **Latency p50** | 10,773ms | **4,516ms** | **Codex (2.4x)** |
| **Latency p95** | 16,892ms | **10,557ms** | **Codex (1.6x)** |

### 3.4 상세 분석

#### Retrieval/Citation (Claude 소폭 우위)

Claude가 3개 케이스에서 Codex보다 정확한 출처를 인용했다. 이 차이는 검색 결과(top-K)는 동일하지만, LLM이 관련 청크를 선택하는 판단에서 발생한다.

#### Refusal Accuracy — 핵심 발견 (Codex 압도적 우위)

Claude의 Refusal 83.33%는 이 실험의 **가장 중요한 발견**이다.

**원인 분석 — 왜 Claude가 거절을 못하는가:**

1. **모델 훈련 철학의 차이**: Claude는 "도움이 되려는(helpful)" 성향이 RLHF로 강하게 학습되어 있다. 사용자가 질문하면 어떻게든 유용한 답변을 제공하려고 한다. 일반 챗봇에서는 장점이지만, RAG에서 "문서에 없으면 모른다고 해라"는 지시와 충돌한다. 반면 Codex는 코드 도구 출신으로 "지시를 정확히 따르라"는 방향으로 훈련되어 "~하지 마라"는 금지 지시에 더 엄격하다.

2. **과잉 추론 (Over-inference)**: Claude의 강한 추론 능력이 역으로 작용한다. 문서에 비슷한 내용이 있으면 "여기서 유추하면..."으로 확장하는 경향이 있다. 예를 들어 "스톡옵션 정책은?" 질문에 급여/복리후생 문서가 context로 주어지면, Claude는 "스톡옵션은 언급되지 않지만, 급여 구성은..."처럼 관련 내용으로 답변을 시도한다. Codex는 "해당 정보를 찾을 수 없습니다"로 깔끔하게 거절한다.

3. **RAG 특유의 함정**: RAG 시스템에서는 **유추하지 않는 것**이 정답이다. LLM이 문서에 없는 내용을 만들어내는 환각(Hallucination)은 "답변을 못함"보다 훨씬 위험하다.

**시사점**: "모델이 똑똑할수록 RAG에 적합한 것은 아니다." Claude의 범용 추론 능력이 RAG의 constrained 환경에서는 약점이 될 수 있다.

#### 속도 (Codex 압도적 우위)

- p50 기준 Codex가 2.4배 빠름
- 사용자 체감 대기시간에 직접적 영향
- 스트리밍 SSE를 사용하더라도 첫 토큰 도달 시간(TTFT)에서 Codex가 유리

#### Keyword Hit Rate (동률)

두 모델 모두 90.91%로 동일. 수치 계산(Q27 "사원→부장 16년"), 멀티홉(Q40, Q41) 같은 어려운 케이스에서도 차이 없음. 답변 내용의 실질적 품질은 동등하다.

---

## 4. 역할 분할 최종 결정

### 4.1 결정

| 역할 | 모델 | 근거 |
|------|------|------|
| **기본 답변 생성** | **Codex** | 속도 2.4x, 거절 정확도 100%, 키워드 정확도 동률 |
| **고정확도 fallback** | Claude | Retrieval/Citation +2.27%p 우위 |

### 4.2 근거

1. **RAG에서 Refusal이 가장 중요**: 문서에 없는 내용을 만들어내는 건 "답변 못함"보다 위험
2. **속도가 UX를 좌우**: p50 4.5초 vs 10.8초 — 사용자가 체감하는 차이
3. **검색 정확도 차이 미미**: 2.27%p 차이는 50케이스에서 1~2건 수준
4. **키워드 정확도 동률**: 답변 내용의 실질적 품질 차이 없음

### 4.3 초기 가설 vs 최종 결과

| | 초기 가설 (D01) | 측정 결과 |
|--|----------------|----------|
| 답변 생성 | Claude (정확도 우선) | **Codex** (거절+속도 우위) |
| 보조 작업 | Codex (속도 우선) | Claude (fallback) |

**가설이 뒤집힌 이유**: Claude의 "도움이 되려는" 성향이 RAG 거절 시나리오에서 약점으로 작용. Codex의 지시 추종(instruction following)이 이 사용 사례에서 더 강력.

---

## 5. 프롬프트 튜닝 히스토리

| 버전 | 변경 | 결과 |
|------|------|------|
| v1 | 초기 SYSTEM_PROMPT (JSON 출력 지시) | JSON/스트리밍 공용 → TS-004 발생 |
| v2 | SYSTEM_PROMPT + SYSTEM_PROMPT_STREAM 분리 | 스트리밍에서 자연어 출력 정상화 |
| v3 (향후) | Claude용 거절 강화 프롬프트 | Refusal Accuracy 개선 가능성 |

### 5.1 향후 개선 방향

**Claude Refusal 개선 시도** (미적용):
```
3. 문서에 답이 없으면 절대로 추측하지 말고, 반드시 다음과 같이만 답하세요:
   "제공된 문서에서 해당 내용을 찾을 수 없습니다."
   일반 지식이나 상식으로 보충하는 것은 금지입니다.
```

이 변경이 Claude의 Refusal을 개선하는지는 추가 측정이 필요하다. 현 시점에서는 Codex 기본 사용이 더 안전한 선택.

---

## 6. 평가 하네스 구조

```
eval/
├── golden_dataset.json    # 50케이스 (7난이도)
├── run.py                 # NoOpCacheService + RAGService 직접 호출
├── metrics.py             # 7개 메트릭
└── results/               # 날짜_provider.json
```

### 실행 방법

```bash
# 측정
python eval/run.py run --provider claude
python eval/run.py run --provider codex

# 비교
python eval/run.py compare eval/results/<claude>.json eval/results/<codex>.json
```

### 메트릭 정의

| 메트릭 | 정의 | 대상 |
|--------|------|------|
| Retrieval Hit Rate | top-K에 정답 파일 포함 | answerable만 |
| Citation Accuracy | LLM 인용 출처에 정답 파일 포함 | answerable만 |
| Refusal Accuracy | 문서에 없는 질문 거절 비율 | unanswerable만 |
| Keyword Hit Rate | 답변에 기대 키워드 전부 포함 | answerable만 |
| JSON Parse Rate | 응답 JSON 정상 파싱 | 전체 |
| Latency p50 | 응답 시간 중앙값 | 전체 |
| Latency p95 | 응답 시간 95퍼센타일 | 전체 |
