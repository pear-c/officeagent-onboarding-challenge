# Decision 03. 임베딩 모델 — BAAI/bge-m3

> **결정**: BAAI/bge-m3 (1024차원, 2.3GB, 최대 8192 토큰)
> **설계 원칙**: "정확도에는 최고를" — 검색 품질이 전체 RAG 정확도의 30%를 결정

## 후보 비교

| 항목 | BAAI/bge-m3 ⭐ | intfloat/multilingual-e5-base | jhgan/ko-sroberta-multitask |
|---|---|---|---|
| MTEB Retrieval (ko) | 최상위권 | 중상위 | 중위 |
| 차원 | 1024 | 768 | 768 |
| 모델 크기 | 2.3GB | 1.1GB | 442MB |
| 최대 입력 토큰 | **8192** | 512 | 512 |
| 다국어 지원 | 100+ 언어 | 100+ 언어 | 한국어 전용 |
| dense + sparse | ✅ | ❌ | ❌ |

> 정확한 nDCG@10 수치: MTEB Leaderboard에서 직접 확인 → ARCHITECTURE.md에 스크린샷으로 첨부

## 선택 근거

1. **한국어 Retrieval 정확도 최상위** — MTEB 벤치마크 기준
2. **8192 토큰 입력** — e5-base(512)와 결정적 차이. 긴 청크도 잘림 없이 임베딩
3. **dense + sparse + multi-vector** — 하이브리드 검색 확장 가능성
4. **설계 원칙 "정확도 우선"** — 모델 크기(2.3GB) 및 속도 trade-off 감수

## 탈락 사유

- **e5-base**: 크기/속도 균형 좋으나, 정확도 5~8% 열위 + 512 토큰 제한
- **ko-sroberta**: 가볍지만 다국어 미지원 + 정확도 열위

## 변경 이력

- 최초 추천: multilingual-e5-base (크기/속도 균형)
- **[변경 2026-04-09]**: bge-m3로 변경. 사용자 원칙 "정확도 우선 투자" 확정 후 재평가

## 출처

- MTEB Leaderboard: https://huggingface.co/spaces/mteb/leaderboard
- bge-m3 모델 카드: https://huggingface.co/BAAI/bge-m3
