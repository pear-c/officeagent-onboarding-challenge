# 트러블슈팅 기록

프로젝트 진행 중 발견한 이슈와 해결 과정을 기록한다.

---

## TS-001. Chroma healthcheck 실패 (v1 API deprecated)

**단계**: 02-ingestion 테스트 B  
**증상**: `docker compose ps`에서 Chroma 컨테이너가 계속 `unhealthy` 상태  
**원인**: `docker-compose.yml`의 healthcheck가 `/api/v1/heartbeat`를 호출하는데, Chroma 최신 버전이 v2 API로 전환되어 v1 엔드포인트가 `{"error":"Unimplemented","message":"The v1 API is deprecated. Please use /v2 apis"}` 반환  
**해결**: healthcheck URL을 `/api/v2/heartbeat`로 변경. 추가로 Chroma 컨테이너에 `curl`이 없어서 `python3 urllib`로 대체  

```yaml
# before
test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]

# after
test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v2/heartbeat')"]
```

---

## TS-002. 마크다운 청킹 시 짧은 청크 과다 생성

**단계**: 02-ingestion 테스트 B  
**증상**: 마크다운 문서 청킹 시 chunk_size=400 대비 극단적으로 작은 청크 다수 생성

| 문서 | 글자 수 | 생성 청크 | 기대 청크 | 최소 청크 | 평균 크기 |
|------|---------|----------|----------|----------|----------|
| `01-rag-overview.md` | 4,746자 | 28개 | ~12개 | 23자 | 156자 |
| `development-guide.md` | 615자 | 5개 | ~2개 | 69자 | 107자 |
| `company-policy.txt` | 528자 | 2개 | 2개 | 248자 | 302자 (정상) |

**원인**: 마크다운 인식 청킹이 헤더(##, ###)별로 섹션을 먼저 분리한 뒤, 각 섹션이 chunk_size 이하면 그대로 1개 청크로 생성. 짧은 섹션(23~75자)도 별도 청크가 됨.

**영향**:
1. **검색 정확도 저하** — 짧은 청크는 문맥 부족으로 임베딩 벡터가 의미를 제대로 담지 못함
2. **top-K 노이즈** — top-K=5 검색 시 무의미한 짧은 청크가 상위 차지
3. **LLM 컨텍스트 낭비** — top-K=5 × 50자 = 250자 vs 적절한 크기면 5 × 350자 = 1,750자
4. **임베딩 비용** — 28개 vs 15개 → 호출 ~2배

**해결**: 마크다운 인식 청킹에 짧은 섹션 병합 로직 추가 (구현 예정)
- 인접 섹션이 합쳐도 chunk_size 이하면 병합
- 최소 청크 크기(100자) 미만 섹션은 다음 섹션과 합침

---

## TS-003. setuptools 멀티 패키지 감지 에러

**단계**: 02-ingestion 테스트 A (단위 테스트 환경 구성)  
**증상**: `pip install -e ".[dev]"` 실행 시 에러

```
error: Multiple top-level packages discovered in a flat-layout: ['app', 'eval', 'retrobot'].
```

**원인**: 프로젝트 루트에 `app/`, `eval/`, `retrobot/` 3개 디렉토리가 있어서 setuptools가 어떤 패키지를 빌드할지 혼란  
**해결**: `pyproject.toml`에 패키지 범위 명시

```toml
[tool.setuptools.packages.find]
include = ["app*"]
```

**우회**: editable 설치 대신 `PYTHONPATH=.`으로 직접 모듈 경로 지정도 가능

```bash
PYTHONPATH=. pytest tests/unit/ -v
```

---

## TS-004. SSE 스트리밍에서 원시 JSON이 UI에 표시됨

**단계**: 03-query 테스트  
**증상**: 최초 질문 시 UI에 답변 대신 원시 JSON이 그대로 표시됨. 캐시 히트 시에는 정상.

```json
{"answer": "제공된 문서에서 해당 내용을 찾을 수 없습니다.", "sources": [], "answerable": false}
```

**원인**: `SYSTEM_PROMPT`가 JSON 형식 출력을 지시하는데, `answer_stream()`에서도 동일한 프롬프트를 사용. LLM이 JSON 토큰을 그대로 스트리밍하여 UI에 원시 JSON 표시. 캐시 히트 시에는 파싱된 `answer` 텍스트만 저장되어 있어 정상 동작.

**해결**: 스트리밍 전용 시스템 프롬프트(`SYSTEM_PROMPT_STREAM`) 추가. JSON 대신 자연어 한국어 텍스트만 출력하도록 지시. sources는 벡터 검색에서 이미 확보했으므로 LLM이 중복 출력할 필요 없음.

```python
# templates.py
SYSTEM_PROMPT        # JSON 응답용 (POST /api/v1/query)
SYSTEM_PROMPT_STREAM # 자연어 텍스트용 (POST /api/v1/query/stream)
```

**교훈**: 스트리밍과 비스트리밍은 출력 포맷 요구사항이 다르므로 프롬프트를 분리해야 함.

---

## TS-005. Claude SDK max_turns=1에서 응답 생성 안 됨

**단계**: 04-eval Claude 측정  
**증상**: 20케이스 전부 `"Claude 응답 오류: Reached maximum number of turns (1)"` 에러. 결과 파일에 정상 답변 0건.

**원인**: `ClaudeAgentOptions(max_turns=1)`로 설정했으나, SDK 내부에서 1턴이 "프롬프트 전송 + 응답 수신"이 아니라 응답 생성 전에 소진됨. `ResultMessage.is_error=True` + `errors` 리스트에 "Reached maximum number of turns (1)" 메시지 포함.

**해결**: 
1. `max_turns=1` → `max_turns=2`로 변경 (1턴 여유)
2. `errors` 리스트에서 "maximum number of turns" 문자열 포함 시 정상 동작으로 처리
3. `result_text`가 있으면 에러 무시하고 정상 반환

```python
# before — stop_reason으로 판별 시도 (실패)
is_max_turns = msg.stop_reason and "max" in msg.stop_reason.lower()

# after — errors 리스트 문자열 매칭 (성공)
is_max_turns = any("maximum number of turns" in e.lower() for e in errors)
```

**교훈**: claude-agent-sdk의 에러 보고 방식이 `stop_reason`이 아닌 `errors` 리스트를 통해 전달됨. SDK 문서보다 실제 동작을 검증해야 함.

---

# 면접 포인트 — 설계 결정과 트레이드오프

프로젝트에서 "왜 이렇게 했나?"로 설명할 수 있는 주요 결정들.

---

## INT-001. LLM 역할 분할을 인상론이 아닌 데이터로 결정

**질문**: "왜 Claude를 답변에, Codex를 보조에 썼나요?"  
**답변 구조**:
1. 처음에는 **잠정 가설**만 세움 (Claude=답변, Codex=보조)
2. `LLMProvider` 추상화로 **1줄 swap** 가능하게 설계
3. 골든 데이터셋 20케이스 × 7메트릭 **평가 하네스**를 만들어 실측
4. 측정 결과 표를 근거로 최종 확정

**핵심**: "인상론 vs 데이터" — 동일 코드 위에서 provider만 바꿔서 비교한 점.

---

## INT-002. 3단계 캐시 설계 (Redis 정확일치 + Chroma 유사질문 + 무효화)

**질문**: "캐시를 왜 이렇게 복잡하게?"  
**답변 구조**:
1. LLM 호출 3~15초 → 캐시 히트 시 ~5ms (600배 차이)
2. **정확 일치**(SHA-256 해시): 동일 질문 즉시 반환
3. **유사 질문**(벡터 유사도 ≥ 0.95): "교육비 한도?" ≈ "교육비 지원은 얼마까지?"
4. **문서 변경 시 무효화**: 문서 재업로드 → 관련 캐시 자동 삭제 (stale 답변 방지)
5. 유사 질문에 Chroma를 별도 collection으로 사용한 이유: Redis RediSearch 모듈 설치 불필요, 이미 Chroma 있음

**핵심**: "단순 TTL 캐시가 아니라, 문서 변경까지 고려한 무효화 전략"

---

## INT-003. SSE 스트리밍에서 sources를 토큰보다 먼저 전송 (D25)

**질문**: "스트리밍 응답을 왜 이런 순서로?"  
**답변 구조**:
1. 벡터 검색은 ~100ms에 완료, LLM 호출은 3~15초
2. sources(출처)를 **먼저 보내면** 사용자가 출처를 보면서 답변 생성을 기다릴 수 있음
3. 구현 복잡도 차이 거의 없음 (yield 순서만 변경)
4. `sources → token(반복) → done` 순서로 SSE 이벤트 설계

**핵심**: "사용자 체감 대기시간을 줄이는 UX 설계"

---

## INT-004. 스트리밍 vs 비스트리밍 프롬프트 분리 (TS-004)

**질문**: "프롬프트를 왜 두 개로 분리?"  
**답변 구조**:
1. JSON 엔드포인트(`/query`): LLM이 `{"answer":"...", "sources":[...]}` 구조화 출력 → 서버가 파싱
2. SSE 엔드포인트(`/query/stream`): 토큰 단위 실시간 전송 → JSON이면 원시 텍스트가 UI에 노출
3. **실제 버그 경험**: 동일 프롬프트 사용 → UI에 원시 JSON 표시됨
4. 해결: `SYSTEM_PROMPT`(JSON) + `SYSTEM_PROMPT_STREAM`(자연어) 분리

**핵심**: "동일 기능이라도 출력 채널(JSON vs 스트리밍)에 따라 프롬프트가 달라야 한다"

---

## INT-005. 평가 하네스에서 NoOpCacheService 패턴

**질문**: "평가할 때 캐시를 어떻게 우회했나요?"  
**답변 구조**:
1. 순수 LLM 성능을 측정하려면 캐시를 거치면 안 됨
2. `redis-cli FLUSHDB`는 문서 해시(`doc:hash:*`)까지 날려서 문서 재업로드 필요
3. **NoOpCacheService**: 항상 miss 반환하는 stub → RAGService 코드 수정 없이 DI로 교체
4. 동일한 RAGService, 동일한 프롬프트, provider만 swap → 공정한 비교

**핵심**: "DI(의존성 주입) 설계 덕분에 테스트/평가 시 컴포넌트를 쉽게 교체 가능"

---

## INT-006. 하이브리드 청킹 + 짧은 섹션 병합 (TS-002)

**질문**: "청킹 전략을 왜 이렇게?"  
**답변 구조**:
1. `.txt`/`.pdf` → 재귀 분할 (`\n\n` → `\n` → `.` → ` ` 우선순위)
2. `.md` → 마크다운 헤더 인식 분할 → 재귀 fallback
3. **실제 문제 발견**: 짧은 마크다운 섹션(23자)이 별도 청크 → 검색 정확도 저하
4. 양방향 병합 로직 추가: 28개 → 21개 청크, 평균 156자 → 208자
5. 이 수치는 실측 결과 (인상론 아님)

**핵심**: "전략 설계 → 실측 → 문제 발견 → 개선" 사이클을 돌렸다는 점

---

## INT-007. LLMProvider 추상화 — 1줄 swap 설계

**질문**: "두 개의 LLM을 어떻게 관리?"  
**답변 구조**:
1. `LLMProvider` ABC: `generate()`, `stream()`, `model_name` 프로퍼티
2. `ClaudeProvider`(claude-agent-sdk) / `CodexProvider`(subprocess) 구현
3. `config.py`에 `llm_answer_provider=claude` 환경변수 → 팩토리에서 선택
4. 평가 하네스에서 provider만 swap해 동일 조건 비교 가능

**핵심**: "Strategy 패턴 적용 → 비즈니스 로직(RAGService)이 구체 LLM에 의존하지 않음"

---

## INT-008. 초기 가설이 데이터로 뒤집힌 경험 — Claude vs Codex

**질문**: "왜 초기에 Claude를 메인으로 가정했다가 바꿨나요?"  
**답변 구조**:
1. 초기 가설: "Claude = 정확도 최고 → 답변 생성, Codex = 속도 → 보조"
2. 50케이스 × 7메트릭 측정 결과, **정확도 동률 + 거절 정확도 Codex 압승 + 속도 2.4배**
3. Claude의 Refusal 83% — "도움이 되려는" 성향이 RAG에서는 환각 위험으로 작용
4. Codex의 Refusal 100% — 지시 추종이 강해 "모르면 모른다"를 정확히 따름
5. 가설을 뒤집고 Codex를 기본 모델로 확정

**핵심**: "똑똑한 모델 ≠ RAG에 적합한 모델". 데이터로 검증하지 않았으면 잘못된 선택을 했을 것.

---

## INT-009. 평가 하네스 고도화 — 20케이스에서 차이가 안 나던 문제

**질문**: "평가를 어떻게 고도화했나요?"  
**답변 구조**:
1. 처음 20케이스(simple docs 2개)에서 양쪽 모두 100% → 차이 식별 불가
2. **복잡한 문서 3개 추가** (200줄 인사규정, 150줄 아키텍처, 100줄 회의록)
3. **난이도 유형 확장**: 수치 계산(4), 멀티홉(2), 함정(6), 긴 답변(1) 추가
4. 50케이스로 확장 후 비로소 Retrieval Hit, Refusal에서 모델 간 차이 발생
5. 특히 Q48(스톡옵션 함정), Q49(미결 사항 구분)에서 모델 차이 극명

**핵심**: "평가 데이터셋의 품질이 평가 결과의 품질을 결정한다"

---

## INT-010. PDF 추출 전략 — LlamaParse vs pypdf 트레이드오프

**질문**: "PDF 추출을 왜 pypdf로 했나요? LlamaParse 같은 고급 파서는 검토 안 했나요?"  
**답변 구조**:
1. **검토함**. LlamaParse(PDF→Markdown 변환)를 실제 테스트까지 진행
2. LlamaParse의 강점: 표/헤더/목록 구조를 마크다운으로 변환 → 기존 마크다운 인식 청킹 재활용 가능
3. **그러나 이 과제에서는 부적합**:

| 제약 | LlamaParse | pypdf |
|------|-----------|-------|
| 실행 방식 | API Key 발급 + `.env` 설정 필요 | `docker compose up` 한 줄로 끝 |
| 데이터 전송 | PDF가 외부 클라우드 서버로 전송 | 완전 로컬 처리 |
| 의존성 | `llama-parse` 패키지 + LlamaCloud 가입 | `pypdf` (이미 포함, MIT) |
| 대상 PDF 특성 | 복잡한 레이아웃/표/이미지에 최적 | 순수 텍스트 PDF에 충분 |

4. **핵심 트레이드오프**: 서버 배포 환경이라면 LlamaParse를 선택했겠지만, PRD의 "한 줄 실행 가능" 요구사항과 평가자의 환경 구성 부담을 고려하여 pypdf 유지를 결정
5. 대신 **pypdf + 경량 마크다운 변환 후처리**로 section 메타데이터 보존 — 외부 의존성 없이 마크다운 인식 청킹 재활용

### 실험 결과 (Before/After)

> LlamaParse 실험은 별도 브랜치(`experiment/llamaparse-comparison`)에서 진행. 본 코드에는 미반영.

```
[Before — pypdf + 재귀 분할]
- 추출 방식: pypdf PdfReader.extract_text()
- 청크 수: (측정 예정)
- section 메타데이터: "" (빈 문자열, 구조 정보 없음)
- 표 보존: 텍스트만 (셀 구분 유실)
- 외부 의존성: 없음

[After — LlamaParse + 마크다운 청킹]
- 추출 방식: LlamaParse API (PDF→Markdown)
- 청크 수: (측정 예정)
- section 메타데이터: 헤더 경로 보존 (예: "1. 비밀번호 정책")
- 표 보존: 마크다운 테이블로 변환
- 외부 의존성: LLAMA_CLOUD_API_KEY 필요

[최종 선택 — pypdf + 경량 마크다운 변환]
- 추출 방식: pypdf + 번호 헤더 정규식 변환
- 청크 수: (측정 예정)
- section 메타데이터: 번호 헤더 보존 (예: "1. 비밀번호 정책")
- 표 보존: 텍스트만 (현재 PDF에 표 없음)
- 외부 의존성: 없음
```

**핵심**: "서버 배포라면 LlamaParse, Docker 한 줄 실행이라면 pypdf — 환경 제약에 맞는 선택을 데이터로 검증했다"
