"""텍스트 추출 — 파일 포맷별 추출기 + 팩토리."""

import io
import logging
import re
from abc import ABC, abstractmethod

from pypdf import PdfReader

_NUMBERED_HEADER = re.compile(r"(?:^|\n)(\d+(?:\.\d+)*\.?\s+[가-힣\uAC00-\uD7AF].{2,30}?)(?=\n|$|\d+\.\d+)", re.MULTILINE)

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


class TextExtractor(ABC):
    """텍스트 추출기 인터페이스."""

    @abstractmethod
    def extract(self, content: bytes, filename: str) -> str:
        """파일 바이너리 → 텍스트 변환."""


class TxtExtractor(TextExtractor):
    """일반 텍스트 파일 추출기."""

    def extract(self, content: bytes, filename: str) -> str:
        return content.decode("utf-8")


class MdExtractor(TextExtractor):
    """마크다운 파일 추출기 (원본 마크다운 구조 보존)."""

    def extract(self, content: bytes, filename: str) -> str:
        return content.decode("utf-8")


class PdfExtractor(TextExtractor):
    """PDF 파일 추출기 (pypdf + 경량 마크다운 변환)."""

    def extract(self, content: bytes, filename: str) -> str:
        reader = PdfReader(io.BytesIO(content))
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pages.append(text)
            else:
                logger.warning("PDF 페이지 %d 텍스트 추출 실패: %s", i + 1, filename)
        raw_text = "\n\n".join(pages)
        return self._to_markdown(raw_text)

    @staticmethod
    def _to_markdown(text: str) -> str:
        """번호 헤더(N. / N.N. 한글제목)만 마크다운 ## 으로 변환."""
        return _NUMBERED_HEADER.sub(r"\n## \1\n", text)


_EXTRACTOR_MAP: dict[str, type[TextExtractor]] = {
    ".txt": TxtExtractor,
    ".md": MdExtractor,
    ".pdf": PdfExtractor,
}


def get_extractor(filename: str) -> TextExtractor:
    """파일 확장자로 추출기 선택."""
    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    cls = _EXTRACTOR_MAP.get(ext)
    if cls is None:
        raise ValueError(f"지원하지 않는 파일 형식: {ext} (허용: {SUPPORTED_EXTENSIONS})")
    return cls()
