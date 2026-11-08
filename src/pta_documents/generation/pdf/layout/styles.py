"""reportlab paragraph styles made from the Word styles of the PTA template (``word_styles``).

One ``ParagraphStyle`` per Word style the DOCX generator uses: size, colour, spacing, line
height ("mindestens" over the font's own line), indents. Bold, italic and capitals are not in
the reportlab style but in ``BlockStyle``: the layout engine writes them as markup, so that the
font family (``<b>``, ``<i>``) resolves the faces. Every paragraph forbids single lines at the
top or bottom of a page (``allowWidows``/``allowOrphans`` 0).

What the templates lack comes from ``design/word.py`` as in the DOCX generator: the code style
(Consolas substitute, 9 pt on light grey, single spacing), the quote indent and the note boxes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Final, cast

from reportlab.lib import colors as rl_colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle

from pta_documents.design import colors, word
from pta_documents.design.fonts import FontFace
from pta_documents.design.word_styles import (
    POINTS_PER_CM,
    LineRule,
    NumberingLevel,
    ParagraphFormat,
    WordDesign,
)
from pta_documents.generation.pdf.layout.fonts import PdfFonts

CODE_PADDING_PT: Final = 3.0
"""Room between the grey area of a code block and its text."""
FOOTNOTE_RULE_PT: Final = 144.0
"""Length of the rule above the footnotes, as Word's separator (2 inches)."""


def color(value: str | None) -> rl_colors.Color:
    """An RGB hex value as a reportlab colour; None is the Word text colour."""
    return rl_colors.HexColor("#" + (value or colors.TEXT_WORD))


@dataclass(frozen=True)
class BlockStyle:
    """A paragraph style and the character formats of the whole paragraph."""

    style: ParagraphStyle
    bold: bool = False
    italic: bool = False
    caps: bool = False
    keep_next: bool = False


class PdfStyles:
    """The styles of one document: one template variant, one font set."""

    def __init__(self, design: WordDesign, fonts: PdfFonts, justify: bool = False) -> None:
        self.design = design
        self.fonts = fonts
        self.justify = justify
        names = word.STYLES
        self.normal = self.block(names.normal)
        self.normal_bold = self.block(names.normal_bold)
        self.headings = tuple(self.block(name) for name in names.headings)
        self.sub_heading = self.block(names.sub_heading)
        self.list_bullet = self.block(names.list_bullet)
        self.list_number = self.block(names.list_number)
        self.caption = self.block(names.caption, align_left=True)
        self.footnote = self.block(names.footnote_text, align_left=True)
        hyperlink = design.character(names.hyperlink)
        self.link_color = color(hyperlink.color)
        self.link_underline = hyperlink.underline
        self.code = self._code()
        normal = design.paragraph(names.normal)
        quote_indent = normal.left_indent_pt + word.QUOTE_INDENT_CM * POINTS_PER_CM
        self.quote = self.block(
            names.normal,
            fmt=replace(normal, left_indent_pt=quote_indent),
            style_name=names.quote,
        )
        self.note = self._note(word.NOTE, names.note)
        self.note_important = self._note(word.NOTE_IMPORTANT, names.note_important)
        table = design.table
        cell = replace(
            normal,
            space_after_pt=table.space_after_pt,
            line_pt=table.line_pt,
            line_rule=table.line_rule,
            color=table.text_color,
        )
        self.cell_padding = (cell.space_before_pt, cell.space_after_pt)
        """Top and bottom padding of table cells: the spacing of their paragraphs (Normal
        before, the table style after), which reportlab does not apply inside cells."""
        cell = replace(cell, space_before_pt=0.0, space_after_pt=0.0)
        self.table_cell = self.block(
            names.normal, fmt=cell, style_name="PDF table cell", align_left=True
        )
        self.table_header = self.block(
            names.normal,
            fmt=replace(cell, color=table.header_color),
            style_name="PDF table header",
            align_left=True,
        )

    def format(self, name: str) -> ParagraphFormat:
        return self.design.paragraph(name)

    def block(
        self,
        name: str,
        fmt: ParagraphFormat | None = None,
        *,
        style_name: str | None = None,
        align_left: bool = False,
    ) -> BlockStyle:
        """The style of the Word style ``name`` (or of ``fmt``), named ``style_name``."""
        fmt = fmt or self.design.paragraph(name)
        return BlockStyle(
            self.paragraph_style(fmt, style_name or name, align_left),
            bold=fmt.bold,
            italic=fmt.italic,
            caps=fmt.caps,
            keep_next=fmt.keep_next,
        )

    def paragraph_style(self, fmt: ParagraphFormat, name: str, align_left: bool) -> ParagraphStyle:
        """The reportlab style of ``fmt``; a numbered style starts its text at its indent and
        leaves the hanging part to the number (``Marker``)."""
        return ParagraphStyle(
            name,
            fontName=self.fonts.text,
            fontSize=fmt.size_pt,
            leading=fmt.leading(self.fonts.line_height()),
            textColor=color(fmt.color),
            spaceBefore=fmt.space_before_pt,
            spaceAfter=fmt.space_after_pt,
            leftIndent=fmt.left_indent_pt,
            firstLineIndent=0 if fmt.numbering is not None else -fmt.hanging_pt,
            alignment=TA_JUSTIFY if self.justify and not align_left else TA_LEFT,
            allowWidows=0,
            allowOrphans=0,
            splitLongWords=1,
        )

    def level(self, list_style: BlockStyle, depth: int) -> NumberingLevel | None:
        """The numbering level ``depth`` (0–2) of a list style."""
        fmt = self.design.paragraph(list_style.style.name)
        return self.design.level(fmt, min(depth, 2))

    def list_style(self, list_style: BlockStyle, depth: int) -> ParagraphStyle:
        """The style of a list paragraph at ``depth``: indented as its numbering level."""
        level = self.level(list_style, depth)
        left = level.left_pt if level is not None else list_style.style.leftIndent
        return ParagraphStyle(f"{list_style.style.name} {depth}", list_style.style, leftIndent=left)

    def indented(self, base: BlockStyle, left_pt: float) -> BlockStyle:
        """``base`` indented to ``left_pt`` (continuation paragraphs of list items)."""
        style = ParagraphStyle(f"{base.style.name} {left_pt:.1f}", base.style, leftIndent=left_pt)
        return replace(base, style=style)

    def _code(self) -> BlockStyle:
        normal = self.design.paragraph(word.STYLES.normal)
        fmt = replace(
            normal,
            name=word.STYLES.code,
            size_pt=word.CODE.size_pt,
            line_pt=12.0,
            line_rule=LineRule.AUTO,
        )
        style = ParagraphStyle(
            fmt.name,
            fontName=self.fonts.mono,
            fontSize=fmt.size_pt,
            leading=fmt.leading(self.fonts.line_height(FontFace.MONO)),
            textColor=color(fmt.color),
            spaceBefore=fmt.space_before_pt + CODE_PADDING_PT,
            spaceAfter=fmt.space_after_pt + CODE_PADDING_PT,
            leftIndent=CODE_PADDING_PT,
            rightIndent=CODE_PADDING_PT,
            backColor=color(word.CODE.background),
            borderPadding=CODE_PADDING_PT,
            alignment=TA_LEFT,
            wordWrap="CJK",
            allowWidows=0,
            allowOrphans=0,
        )
        return BlockStyle(style)

    def _note(self, design: word.NoteStyle, name: str) -> BlockStyle:
        normal = self.design.paragraph(word.STYLES.normal)
        indent = design.rule_pt + design.indent_pt
        style = ParagraphStyle(
            name,
            self.paragraph_style(normal, name, False),
            leftIndent=indent,
            rightIndent=design.indent_pt,
            backColor=color(design.background),
            borderPadding=cast(Any, (0, design.indent_pt, 0, indent)),
        )
        return BlockStyle(style)
