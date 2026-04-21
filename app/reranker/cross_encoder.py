"""Cross-encoder reranker — bge-reranker-v2-m3 기반 재정렬."""

import logging
import time

from sentence_transformers import CrossEncoder

from app.vectorstore.chroma_store import SearchResult

logger = logging.getLogger(__name__)


class Reranker:
    """Cross-encoder로 query-document 쌍의 관련성을 재평가하여 순서를 재정렬."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        start = time.time()
        logger.info("Reranker 모델 로딩 시작: %s", model_name)
        self._model = CrossEncoder(model_name)
        elapsed = time.time() - start
        logger.info("Reranker 모델 로딩 완료: %.1f초", elapsed)

    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """검색 결과를 cross-encoder 점수로 재정렬 후 상위 top_k 반환."""
        if not results:
            return results

        pairs = [[query, r.text] for r in results]
        scores = self._model.predict(pairs)

        scored = sorted(
            zip(results, scores), key=lambda x: x[1], reverse=True,
        )

        reranked = [r for r, _ in scored[:top_k]]

        if logger.isEnabledFor(logging.DEBUG):
            for r, s in scored[:top_k]:
                logger.debug(
                    "rerank score=%.4f file=%s chunk=%s",
                    s, r.metadata.get("source_file", "?"), r.chunk_id,
                )

        return reranked
