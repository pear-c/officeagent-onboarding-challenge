# 트러블슈팅 기록

프로젝트 진행 중 발견한 이슈와 해결 과정을 기록.

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

## TS-006. PDF 법률 조문이 청크 경계에서 잘리는 문제

**단계**: 05-pdf-enhance 테스트  
**증상**: Q3 "예방적 품질관리의 법적 근거는?" 질문에 Claude가 "청크가 일부 잘려있어 원문 확인 권장" 안내  
**원인**: pypdf + 재귀 분할(400자)로 PDF를 청킹하면, 법률 인용문(공공데이터법 제22조 전문)이 여러 청크에 걸쳐 분산됨. top-5 검색에서 조문 전체가 포함되지 않아 LLM이 불완전한 컨텍스트를 감지  
**영향**: 답변 정확도에는 문제 없지만(핵심 키워드는 포함), 긴 법률/규정 텍스트가 잘리면 LLM이 답변에 불확실성을 표시  
**해결**: 05-pdf-enhance에서 번호 헤더(`1. 제목`) 기반 마크다운 변환 → 섹션 단위 청킹 적용. After 테스트에서 "청크 잘려있어" 안내가 사라지고 깔끔한 답변 생성 확인. 응답 속도도 12778ms → 8496ms로 33% 개선.

---

## TS-007. LLM CLI 미설치 시 start.sh가 실패하지 않는 문제

**단계**: 제출 전 전체 테스트  
**증상**: codex CLI만 설치된 환경에서 `./start.sh` 실행 → CLI 체크 통과 → `.env`에 `LLM_ANSWER_PROVIDER=claude` → 질문 시 Claude 호출 실패  
**원인**: start.sh의 CLI 체크는 "설치 여부"만 확인하고, 실제 LLM 선택은 `.env` 값이 결정. 두 로직이 연동되지 않음  
**해결**: start.sh에서 `.env` 생성 후 설치된 CLI에 맞춰 `LLM_ANSWER_PROVIDER`를 자동 설정. claude 우선, claude 없으면 codex로 전환.

```bash
# 자동 감지 로직
if has_claude → LLM_ANSWER_PROVIDER=claude
elif has_codex → LLM_ANSWER_PROVIDER=codex (자동 전환 + 안내 메시지)
```

**교훈**: "한 줄 실행"을 목표로 하려면 사전 체크와 설정 생성이 연동되어야 한다. 체크만 하고 설정에 반영하지 않으면 의미 없음.

---

## TS-008. 문서 업로드 후에도 이전의 "찾을 수 없음" 캐시가 반환되는 문제

**단계**: 전체 테스트 (2026-04-15)
**증상**:
1. 문서 업로드 전에 질문 → "제공된 문서에서 해당 내용을 찾을 수 없습니다" 응답
2. 이 응답이 캐시됨
3. 이후 관련 문서를 업로드하고 동일 질문 → 여전히 캐시된 "찾을 수 없습니다" 반환 (0ms, 캐시)

**원인**: 캐시 무효화 로직은 "문서 변경 시 해당 문서와 연관된 캐시만 삭제". 그런데 `answerable=false` 답변은 `sources=[]` → `source_files=[]`로 저장되어 **어떤 문서와도 연관되지 않음**. 따라서 새 문서를 업로드해도 이 캐시는 영구히 삭제되지 않음.

**해결**: `answerable=false`인 경우 **캐시 저장 자체를 건너뛰도록** 변경.

```python
# rag_service.py — JSON 응답
if answer_data.get("answerable", True):
    await self._save_answer_cache(...)

# rag_service.py — 스트리밍
if "찾을 수 없습니다" not in accumulated_text:
    await self._save_stream_cache(...)
```

**근거**:
1. "찾을 수 없다" 답변은 **"현재 문서 상태 기준"이지 영구 진실이 아님** — 문서는 언제든 추가될 수 있음
2. 캐시 이득이 적음 — refusal은 LLM 호출 없이도 빠르게 판정 가능 (검색 결과 빈 경우)
3. 답변 가능한 질문만 캐시하면 무효화 로직이 단순해짐 (source_files 기반 삭제가 의미 있음)

**근본 해결 (추가 적용)**: answerable=false 캐시 방지만으로는 answerable=true 캐시도 새 문서 추가 시 stale해지는 문제가 남음. → **문서 업로드(추가/변경) 시 전체 QA 캐시 삭제**(`invalidate_all()`)로 전환.

```python
# ingest_service.py — 문서 업로드 시
if self._cache_service is not None:
    await self._cache_service.invalidate_all()
```

**전체 삭제를 선택한 근거**:
1. 문서 추가 시 기존 답변의 관련성이 달라질 수 있음 (새 문서에 더 정확한 정보가 있을 수 있음)
2. 문서 업로드 빈도 << 질의 빈도 → 전체 캐시 재빌드 비용이 낮음
3. 파일별 추적(source_files)보다 확실하고 엣지 케이스 없음

**향후 개선**: 문서 추가 빈도가 높아지면 Corpus 버전 태깅(`corpus:version` Redis 키) 기반 lazy invalidation으로 전환 가능. 현재는 전체 삭제가 도메인 특성에 가장 안전.

**교훈**: 캐시 무효화는 "캐시 키의 의존성"을 명확히 해야 한다. 빈 의존성(source_files=[])을 가진 캐시는 무효화 불가능한 좀비 캐시가 된다. 추적 누락 가능성이 있으면 전체 무효화가 더 안전한 선택이다.

---

## TS-009. 거절 판정 문자열 매칭이 LLM 동의어에 취약

**단계**: 제출 전 검증 (2026-04-16)
**증상**: 스트리밍 응답에서 `is_answerable = "찾을 수 없습니다" not in accumulated_text` 식 단일 패턴 매칭. LLM이 "확인할 수 없습니다", "답변하기 어렵습니다", "정보가 없습니다" 같은 **동의어**를 쓰면 answerable=true로 오판정 → 근거 없는 답변이 캐시에 저장되고 출처까지 표시됨.

**원인**: 프롬프트에는 "정확히 '찾을 수 없습니다'로 답하세요"라고 지시했지만, Claude는 때때로 다른 표현을 쓰는 경향이 있음(helpfulness 성향).

**해결**: 이중 방어 적용.

1. **프롬프트 측**: 동의어 사용 금지를 명시
   ```
   3. 문서에 답이 없으면 정확히 "제공된 문서에서 해당 내용을 찾을 수 없습니다."라고 답하세요.
      동의어("확인할 수 없습니다", "답변하기 어렵습니다" 등) 사용 금지.
   ```
2. **서버 측**: 패턴 리스트 매칭
   ```python
   _REFUSAL_PATTERNS = ("찾을 수 없습니다", "확인할 수 없", "답변할 수 없",
                        "정보가 없", "제공되지 않", "포함되어 있지 않", ...)
   def _is_refusal(text): return any(p in text for p in _REFUSAL_PATTERNS)
   ```

**교훈**: LLM은 프롬프트 지시를 100% 따르지 않는다. 형식이 중요한 판정(거절 여부, JSON 구조 등)은 **프롬프트 + 서버 측 검증** 이중화가 안전하다.
