# Decision 05. 캐시 DB — Redis

> **결정**: Redis 7 (Docker)
> **설계 원칙**: "속도에는 캐시를" — LLM 호출(3~15초)을 캐시 hit(~5ms)으로 대체

## PRD 요구사항 매핑

| PRD 요구사항 | Redis 구현 방식 |
|---|---|
| 동일 질문 캐시 | SHA-256(질문) → Redis key, 답변 JSON → value |
| 유사 질문 캐시 | 질문 임베딩 → Chroma `cache_questions` collection, cosine ≥ 0.95 hit |
| 캐시 히트 여부 응답 포함 | 응답 JSON에 `cached: true/false` 필드 |
| 문서 변경 시 무효화 | 문서 SHA-256 해시 비교 → 변경 시 관련 캐시 키 삭제 |

## 3단계 캐시 설계

| 단계 | 방식 | 키 패턴 | TTL |
|---|---|---|---|
| 1. 정확 일치 | SHA-256(질문) → Redis | `cache:exact:{hash}` | 1시간 |
| 2. 유사 질문 | embed(질문) → Chroma cache collection | 벡터 유사도 ≥ 0.95 | 1시간 |
| 3. 무효화 | SHA-256(문서) → Redis | `doc:hash:{filename}` | 없음 |

## 무효화 전략 (content-hash-cache-pattern 스킬 적용)

```
문서 재업로드 →
  SHA-256(새 파일) vs Redis에 저장된 이전 해시 →
    동일 → "이미 최신" 반환
    변경됨 → 관련 캐시 키 삭제 + Chroma 벡터 삭제 + 재 Ingestion
```

## 선택 근거

1. **캐시 업계 표준** — 채점자도 익숙, 레퍼런스 풍부
2. **TTL 네이티브 지원** — 시간 기반 캐시 만료 자동화
3. **Python 클라이언트 성숙** — `redis-py` 비동기 지원
4. **content-hash-cache-pattern** 스킬과 자연스럽게 결합

## 왜 유사 질문 캐시에 Chroma를 쓰는가

Redis 자체도 `RediSearch` 모듈로 벡터 검색이 가능하지만:
- RediSearch는 별도 모듈 설치 필요 (Docker 이미지 변경)
- 이미 Chroma가 있으니 별도 collection으로 분리하는 게 단순
- 캐시 질문 수는 적으므로(수백~수천) Chroma로 충분
