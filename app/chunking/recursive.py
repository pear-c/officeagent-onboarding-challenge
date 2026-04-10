"""청킹 — 재귀 분할 + 마크다운 인식 하이브리드."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    """청크 결과 (불변)."""
    text: str
    chunk_id: int
    source_file: str
    section: str  # 마크다운 헤더 경로 (예: "코드 리뷰 정책 > 리뷰 체크리스트")
    start_char: int
    end_char: int


# TODO: 02-ingestion 단계에서 구현
# def recursive_chunk(text, chunk_size, overlap) -> list[Chunk]
# def markdown_aware_chunk(text, chunk_size, overlap) -> list[Chunk]
# def chunk_document(text, filename, chunk_size=400, overlap=80) -> list[Chunk]
