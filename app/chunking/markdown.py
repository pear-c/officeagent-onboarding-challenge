"""청킹 — 마크다운 인식 (헤더 기반 섹션 분할 → 재귀 fallback)."""

import re

from app.chunking.recursive import recursive_chunk

# 마크다운 헤더 패턴 (# ~ ###### 모두 매칭 — 계층 경로 구성에 h1도 필요)
_HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def _parse_sections(text: str) -> list[tuple[str, str]]:
    """마크다운 텍스트를 (섹션 경로, 텍스트) 튜플 리스트로 분할.

    헤더 계층을 추적하여 "상위 헤더 > 하위 헤더" 형태의 경로를 생성.
    """
    sections: list[tuple[str, str]] = []
    header_stack: list[tuple[int, str]] = []  # (level, title)
    current_text_parts: list[str] = []
    current_section_path = ""

    for line in text.split("\n"):
        match = _HEADER_PATTERN.match(line)
        if match:
            # 이전 섹션 저장
            if current_text_parts:
                content = "\n".join(current_text_parts).strip()
                if content:
                    sections.append((current_section_path, content))
                current_text_parts = []

            level = len(match.group(1))
            title = match.group(2).strip()

            # 스택에서 현재 레벨 이상의 헤더 제거
            while header_stack and header_stack[-1][0] >= level:
                header_stack.pop()
            header_stack.append((level, title))

            # 섹션 경로 생성
            current_section_path = " > ".join(h[1] for h in header_stack)
        else:
            current_text_parts.append(line)

    # 마지막 섹션 저장
    if current_text_parts:
        content = "\n".join(current_text_parts).strip()
        if content:
            sections.append((current_section_path, content))

    return sections


def markdown_aware_chunk(
    text: str,
    chunk_size: int = 400,
    overlap: int = 80,
) -> list[tuple[str, str]]:
    """마크다운 인식 청킹 — 헤더 기반 섹션 분할 후, 큰 섹션은 재귀 분할.

    Args:
        text: 마크다운 텍스트
        chunk_size: 청크 최대 길이 (글자 수)
        overlap: 청크 간 겹침 길이

    Returns:
        (섹션 경로, 청크 텍스트) 튜플 리스트
    """
    if not text or not text.strip():
        return []

    sections = _parse_sections(text)

    # 헤더가 없으면 재귀 분할로 fallback
    if not sections:
        chunks = recursive_chunk(text, chunk_size, overlap)
        return [("", chunk) for chunk in chunks]

    result: list[tuple[str, str]] = []
    for section_path, section_text in sections:
        if len(section_text) <= chunk_size:
            result.append((section_path, section_text))
        else:
            # 큰 섹션은 재귀 분할로 fallback
            sub_chunks = recursive_chunk(section_text, chunk_size, overlap)
            for sub in sub_chunks:
                result.append((section_path, sub))

    return result
