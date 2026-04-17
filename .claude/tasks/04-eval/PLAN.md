# 04-eval — 평가 하네스 구현

## 목표

골든 데이터셋 20케이스 + 7메트릭으로 Claude vs Codex를 비교 측정하고,
LLM 역할 분할을 **데이터로 확정**한다. 결과를 PROMPT_DESIGN.md에 기재.

## 핵심 설계 결정

- **RAGService 직접 호출** (HTTP API 아닌) — provider swap 코드 1줄, 서버 재시작 불필요
- **NoOpCacheService** — FLUSHDB 대신 캐시 없는 RAGService로 순수 LLM 성능 측정
- **keyword_hit_rate 추가** — citation_accuracy(파일 일치)와 별도로 답변 내용 정확도 측정

## 구현 순서

| 순서 | 파일 | 내용 | 예상 줄수 |
|------|------|------|----------|
| 1 | `eval/metrics.py` | 7개 메트릭 함수 | ~100 |
| 2 | `eval/run.py` | CLI + NoOpCacheService + 실행 + 비교 | ~220 |
| 3 | 측정 실행 | Claude → Codex → 결과 비교 | - |
| 4 | `PROMPT_DESIGN.md` | 프롬프트 설계 + 측정 결과 표 | ~150 |

## 실행 흐름

```
eval/run.py --provider claude
  ① Embedder + ChromaStore + NoOpCacheService 초기화
  ② ClaudeProvider 인스턴스 생성
  ③ RAGService(cache=NoOp, llm=Claude) 구성
  ④ golden_dataset.json 20케이스 순차 실행
  ⑤ metrics.py로 7개 메트릭 계산
  ⑥ results/에 JSON 저장 + 터미널 요약 출력

eval/run.py --compare result1.json result2.json
  → 두 결과를 나란히 비교 표 출력
```

## 산출물

| 산출물 | 위치 |
|--------|------|
| `eval/metrics.py` | `eval/metrics.py` |
| `eval/run.py` | `eval/run.py` |
| 측정 결과 | `eval/results/` |
| **PROMPT_DESIGN.md** (필수) | 리포 루트 |
