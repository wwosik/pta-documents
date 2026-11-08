"""Building PDFs with the layout engine and reading them back with pdfplumber and pikepdf."""

from __future__ import annotations

import io
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import pdfplumber
from PIL import Image

from pta_documents.generation.common.result import Notes
from pta_documents.generation.pdf.layout import LayoutSettings, PdfInfo, layout
from pta_documents.markdown.document import DocumentResource, MarkdownDocument
from pta_documents.markdown.parser import create_parser


def make_pdf(
    markdown: str,
    resources: Sequence[DocumentResource] = (),
    settings: LayoutSettings | None = None,
    notes: Notes | None = None,
) -> bytes:
    tokens = create_parser().parse(markdown)
    document = MarkdownDocument(markdown, tuple(resources))
    result = layout(tokens, document, settings or LayoutSettings(), notes, PdfInfo(title="Test"))
    return result.content


def png(width: int = 400, height: int = 200, rgb: tuple[int, int, int] = (0, 111, 185)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), rgb).save(buffer, "PNG")
    return buffer.getvalue()


def image(path: str, width: int = 400, height: int = 200) -> DocumentResource:
    return DocumentResource(path, "image/png", png(width, height))


@dataclass(frozen=True)
class Line:
    page: int
    """0-based."""
    top: float
    text: str
    chars: list[dict[str, Any]]

    @property
    def size(self) -> float:
        return round(float(self.chars[0]["size"]), 1)

    @property
    def font(self) -> str:
        return str(self.chars[0]["fontname"])

    @property
    def color(self) -> tuple[float, ...]:
        return tuple(round(float(c), 3) for c in self.chars[-1]["non_stroking_color"])


class Pdf:
    """A PDF read back: lines, rectangles and images per page."""

    def __init__(self, content: bytes) -> None:
        self.content = content
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            self.width = float(pdf.pages[0].width)
            self.height = float(pdf.pages[0].height)
            self.lines: list[Line] = []
            self.rects: list[list[dict[str, Any]]] = []
            self.images: list[list[dict[str, Any]]] = []
            self.page_texts: list[str] = []
            for n, page in enumerate(pdf.pages):
                for line in page.extract_text_lines(return_chars=True):
                    self.lines.append(Line(n, float(line["top"]), line["text"], line["chars"]))
                self.rects.append(list(page.rects))
                self.images.append(list(page.images))
                self.page_texts.append(page.extract_text() or "")

    @property
    def pages(self) -> int:
        return len(self.page_texts)

    def line(self, text: str) -> Line:
        """The first line containing ``text``."""
        for line in self.lines:
            if text in line.text:
                return line
        raise AssertionError(f"no line contains {text!r}: {[x.text for x in self.lines]}")

    def page_of(self, text: str) -> int:
        return self.line(text).page

    def lines_on(self, page: int) -> list[Line]:
        return [line for line in self.lines if line.page == page]


def rgb(value: str) -> tuple[float, ...]:
    """A hex colour as pdfplumber reports fill colours (0…1 per channel)."""
    return tuple(round(int(value[i : i + 2], 16) / 255, 3) for i in (0, 2, 4))


def filler(count: int, word: str = "Füllzeile") -> str:
    """``count`` one-line paragraphs."""
    return "\n\n".join(f"{word} {n}" for n in range(1, count + 1)) + "\n\n"


SPACER = "spacer.png"


def spacer(points: float) -> tuple[str, DocumentResource]:
    """An image ``points`` high (at 96 dpi) that pushes what follows down the page by exactly
    that much plus a paragraph's spacing — finer steps than paragraphs."""
    return f"![]({SPACER})\n\n", image(SPACER, 4, round(points / 0.75))
