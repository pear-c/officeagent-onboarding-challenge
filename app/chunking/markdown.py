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

    # 짧은 인접 섹션 병합 → 큰 섹션은 재귀 분할
    merged = _merge_short_sections(sections, chunk_size)

    result: list[tuple[str, str]] = []
    for section_path, section_text in merged:
        if len(section_text) <= chunk_size:
            result.append((section_path, section_text))
        else:
            # 큰 섹션은 재귀 분할로 fallback
            sub_chunks = recursive_chunk(section_text, chunk_size, overlap)
            for sub in sub_chunks:
                result.append((section_path, sub))

    return result


_MIN_CHUNK_SIZE = 100  # 이 미만인 섹션은 인접 섹션과 병합 시도


def _merge_short_sections(
    sections: list[tuple[str, str]],
    chunk_size: int,
) -> list[tuple[str, str]]:
    """짧은 인접 섹션을 병합하여 청크 크기를 적정 수준으로 유지.

    1차: 짧은 섹션을 다음 섹션에 병합 (앞→뒤)
    2차: 여전히 짧은 섹션을 이전 섹션에 병합 (뒤→앞)
    """
    if not sections:
        return []

    # 1차: 앞→뒤 병합
    forward: list[tuple[str, str]] = []
    current_path, current_text = sections[0]

    for i in range(1, len(sections)):
        next_path, next_text = sections[i]
        combined_len = len(current_text) + len(next_text) + 1

        if len(current_text) < _MIN_CHUNK_SIZE and combined_len <= chunk_size:
            current_text = current_text + "\n" + next_text
        else:
            forward.append((current_path, current_text))
            current_path, current_text = next_path, next_text

    forward.append((current_path, current_text))

    # 2차: 뒤→앞 병합 (1차에서 남은 짧은 청크를 이전 청크에 붙임)
    if len(forward) <= 1:
        return forward

    backward: list[tuple[str, str]] = [forward[-1]]

    for i in range(len(forward) - 2, -1, -1):
        prev_path, prev_text = forward[i]
        curr_path, curr_text = backward[-1]
        combined_len = len(prev_text) + len(curr_text) + 1

        if len(curr_text) < _MIN_CHUNK_SIZE and combined_len <= chunk_size:
            backward[-1] = (prev_path, prev_text + "\n" + curr_text)
        else:
            backward.append((prev_path, prev_text))

    backward.reverse()
    return backward
