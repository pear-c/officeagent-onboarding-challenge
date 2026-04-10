"""캐시 서비스 — 정확 일치 + 유사 질문 + 무효화."""


class CacheService:
    """3단계 캐시 관리."""

    # TODO: 03-query 단계에서 구현
    # - get_exact(question_hash) → CachedAnswer | None
    # - get_similar(question_embedding, threshold) → CachedAnswer | None
    # - save(question, question_embedding, answer) → None
    # - invalidate_by_document(filename) → int (삭제된 키 수)
    # - get_document_hash(filename) → str | None
    # - save_document_hash(filename, content_hash) → None
    pass
