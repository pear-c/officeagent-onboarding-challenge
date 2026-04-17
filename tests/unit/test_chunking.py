"""청킹 단위 테스트."""

import pytest

from app.chunking.markdown import markdown_aware_chunk
from app.chunking.recursive import Chunk, recursive_chunk
from app.chunking.router import chunk_document


class TestRecursiveChunk:
    def test_empty_string(self):
        assert recursive_chunk("") == []

    def test_whitespace_only(self):
        assert recursive_chunk("   \n\n  ") == []

    def test_short_text_no_split(self):
        text = "짧은 텍스트"
        result = recursive_chunk(text, chunk_size=400)
        assert len(result) == 1
        assert result[0] == text

    def test_paragraph_split(self):
        text = "첫 번째 문단입니다.\n\n두 번째 문단입니다."
        result = recursive_chunk(text, chunk_size=20, overlap=0)
        assert len(result) >= 2
        assert "첫 번째" in result[0]
        assert "두 번째" in result[-1]

    def test_respects_chunk_size(self):
        text = "가나다라마바사 " * 100  # ~800자
        result = recursive_chunk(text, chunk_size=100, overlap=0)
        for chunk in result:
            assert len(chunk) <= 120  # 약간의 여유 허용 (구분자 보존)

    def test_overlap_produces_more_chunks(self):
        text = "테스트 문장입니다. " * 50
        no_overlap = recursive_chunk(text, chunk_size=100, overlap=0)
        with_overlap = recursive_chunk(text, chunk_size=100, overlap=30)
        assert len(with_overlap) >= len(no_overlap)

    def test_korean_text(self):
        """한글 텍스트가 깨지지 않는지 확인."""
        text = "한글로 작성된 긴 문서입니다. " * 50
        result = recursive_chunk(text, chunk_size=100, overlap=20)
        for chunk in result:
            # 유효한 UTF-8 문자열인지 확인
            chunk.encode("utf-8").decode("utf-8")

    def test_force_split_no_separator(self):
        """구분자가 전혀 없는 긴 텍스트 → 강제 분할."""
        text = "가" * 500  # 구분자 없는 500자
        result = recursive_chunk(text, chunk_size=100, overlap=0)
        assert len(result) >= 5


class TestMarkdownAwareChunk:
    def test_empty_string(self):
        assert markdown_aware_chunk("") == []

    def test_no_headers_fallback(self):
        """헤더 없는 텍스트 → 재귀 분할 fallback."""
        text = "일반 텍스트입니다.\n\n다른 문단입니다."
        result = markdown_aware_chunk(text, chunk_size=400)
        assert len(result) >= 1
        assert all(section == "" for section, _ in result)

    def test_header_sections(self):
        text = "# 제목\n\n소개 내용.\n\n## 섹션 A\n\n내용 A.\n\n## 섹션 B\n\n내용 B."
        result = markdown_aware_chunk(text, chunk_size=400)
        sections = [s for s, _ in result]
        assert any("섹션 A" in s for s in sections)
        assert any("섹션 B" in s for s in sections)

    def test_nested_headers(self):
        text = "# 상위\n\n## 중간\n\n### 하위\n\n내용."
        result = markdown_aware_chunk(text, chunk_size=400)
        sections = [s for s, _ in result]
        # 경로가 "상위 > 중간 > 하위" 형태인지
        assert any("상위" in s and "중간" in s and "하위" in s for s in sections)

    def test_large_section_recursive_fallback(self):
        """큰 섹션은 재귀 분할로 fallback."""
        text = "## 섹션\n\n" + ("내용입니다. " * 100)
        result = markdown_aware_chunk(text, chunk_size=100, overlap=20)
        assert len(result) > 1
        # 모든 청크가 같은 섹션 경로를 가져야 함
        assert all(s == "섹션" for s, _ in result)


class TestChunkDocument:
    def test_txt_file(self):
        text = "문단 1.\n\n문단 2.\n\n문단 3."
        result = chunk_document(text, "test.txt", chunk_size=400)
        assert all(isinstance(c, Chunk) for c in result)
        assert all(c.source_file == "test.txt" for c in result)
        assert all(c.section == "" for c in result)

    def test_md_file(self):
        text = "# 제목\n\n## 섹션\n\n내용."
        result = chunk_document(text, "guide.md", chunk_size=400)
        assert all(isinstance(c, Chunk) for c in result)
        assert all(c.source_file == "guide.md" for c in result)
        assert any(c.section != "" for c in result)

    def test_pdf_uses_recursive(self):
        text = "PDF에서 추출된 텍스트입니다.\n\n다음 페이지 내용."
        result = chunk_document(text, "doc.pdf", chunk_size=400)
        assert all(isinstance(c, Chunk) for c in result)
        assert all(c.section == "" for c in result)

    def test_chunk_ids_sequential(self):
        text = "문장 1.\n\n문장 2.\n\n문장 3.\n\n문장 4.\n\n문장 5."
        result = chunk_document(text, "test.txt", chunk_size=20, overlap=0)
        ids = [c.chunk_id for c in result]
        assert ids == list(range(len(result)))

    def test_chunk_immutable(self):
        text = "테스트 텍스트입니다."
        result = chunk_document(text, "test.txt")
        with pytest.raises(AttributeError):
            result[0].text = "수정 시도"  # frozen=True
