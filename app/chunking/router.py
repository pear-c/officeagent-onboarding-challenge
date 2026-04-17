"""청킹 라우터 — 파일 포맷별 청킹 전략 분기."""

from app.chunking.markdown import markdown_aware_chunk
from app.chunking.recursive import Chunk, recursive_chunk


def chunk_document(
    text: str,
    filename: str,
    chunk_size: int = 400,
    overlap: int = 80,
    force_markdown: bool = False,
) -> list[Chunk]:
    """파일 확장자에 따라 적절한 청킹 전략을 선택하고 Chunk 리스트 반환.

    - .md 또는 force_markdown=True: 마크다운 인식 (헤더 기반 섹션 분할 → 재귀 fallback)
    - .txt 등: 재귀 분할
    """
    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""

    if ext == ".md" or force_markdown:
        raw_chunks = markdown_aware_chunk(text, chunk_size, overlap)
        return _build_chunks_with_sections(raw_chunks, filename, text)

    raw_texts = recursive_chunk(text, chunk_size, overlap)
    return _build_chunks_plain(raw_texts, filename, text)


def _build_chunks_with_sections(
    section_chunks: list[tuple[str, str]],
    filename: str,
    original_text: str,
) -> list[Chunk]:
    """마크다운 청킹 결과 → Chunk 객체 리스트.

    동일 텍스트 중복 매칭 방지를 위해 이전 검색 위치 이후부터 find.
    """
    chunks: list[Chunk] = []
    search_from = 0
    for idx, (section, chunk_text) in enumerate(section_chunks):
        pos = original_text.find(chunk_text, search_from)
        start = max(pos, 0)
        chunks.append(
            Chunk(
                text=chunk_text,
                chunk_id=idx,
                source_file=filename,
                section=section,
                start_char=start,
                end_char=start + len(chunk_text),
            )
        )
        if pos >= 0:
            search_from = start + len(chunk_text)
    return chunks


def _build_chunks_plain(
    texts: list[str],
    filename: str,
    original_text: str,
) -> list[Chunk]:
    """재귀 분할 결과 → Chunk 객체 리스트.

    동일 텍스트 중복 매칭 방지를 위해 이전 검색 위치 이후부터 find.
    """
    chunks: list[Chunk] = []
    search_from = 0
    for idx, chunk_text in enumerate(texts):
        pos = original_text.find(chunk_text, search_from)
        start = max(pos, 0)
        chunks.append(
            Chunk(
                text=chunk_text,
                chunk_id=idx,
                source_file=filename,
                section="",
                start_char=start,
                end_char=start + len(chunk_text),
            )
        )
        if pos >= 0:
            search_from = start + len(chunk_text)
    return chunks
