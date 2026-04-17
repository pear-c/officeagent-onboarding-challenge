"""임베딩 래퍼 — sentence-transformers + bge-m3."""

import logging
import time

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class Embedder:
    """임베딩 모델 로딩 및 텍스트 → 벡터 변환.

    앱 시작 시 1회 로딩하여 app.state에 저장한다.
    """

    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "cpu"):
        start = time.time()
        logger.info("임베딩 모델 로딩 시작: %s (device=%s)", model_name, device)
        self._model = SentenceTransformer(model_name, device=device)
        elapsed = time.time() - start
        logger.info("임베딩 모델 로딩 완료: %.1f초", elapsed)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """텍스트 리스트 → 벡터 리스트."""
        if not texts:
            return []
        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """단일 쿼리 → 벡터."""
        return self.embed([query])[0]
