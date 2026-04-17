# Decision 07. 평가 하네스 설계

> **결정**: 골든 데이터셋 20케이스 + 6메트릭 + `eval/` 디렉토리
> **핵심 근거**: 기술 선택과 프롬프트 튜닝을 인상론이 아닌 데이터로 결정

## 목적

1. **임베딩 모델 선택 검증** — bge-m3가 실제 우리 데이터에서도 최고인지
2. **LLM 모델 역할 분할 확정** — Claude vs Codex 어느 쪽이 답변/보조에 적합한지
3. **청킹 전략 비교** — 고정 크기 vs 재귀 vs 하이브리드 Hit Rate 비교
4. **프롬프트 튜닝** — 프롬프트 변경 전후 회귀 테스트
5. **ARCHITECTURE.md / PROMPT_DESIGN.md 수치 근거** — 면접에서 "왜?" 답변

## 구조

```
eval/
├── golden_dataset.json    # 골든 케이스 20개
├── run.py                 # 실행 스크립트
├── metrics.py             # 메트릭 계산
└── results/               # 실행 결과 (날짜별 JSON)
```

## 골든 데이터셋 (20케이스)

sample-docs 2개 파일에서 추출:

| 유형 | 개수 | 예시 |
|---|---|---|
| answerable | 12 | "교육비 지원 한도는?" → company-policy.txt |
| unanswerable | 5 | "화성 지사 주소는?" → 문서에 없음, "모름" 답해야 함 |
| edge case | 3 | "재택근무 가능?" → 조건부 답변 (팀장 승인, 고객 미팅 제외) |

### 케이스 형식

```json
{
  "id": "Q01",
  "question": "교육비 지원 한도는 얼마인가요?",
  "expected_source": "company-policy.txt",
  "expected_section": "교육비 지원",
  "expected_keywords": ["200만원", "연간"],
  "answerable": true,
  "difficulty": "easy"
}
```

## 메트릭 (eval-harness 스킬 참조)

| 메트릭 | 측정 방법 | 목표 | eval 타입 |
|---|---|---|---|
| **Retrieval Hit Rate** | 검색된 top-K에 `expected_source` 포함? | ≥ 0.85 | Capability |
| **Citation Accuracy** | 답변이 인용한 출처가 `expected_source`와 일치? | ≥ 0.80 | Capability |
| **Refusal Accuracy** | `answerable=false`에서 "모름" 응답? | ≥ 0.90 | Capability |
| **JSON Parse Rate** | 구조화 출력이 깨지지 않는 비율 | ≥ 0.95 | Regression |
| **Latency p50** | 응답 시간 중앙값 | < 10초 | Regression |
| **Latency p95** | 응답 시간 95퍼센타일 | < 20초 | Regression |

### 측정 방법

- **pass@1**: 1회 실행 결과 (기본)
- 시간 되면 **pass@3**: 3회 실행 중 최소 1회 성공 (신뢰도↑)

## 실행 방법

```bash
# Claude로 측정
python eval/run.py --provider claude

# Codex로 측정
python eval/run.py --provider codex

# 청킹 전략 비교
python eval/run.py --provider claude --chunking fixed
python eval/run.py --provider claude --chunking recursive
python eval/run.py --provider claude --chunking hybrid

# 결과 비교
python eval/run.py --compare eval/results/2026-04-12_claude.json eval/results/2026-04-12_codex.json
```

## 결과 활용

| 결과 | 반영 위치 |
|---|---|
| Claude vs Codex 비교 표 | ARCHITECTURE.md 3.6절 + PROMPT_DESIGN.md |
| 청킹 전략 비교 표 | ARCHITECTURE.md 3.5절 |
| 캐시 hit/miss 응답 시간 | ARCHITECTURE.md 9.3절 |
| 프롬프트 변경 전후 비교 | PROMPT_DESIGN.md |
