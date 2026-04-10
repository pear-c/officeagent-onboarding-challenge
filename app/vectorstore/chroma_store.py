"""Chroma 벡터 DB 클라이언트."""

import logging
from dataclasses import dataclass

import chromadb

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchResult:
    """벡터 검색 결과."""

    chunk_id: str
    text: str
    metadata: dict
    distance: float


class ChromaStore:
    """Chroma 서버 연결 + 벡터 CRUD."""

    def __init__(self, host: str, port: int, collection_name: str):
        self._client = chromadb.HttpClient(host=host, port=port)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "Chroma 연결: %s:%d, collection=%s (%d vectors)",
            host, port, collection_name, self._collection.count(),
        )

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        """벡터 + 문서 + 메타데이터 저장."""
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info("Chroma 저장 완료: %d vectors", len(ids))

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """벡터 유사도 검색."""
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        items: list[SearchResult] = []
        if not results["ids"] or not results["ids"][0]:
            return items

        for i, chunk_id in enumerate(results["ids"][0]):
            items.append(
                SearchResult(
                    chunk_id=chunk_id,
                    text=results["documents"][0][i] if results["documents"] else "",
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    distance=results["distances"][0][i] if results["distances"] else 0.0,
                )
            )
        return items

    def delete_by_document(self, filename: str) -> None:
        """특정 문서의 모든 벡터 삭제 (재업로드 시 사용)."""
        self._collection.delete(where={"source_file": filename})
        logger.info("Chroma 삭제 완료: source_file=%s", filename)

    def list_documents(self) -> list[dict]:
        """저장된 문서 메타데이터 조회 (고유 filename별 요약)."""
        all_meta = self._collection.get(include=["metadatas"])
        if not all_meta["metadatas"]:
            return []

        # filename별 청크 수 집계
        doc_map: dict[str, dict] = {}
        for meta in all_meta["metadatas"]:
            fname = meta.get("source_file", "unknown")
            if fname not in doc_map:
                doc_map[fname] = {
                    "filename": fname,
                    "content_hash": meta.get("content_hash", ""),
                    "chunk_count": 0,
                    "file_size": meta.get("file_size", 0),
                }
            doc_map[fname]["chunk_count"] += 1

        return list(doc_map.values())

    def get_document_chunk_count(self, filename: str) -> int:
        """특정 문서의 청크 수 조회."""
        result = self._collection.get(
            where={"source_file": filename},
            include=[],
        )
        return len(result["ids"])

    def count(self) -> int:
        """저장된 벡터 총 수."""
        return self._collection.count()

    def heartbeat(self) -> bool:
        """Chroma 서버 healthcheck."""
        try:
            self._client.heartbeat()
            return True
        except Exception:
            return False
