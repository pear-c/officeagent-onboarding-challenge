# 04-eval — CHECKLIST

## 0. 사전 준비

- [x] [AI] PLAN.md / CONTEXT.md / CHECKLIST.md 작성
- [ ] [AI] feature/04-eval 브랜치 생성

## 1. eval/metrics.py 구현

- [ ] [AI] `retrieval_hit_rate()` — top-K에 expected_source 포함 여부
- [ ] [AI] `citation_accuracy()` — LLM 인용 출처 일치
- [ ] [AI] `refusal_accuracy()` — unanswerable 거절 정확도
- [ ] [AI] `keyword_hit_rate()` — 답변에 expected_keywords 포함
- [ ] [AI] `json_parse_rate()` — JSON 정상 파싱 비율
- [ ] [AI] `latency_percentile()` — p50/p95

## 2. eval/run.py 구현

- [ ] [AI] NoOpCacheService 클래스
- [ ] [AI] 초기화 헬퍼 (Embedder + ChromaStore)
- [ ] [AI] `run_eval(provider)` — 20케이스 순차 실행
- [ ] [AI] 결과 JSON 저장
- [ ] [AI] `compare(result1, result2)` — 비교 표 출력
- [ ] [AI] CLI (argparse)

## 3. 측정 실행

- [ ] [USER] Claude 측정 (`python eval/run.py --provider claude`)
- [ ] [USER] Codex 측정 (`python eval/run.py --provider codex`)

## 4. 산출물

- [ ] [AI] PROMPT_DESIGN.md 작성 (측정 결과 기반)
- [ ] [AI] ARCHITECTURE.md 수치 업데이트

## 5. 검증 + 리뷰

- [ ] [AI] Python 문법 검사
- [ ] [AI] 코드 리뷰

## 6. 커밋 + push

- [ ] [AI] feature/04-eval 커밋 + push
- [ ] [AI] develop 머지
