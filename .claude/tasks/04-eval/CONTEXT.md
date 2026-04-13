# 04-eval — CONTEXT

## 결정 이력

### D31. RAGService 직접 호출 방식 채택 (2026-04-13)

- **결정**: HTTP API 대신 RAGService를 직접 인스턴스화하여 평가
- **이유**: 검증 에이전트 피드백 — provider swap 코드 1줄, 서버 재시작 불필요, 한 번에 비교 가능
- **trade-off**: HTTP 레이어 검증 불가 → 서비스 레이어만 검증 (평가 목적에 충분)

### D32. NoOpCacheService로 캐시 우회 (2026-04-13)

- **결정**: FLUSHDB 대신 NoOpCacheService(항상 miss) 주입
- **이유**: 검증 에이전트 피드백 — FLUSHDB는 `doc:hash:*`까지 삭제하여 문서 재업로드 필요
- **구현**: `get_exact()` → None, `get_similar()` → None, `save()` → pass

### D33. keyword_hit_rate 메트릭 추가 (2026-04-13)

- **결정**: Decision 07의 6메트릭에 keyword_hit_rate 추가 (총 7개)
- **이유**: citation_accuracy는 파일 일치만, keyword_hit_rate는 답변 내용 정확도 측정
- **근거**: golden_dataset.json에 expected_keywords 이미 정의됨

## 참고 파일

| 파일 | 용도 |
|------|------|
| `eval/golden_dataset.json` | 골든 데이터셋 20케이스 (01-architecture에서 작성) |
| `.claude/knowledge/decisions/07-eval-harness.md` | 평가 하네스 설계 원본 |
| `app/services/rag_service.py` | RAGService — 직접 호출 대상 |
| `app/prompts/templates.py` | SYSTEM_PROMPT — 프롬프트 튜닝 대상 |
