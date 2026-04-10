# 02-ingestion — CHECKLIST

## 0. 사전 준비

- [x] [AI] feature/02-ingestion 브랜치 생성
- [x] [AI] PLAN.md / CONTEXT.md / CHECKLIST.md 작성

## 1. 텍스트 추출 모듈

- [x] [AI] `app/extraction/__init__.py` 생성
- [x] [AI] `app/extraction/text_extractor.py` — TextExtractor ABC + Txt/Md/Pdf 추출기 + 팩토리
- [x] [AI] `tests/unit/test_extraction.py` — 단위 테스트

## 2. 청킹 모듈

- [x] [AI] `app/chunking/recursive.py` — `recursive_chunk()` 구현 (Chunk dataclass 유지)
- [x] [AI] `app/chunking/markdown.py` — `markdown_aware_chunk()` 구현
- [x] [AI] `app/chunking/router.py` — `chunk_document()` 포맷별 분기
- [x] [AI] `tests/unit/test_chunking.py` — 경계 케이스 (빈 문자열, 한글, overlap)

## 3. 임베딩 래퍼

- [x] [AI] `app/embedding/embedder.py` — SentenceTransformer 래퍼 (embed, embed_query)

## 4. Chroma 클라이언트

- [x] [AI] `app/vectorstore/chroma_store.py` — 연결 + add/search/delete/list_documents/get_document_chunk_count

## 5. Redis 클라이언트 (해시만)

- [x] [AI] `app/cache/redis_cache.py` — 비동기 연결 + get/set/delete_document_hash + close

## 6. IngestService

- [x] [AI] `app/services/ingest_service.py` — 파이프라인 조율 + 로깅 + 에러 메시지 sanitize

## 7. DI + Lifespan + Exception Handler

- [x] [AI] `app/api/deps.py` — get_embedder, get_chroma_store, get_redis_cache, get_ingest_service
- [x] [AI] `app/main.py` — Lifespan (모델 로딩, DB 연결, IngestService, 종료) + exception handler
- [x] [AI] `app/config.py` — max_file_size, max_filename_length 추가

## 8. API 라우터

- [x] [AI] `app/api/routers/ingest.py` — POST/GET + 스트리밍 크기 검증 + filename 검증

## 9. 파이프라인 5단계 (검증)

- [x] [AI] Python 파일 문법 검사 — 14개 전체 통과
- [x] [AI] 보안 패턴 검사 — 시크릿 없음, 위험 함수 없음

## 10. 파이프라인 6단계 (리뷰)

- [x] [AI] 설계 리뷰 — PLAN.md 반영 확인
- [x] [AI] 코드 품질 리뷰 — HIGH 2개 수정 (IngestService 싱글턴, Chroma 전체 스캔)
- [x] [AI] 보안 리뷰 — MEDIUM 2개 수정 (filename 검증, 에러 메시지 sanitize)
- [x] [AI] 성능 리뷰 — _build_existing_doc_info 전용 메서드 추가
- [x] HIGH 이슈 수정 → 5단계 재실행 통과

## 10.1. 리뷰에서 남은 MEDIUM/LOW (다음 단계로 이연)

- [ ] `tests/unit/test_ingest_service.py` — IngestService Mock 단위 테스트 (03-query에서 추가)
- [ ] `tests/integration/` — API 엔드포인트 통합 테스트 (Docker 의존)
- [ ] `tests/unit/test_extraction.py` — PdfExtractor.extract() 테스트 (PDF 샘플 필요)
- [ ] `chroma_store.py:list_documents()` — 대량 데이터 시 페이지네이션 (현재 불필요)

## 11. 청킹 개선 (테스트 중 발견)

- [x] [AI] 마크다운 짧은 섹션 양방향 병합 로직 추가
- [x] [AI] Chroma healthcheck v1 → v2 수정
- [x] [AI] docs/TROUBLESHOOTING.md 생성
- [x] [AI] knowledge/decisions/08-chunking-size-tradeoff.md 추가

## 12. 테스트

- [x] [USER] 단위 테스트 27 passed
- [x] [USER] 전체 파이프라인 (TXT/MD/PDF 업로드 + 중복 감지 + 문서 목록 + UI)

## 13. 커밋 + push

- [x] [AI] feature/02-ingestion 1차 커밋 + push
- [x] [AI] 청킹 개선 2차 커밋 + push
