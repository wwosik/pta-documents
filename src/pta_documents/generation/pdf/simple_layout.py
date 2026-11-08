"""An interim layout until the layout engine of E05-S02: the text of the document, plainly.

Every block becomes left-aligned lines of plain text — headings bold, code in the mono face,
list items with a dash, table rows as cells side by side — greedily wrapped at spaces on A4 in
the orientation of the template. No numbering, no styles from the Word template, no images, no
links, no bookmarks, no page-break rules: all of that is E05-S02, which replaces this module as
``generator.BODY_LAYOUT``.

Characters the face lacks become ``?`` (white space a plain space), since PDF/A forbids
``.notdef``; the generator notes them (``character-missing``). E05-S04 replaces this with
``replace_unsupported``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Final

from markdown_it.token import Token

from pta_documents.design.fonts import FontFace
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common.style_rules import heading_text, inline_text
from pta_documents.generation.pdf.body import BodySource
from pta_documents.generation.pdf.fonts import FontMetrics
from pta_documents.generation.pdf.page_model import (
    POINTS_PER_CM,
    LaidOutPage,
    Layout,
    PageGeometry,
    PageItem,
    TextItem,
)

FORMAT: Final = DocumentFormat.PDF
BODY_SIZE: Final = 10.0
CODE_SIZE: Final = 9.0
HEADING_SIZES: Final = (16.0, 13.0, 11.0)
"""``#``, ``##``, ``###`` and deeper."""
LINE_HEIGHT: Final = 1.3
DESCENT: Final = 0.25
"""Share of the size below the baseline within a line."""
PARAGRAPH_GAP: Final = 6.0
LIST_INDENT: Final = 0.6 * POINTS_PER_CM
QUOTE_INDENT: Final = 1.25 * POINTS_PER_CM
CELL_SEPARATOR: Final = "   "
BULLET: Final = "–"
MISSING: Final = "?"

MARGINS_CM: Final = {
    "portrait": (2.2, 3.5, 2.2, 2.0),
    "landscape": (2.2, 4.2, 2.2, 2.5),
}
"""Left, top, right, bottom of the PTA Word templates (E05-S02 reads them from the template)."""


def geometry_for(source: BodySource) -> PageGeometry:
    orientation = source.options.variant.orientation
    left, top, right, bottom = (cm * POINTS_PER_CM for cm in MARGINS_CM[orientation.value])
    return PageGeometry.a4(orientation, left, top, right, bottom)


def lay_out(source: BodySource, fonts: FontMetrics) -> Layout:
    """The pages of ``source``: one empty page for an empty document."""
    writer = _Writer(geometry_for(source), fonts)
    writer.blocks(source.tokens)
    return writer.layout()


@dataclass
class _Writer:
    geometry: PageGeometry
    fonts: FontMetrics
    pages: list[list[PageItem]] = field(default_factory=lambda: [[]])
    y: float = 0.0

    def __post_init__(self) -> None:
        self.y = self.geometry.top

    def layout(self) -> Layout:
        return Layout(self.geometry, tuple(LaidOutPage(tuple(items)) for items in self.pages))

    # ------------------------------------------------------------------ blocks

    def blocks(self, tokens: Sequence[Token]) -> None:
        indent = 0.0
        prefixes: list[str] = []
        for i, token in enumerate(tokens):
            match token.type:
                case "bullet_list_open" | "ordered_list_open":
                    indent += LIST_INDENT
                case "bullet_list_close" | "ordered_list_close":
                    indent -= LIST_INDENT
                case "list_item_open":
                    prefixes.append(f"{token.info}{token.markup} " if token.info else BULLET + " ")
                case "blockquote_open":
                    indent += QUOTE_INDENT
                case "blockquote_close":
                    indent -= QUOTE_INDENT
                case "heading_open":
                    level = int(token.tag[1])
                    text, _ = heading_text(tokens[i + 1], FORMAT)
                    size = HEADING_SIZES[min(level, len(HEADING_SIZES)) - 1]
                    self.gap(PARAGRAPH_GAP)
                    self.paragraph(text, FontFace.BOLD, size, indent)
                case "inline" if i > 0 and tokens[i - 1].type == "paragraph_open":
                    lead = prefixes.pop() if prefixes else ""
                    self.paragraph(lead + inline_text(token), FontFace.REGULAR, BODY_SIZE, indent)
                case "fence" | "code_block":
                    for line in token.content.rstrip("\n").split("\n"):
                        self.paragraph(line, FontFace.MONO, CODE_SIZE, indent, gap=0)
                    self.gap(PARAGRAPH_GAP)
                case "tr_open":
                    self.row(tokens, i, indent)
                case _:
                    pass

    def row(self, tokens: Sequence[Token], start: int, indent: float) -> None:
        cells: list[str] = []
        i = start + 1
        while tokens[i].type != "tr_close":
            if tokens[i].type == "inline":
                cells.append(inline_text(tokens[i]))
            i += 1
        self.paragraph(CELL_SEPARATOR.join(cells), FontFace.REGULAR, BODY_SIZE, indent, gap=0)

    # ------------------------------------------------------------------ lines

    def gap(self, height: float) -> None:
        if self.y > self.geometry.top:
            self.y += height

    def paragraph(
        self, text: str, face: FontFace, size: float, indent: float, gap: float = PARAGRAPH_GAP
    ) -> None:
        height = size * LINE_HEIGHT
        bottom = self.geometry.height - self.geometry.bottom
        for line in self.wrap(self.showable(text, face), face, size, self.text_width(indent)):
            if self.y + height > bottom and self.pages[-1]:
                self.pages.append([])
                self.y = self.geometry.top
            self.y += height
            if line:
                x = self.geometry.left + indent
                self.pages[-1].append(TextItem(x, self.y - size * DESCENT, line, face, size))
        self.y += gap

    def text_width(self, indent: float) -> float:
        return max(self.geometry.text_width - indent, self.geometry.text_width / 4)

    def wrap(self, text: str, face: FontFace, size: float, width: float) -> list[str]:
        """Greedy at spaces; a word longer than the line is cut between characters."""
        lines: list[str] = []
        current = ""
        for word in text.split(" "):
            candidate = f"{current} {word}" if current else word
            if not current or self.fonts.width(candidate, face, size) <= width:
                current = candidate
            else:
                lines.append(current)
                current = word
            while len(current) > 1 and self.fonts.width(current, face, size) > width:
                cut = len(current) - 1
                while cut > 1 and self.fonts.width(current[:cut], face, size) > width:
                    cut -= 1
                lines.append(current[:cut])
                current = current[cut:]
        lines.append(current)
        return lines

    def showable(self, text: str, face: FontFace) -> str:
        """``text`` with every character the face lacks replaced."""
        return "".join(
            char
            if char == " " or self.fonts.has_glyph(char, face)
            else (" " if char.isspace() else MISSING)
            for char in text
        )
