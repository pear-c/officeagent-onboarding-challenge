"""RAG 파이프라인 조율 — 캐시 확인 → 검색 → 프롬프트 → LLM → 캐시 저장."""


class RAGService:
    """질의응답 파이프라인 조율."""

    # TODO: 03-query 단계에서 구현
    # - check_cache(question) → CacheResult | None
    # - search(question) → list[SearchResult]
    # - build_prompt(question, chunks) → (system, user)
    # - generate_answer(system, user) → LLMResponse
    # - save_cache(question, answer) → None
    # - answer(question) → QueryAnswer
    # - answer_stream(question) → AsyncIterator[str]
    pass
