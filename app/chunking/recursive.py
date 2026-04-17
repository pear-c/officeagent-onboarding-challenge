"""청킹 — 재귀 분할 (Recursive Character Text Splitter)."""

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


# 구분자 우선순위: 단락 → 줄바꿈 → 문장 끝 → 공백
_SEPARATORS = ["\n\n", "\n", ". ", " "]


def _split_by_separator(text: str, separator: str) -> list[str]:
    """구분자로 텍스트를 분할하되, 구분자를 청크 끝에 보존."""
    if not text:
        return []
    parts = text.split(separator)
    # 구분자를 각 파트 끝에 붙여서 보존 (마지막 파트 제외)
    result = []
    for i, part in enumerate(parts):
        if i < len(parts) - 1:
            result.append(part + separator)
        elif part:  # 마지막 파트가 비어있지 않으면
            result.append(part)
    return result


def _merge_chunks(
    parts: list[str],
    chunk_size: int,
    overlap: int,
) -> list[str]:
    """작은 파트들을 chunk_size 이하로 병합하고 overlap 적용."""
    merged: list[str] = []
    current = ""

    for part in parts:
        # 현재 청크에 추가해도 크기 초과하지 않으면 병합
        if current and len(current) + len(part) > chunk_size:
            merged.append(current.strip())
            # overlap: 이전 청크의 끝부분을 다음 청크 시작에 포함
            if overlap > 0 and len(current) > overlap:
                current = current[-overlap:] + part
            else:
                current = part
        else:
            current += part

    if current.strip():
        merged.append(current.strip())

    return merged


def recursive_chunk(
    text: str,
    chunk_size: int = 400,
    overlap: int = 80,
) -> list[str]:
    """재귀 분할 — 구분자 우선순위에 따라 텍스트를 chunk_size 이하로 분할.

    Args:
        text: 분할할 텍스트
        chunk_size: 청크 최대 길이 (글자 수)
        overlap: 청크 간 겹침 길이

    Returns:
        분할된 텍스트 조각 리스트
    """
    if not text or not text.strip():
        return []

    # 이미 chunk_size 이하면 그대로 반환
    if len(text) <= chunk_size:
        return [text.strip()]

    return _recursive_split(text, chunk_size, overlap, separator_idx=0)


def _recursive_split(
    text: str,
    chunk_size: int,
    overlap: int,
    separator_idx: int,
) -> list[str]:
    """구분자 우선순위를 따라 재귀적으로 분할."""
    # 모든 구분자를 소진하면 강제 분할
    if separator_idx >= len(_SEPARATORS):
        return _force_split(text, chunk_size, overlap)

    separator = _SEPARATORS[separator_idx]
    parts = _split_by_separator(text, separator)

    # 구분자로 분할되지 않으면 다음 구분자 시도
    if len(parts) <= 1:
        return _recursive_split(text, chunk_size, overlap, separator_idx + 1)

    # 분할된 파트들을 병합
    merged = _merge_chunks(parts, chunk_size, overlap)

    # 병합 후에도 chunk_size 초과하는 청크는 다음 구분자로 재분할
    result: list[str] = []
    for chunk in merged:
        if len(chunk) > chunk_size:
            result.extend(
                _recursive_split(chunk, chunk_size, overlap, separator_idx + 1)
            )
        else:
            result.append(chunk)

    return result


def _force_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """구분자가 없을 때 글자 수 기준으로 강제 분할."""
    result: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            result.append(chunk)
        start += chunk_size - overlap if overlap < chunk_size else chunk_size
    return result
