"""평가 메트릭 계산 — 골든 데이터셋 기반 7개 메트릭."""

import statistics


def retrieval_hit_rate(results: list[dict], golden: list[dict]) -> float:
    """검색된 top-K sources에 expected_source가 포함된 비율.

    answerable=true인 케이스만 대상.
    """
    hits, total = 0, 0
    for case, gold in zip(results, golden):
        if not gold.get("answerable"):
            continue
        total += 1
        expected = gold.get("expected_source", "")
        source_files = [s.get("file", "") for s in case.get("sources", [])]
        if expected in source_files:
            hits += 1
    return hits / total if total > 0 else 0.0


def citation_accuracy(results: list[dict], golden: list[dict]) -> float:
    """LLM이 인용한 출처가 expected_source와 일치하는 비율.

    answerable=true인 케이스만 대상.

    NOTE: 현재 구현에서는 retrieval_hit_rate와 동일한 값을 반환한다.
    RAGService._build_sources()가 LLM 인용 → 검색 결과 fallback으로 동작하여
    sources가 혼합되어 있기 때문. 향후 검색 결과(retrieval)와 LLM 인용(citation)을
    별도 필드로 분리하면 차별화 가능.
    """
    hits, total = 0, 0
    for case, gold in zip(results, golden):
        if not gold.get("answerable"):
            continue
        total += 1
        expected = gold.get("expected_source", "")
        source_files = [s.get("file", "") for s in case.get("sources", [])]
        if expected in source_files:
            hits += 1
    return hits / total if total > 0 else 0.0


def refusal_accuracy(results: list[dict], golden: list[dict]) -> float:
    """answerable=false 케이스에서 거절 응답한 비율.

    "찾을 수 없습니다" 포함 또는 answerable=false 판정.
    """
    hits, total = 0, 0
    refusal_phrases = ["찾을 수 없습니다", "없습니다", "답변할 수 없"]
    for case, gold in zip(results, golden):
        if gold.get("answerable"):
            continue
        total += 1
        answer = case.get("answer", "")
        is_refused = (
            not case.get("answerable", True)
            or any(phrase in answer for phrase in refusal_phrases)
        )
        if is_refused:
            hits += 1
    return hits / total if total > 0 else 0.0


def keyword_hit_rate(results: list[dict], golden: list[dict]) -> float:
    """답변에 expected_keywords가 모두 포함된 비율.

    answerable=true인 케이스만 대상.
    """
    hits, total = 0, 0
    for case, gold in zip(results, golden):
        if not gold.get("answerable"):
            continue
        keywords = gold.get("expected_keywords", [])
        if not keywords:
            continue
        total += 1
        answer = case.get("answer", "")
        if all(kw in answer for kw in keywords):
            hits += 1
    return hits / total if total > 0 else 0.0


def json_parse_rate(results: list[dict]) -> float:
    """JSON 응답이 정상 파싱된 비율."""
    if not results:
        return 0.0
    parsed = sum(1 for r in results if r.get("json_parsed", False))
    return parsed / len(results)


def latency_percentile(results: list[dict], p: int = 50) -> float:
    """응답 시간 p-percentile (ms)."""
    latencies = [r.get("latency_ms", 0) for r in results if r.get("latency_ms")]
    if not latencies:
        return 0.0
    latencies.sort()
    idx = int(len(latencies) * p / 100)
    idx = min(idx, len(latencies) - 1)
    return float(latencies[idx])


def compute_all(results: list[dict], golden: list[dict]) -> dict:
    """7개 메트릭 일괄 계산."""
    return {
        "retrieval_hit_rate": round(retrieval_hit_rate(results, golden), 4),
        "citation_accuracy": round(citation_accuracy(results, golden), 4),
        "refusal_accuracy": round(refusal_accuracy(results, golden), 4),
        "keyword_hit_rate": round(keyword_hit_rate(results, golden), 4),
        "json_parse_rate": round(json_parse_rate(results), 4),
        "latency_p50_ms": round(latency_percentile(results, 50)),
        "latency_p95_ms": round(latency_percentile(results, 95)),
    }
