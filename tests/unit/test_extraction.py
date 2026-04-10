"""텍스트 추출 단위 테스트."""

import pytest

from app.extraction.text_extractor import (
    MdExtractor,
    PdfExtractor,
    TxtExtractor,
    get_extractor,
)


class TestTxtExtractor:
    def test_utf8_text(self):
        content = "안녕하세요\n한글 텍스트입니다.".encode("utf-8")
        result = TxtExtractor().extract(content, "test.txt")
        assert "안녕하세요" in result
        assert "한글 텍스트입니다." in result

    def test_empty_file(self):
        result = TxtExtractor().extract(b"", "empty.txt")
        assert result == ""


class TestMdExtractor:
    def test_preserves_markdown_structure(self):
        content = "# 제목\n\n## 섹션\n\n내용입니다.".encode("utf-8")
        result = MdExtractor().extract(content, "test.md")
        assert "# 제목" in result
        assert "## 섹션" in result
        assert "내용입니다." in result


class TestGetExtractor:
    def test_txt(self):
        assert isinstance(get_extractor("file.txt"), TxtExtractor)

    def test_md(self):
        assert isinstance(get_extractor("file.md"), MdExtractor)

    def test_pdf(self):
        assert isinstance(get_extractor("file.pdf"), PdfExtractor)

    def test_unsupported(self):
        with pytest.raises(ValueError, match="지원하지 않는 파일 형식"):
            get_extractor("file.docx")

    def test_no_extension(self):
        with pytest.raises(ValueError, match="지원하지 않는 파일 형식"):
            get_extractor("noext")

    def test_case_insensitive(self):
        assert isinstance(get_extractor("FILE.TXT"), TxtExtractor)
        assert isinstance(get_extractor("Doc.PDF"), PdfExtractor)
