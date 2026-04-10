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
