"""The slides a deck is made of, between parsing the Markdown and writing the PPTX."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Final

from pta_documents.generation.common.text_metrics import TextRun
from pta_documents.markdown.document import DocumentResource


@dataclass(frozen=True)
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    strike: bool = False
    code: bool = False
    link: str | None = None
    is_break: bool = False

    def metric(self) -> TextRun:
        if self.is_break:
            return TextRun(is_break=True)
        return TextRun(self.text, self.bold)


BREAK = Run("", is_break=True)


class Kind(Enum):
    SUBHEADLINE = "subheadline"
    """Text level 1 of the PTA body: ``###`` and deeper headings."""
    INTRO = "intro"
    """Text level 2: ordinary paragraphs."""
    BULLET = "bullet"
    """Text levels 3-5: bullet list items by depth."""
    NUMBERED = "numbered"
    """Text levels 3-5 with automatic numbers."""


@dataclass(frozen=True)
class Paragraph:
    runs: tuple[Run, ...]
    kind: Kind = Kind.INTRO
    depth: int = 0
    """Nesting depth of list items (0-2)."""
    start: int = 1
    """The first number of a numbered list."""

    @property
    def level(self) -> int:
        """Zero-based paragraph level of the PTA body placeholder (``a:pPr/@lvl``)."""
        if self.kind is Kind.SUBHEADLINE:
            return 0
        if self.kind is Kind.INTRO:
            return 1
        return 2 + min(self.depth, 2)

    @property
    def is_bold_only(self) -> bool:
        texts = [r for r in self.runs if not r.is_break and r.text.strip()]
        return bool(texts) and all(r.bold for r in texts)


class Align(Enum):
    DEFAULT = "default"
    LEFT = "l"
    CENTER = "ctr"
    RIGHT = "r"


@dataclass(frozen=True)
class Table:
    rows: tuple[tuple[tuple[Run, ...], ...], ...]
    alignments: tuple[Align, ...]
    has_header: bool
    title: tuple[Run, ...] | None = None

    def subset(self, body_rows: list[int], keep_title: bool) -> Table:
        chosen = ([0] if self.has_header else []) + body_rows
        return Table(
            tuple(self.rows[r] for r in chosen),
            self.alignments,
            self.has_header,
            self.title if keep_title else None,
        )


PICTURE_TYPES: Final = ("image/png", "image/jpeg", "image/gif", "image/bmp", "image/tiff")
"""The image formats slides take; the parser converts others (image converters) or refuses them."""


@dataclass(frozen=True)
class Image:
    resource: DocumentResource
    alt: str
    line: int | None = None
    """The line of the image in the Markdown, for notes about it."""


@dataclass(frozen=True)
class Images:
    images: tuple[Image, ...]


@dataclass(frozen=True)
class Code:
    lines: tuple[str, ...]


Visual = Table | Images | Code


@dataclass(frozen=True)
class Separator:
    """A ``---`` line: splits the content of a slide with a named layout."""


Item = Paragraph | Table | Images | Code | Separator


@dataclass(frozen=True)
class Slide:
    title: tuple[Run, ...]
    line: int | None = None


@dataclass(frozen=True)
class TitleSlide(Slide):
    subtitle: tuple[Paragraph, ...] = ()
    layout: str | None = None


@dataclass(frozen=True)
class ChapterSlide(Slide):
    number: int = 1
    layout: str | None = None


@dataclass(frozen=True)
class ClosingSlide(Slide):
    layout: str | None = None


@dataclass(frozen=True)
class ContentSlide(Slide):
    body: tuple[Paragraph, ...] = ()


@dataclass(frozen=True)
class VisualSlide(Slide):
    above: tuple[Paragraph, ...] = ()
    visual: Visual | None = None
    below: tuple[Paragraph, ...] = ()


@dataclass(frozen=True)
class LayoutSlide(Slide):
    """A ``##`` slide on a layout named in its heading; content split at ``---``."""

    layout: str = ""
    segments: tuple[tuple[Item, ...], ...] = field(default_factory=tuple)


def plain_text(runs: tuple[Run, ...]) -> str:
    return "".join(" " if r.is_break else r.text for r in runs).strip()
