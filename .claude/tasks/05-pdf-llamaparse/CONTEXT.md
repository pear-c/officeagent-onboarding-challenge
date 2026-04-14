# 05-pdf-enhance — CONTEXT

## 결정 이력

### D34. LlamaParse 제외 결정 (2026-04-14)

- **결정**: LlamaParse 사용하지 않음. pypdf 유지.
- **이유**: API Key 필수, 클라우드 전송, docker compose up 한 줄 실행 불가
- **검증**: 검증 에이전트 + 실제 실험에서 확인 (정답률 80%로 오히려 하락)

### D35. 경량 마크다운 변환으로 방향 전환 (2026-04-14)

- **결정**: pypdf 출력에 번호 헤더(`^\d+\.\s+[가-힣]`) → `##` 변환만 추가
- **이유**: section 메타데이터 보존 + 마크다운 인식 청킹 재활용
- **결과**: 정답률 100% 유지, 응답 속도 22% 개선, TS-006 해결

### D36. router.py 수정 방식 — force_markdown 파라미터 (2026-04-14)

- **결정**: `chunk_document()`에 `force_markdown=False` 파라미터 추가
- **이유**: TextExtractor ABC 시그니처 변경 없이, ingest_service에서 확장자 판단 후 전달

### D37. LLM 기본 모델 Claude 유지 (2026-04-14)

- **결정**: 자동 평가에서 Codex 우위였지만, UI 비교에서 Claude가 답변 품질(구조화, 가독성, 투명성) 우위
- **이유**: 정답률 동일 시 사용자 체감 품질이 차별점. 메트릭 ≠ UX.
- **근거**: eval/images/ 스크린샷 비교 (INT-008-1)

### D38. LlamaParse 실험 결과 — "더 많은 정보 ≠ 더 좋은 검색" (2026-04-14)

- **실험**: 별도 브랜치에서 LlamaParse 적용, 동일 질문 5개 비교
- **결과**: 텍스트 2.1배, 청크 1.5배, 업로드 16배 느림, **정답률 80% (하락)**
- **원인**: 청크 264개로 검색 공간 확대 → 관련 청크가 top-5에서 밀림
- **교훈**: RAG에서는 추출 품질보다 검색 정밀도가 중요

## 최종 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `app/extraction/text_extractor.py` | `_to_markdown()` 추가 (+8줄) |
| `app/chunking/router.py` | `force_markdown` 파라미터 (+4줄) |
| `app/services/ingest_service.py` | PDF일 때 `force_markdown=True` (+2줄) |
| `static/index.html` | marked.js 마크다운 렌더링 + answerable=false 출처 숨김 |
| `eval/run.py` | `--filter` 옵션 추가 |
| `eval/golden_dataset.json` | Q21~Q50 재구성 (신규 파일 기준) |
| `sample-docs/` | 3개 삭제 + 3개 추가 (md, txt, pdf) |
| `start.sh`, `scripts/seed.sh` | 평가자 파일 2개만 자동 업로드 |
| `docs/TROUBLESHOOTING.md` | TS-006, INT-008-1, INT-010 추가 |
| `PROMPT_DESIGN.md` | 삭제된 파일 참조 수정 |
