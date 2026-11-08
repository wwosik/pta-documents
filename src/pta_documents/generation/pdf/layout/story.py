"""Markdown tokens → reportlab flowables in the PTA Word styles (port of DocLibs
``MarkdownParser`` and ``LayoutEngine`` onto reportlab's page layout).

Every block takes the Word style the DOCX writer gives it (``generation/docx/writer.py``):
``#``–``###`` are numbered headings 1–3, deeper ones "Zwischenüberschrift" in capitals without a
number, a paragraph bold as a whole is "Standard fett", ``Tabelle: …`` after a table and an image
alone in its paragraph with a title or alt text get the captions "Tabelle n: …" and
"Abbildung n: …". The page breaking rules of DocLibs stay: headings keep the start of what
follows (``KeepWithStart``), no paragraph leaves a single line on a page, list markers go with
their first line, tables repeat their header, images never split and only shrink.
"""

from __future__ import annotations

import io
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final

from markdown_it.token import Token
from PIL import Image as PilImage
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable, KeepTogether

from pta_documents.design import colors, word, word_styles
from pta_documents.design.colors import StatusCategory
from pta_documents.design.fonts import FontFace, FontSet, bundled
from pta_documents.design.variants import (
    DEFAULT_WORD_VARIANT,
    TEXTS,
    GeneratedTexts,
    Language,
    WordVariant,
)
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import (
    block_shapes,
    code_blocks,
    code_highlight,
    generated_images,
    html,
    layout_syntax,
    layout_tokens,
)
from pta_documents.generation.common.images import (
    GENERATOR_SCALE,
    ImageConverter,
    convert_image,
    refusal_hint,
)
from pta_documents.generation.common.renderers import CodeBlockRenderer, ImageGraphic
from pta_documents.generation.common.result import NoteCodes, Notes
from pta_documents.generation.pdf.layout import flowables as fl
from pta_documents.generation.pdf.layout.fonts import PdfFonts, register
from pta_documents.generation.pdf.layout.inline import InlineOptions, InlineWriter, hex_attribute
from pta_documents.generation.pdf.layout.styles import (
    FOOTNOTE_RULE_PT,
    BlockStyle,
    PdfStyles,
    color,
)
from pta_documents.markdown.anchors import Anchors
from pta_documents.markdown.document import DocumentResource, MarkdownDocument
from pta_documents.markdown.parser import ALERT, child_lines, container, line_of

FORMAT: Final = DocumentFormat.PDF
POINTS_PER_PIXEL: Final = 0.75
"""Images are placed at 96 dpi: a pixel is three quarters of a point."""
DIRECT_IMAGES: Final = ("image/png", "image/jpeg")
PILLOW_IMAGES: Final = ("image/gif", "image/bmp", "image/tiff", "image/webp")
"""Formats Pillow reads and the engine turns into PNG."""
SCALE: Final = re.compile(r"(?:^|\s)scale\s*=\s*([0-9]*\.?[0-9]+)(?=\s|$)")
"""``![alt](bild.png "scale=0.5")``: the image at half its natural size."""
DRAWN_CONTAINERS: Final = (
    layout_syntax.TIMELINE,
    layout_syntax.GANTT,
    layout_syntax.STEPS,
    layout_syntax.RISK_MATRIX,
)
"""The containers the PDF shows as their content until it draws them (E05-S04)."""
TABLE_CELL_GAP_PT: Final = 0.3 * word_styles.POINTS_PER_CM
"""Room between columns when sizing them, as in the DOCX writer (``TABLE_CELL_GAP``)."""
MAX_ENLARGEMENT: Final = 2.0


@dataclass(frozen=True)
class LayoutSettings:
    """What the layout depends on besides the Markdown (the PDF generator fills it from
    ``PdfOptions`` and the front matter)."""

    variant: WordVariant = DEFAULT_WORD_VARIANT
    """The Word template whose styles and page the PDF takes."""
    language: Language = Language.DE
    fonts: FontSet | None = None
    """None: the bundled fonts (Selawik, Inconsolata), the same on every machine."""
    justify: bool = False
    """Justified text (``blocksatz: ja``); captions, cells and code stay left-aligned."""
    highlight: bool = True
    """Code in colour when its language is known (E17-S02)."""
    image_converters: Sequence[ImageConverter] = ()
    code_block_renderers: Sequence[CodeBlockRenderer] = ()
    line_offset: int = 0
    """Lines before the body (front matter), for the line numbers of notes and errors."""
    status_labels: Mapping[str, StatusCategory] = field(default_factory=dict[str, StatusCategory])
    """Status labels of the front matter (``FrontMatter.status_labels``, typeset like the
    text): table cells of exactly such a code span are bold in the colour of the category."""


@dataclass(frozen=True)
class LayoutContext:
    """The fonts, styles and page of one document, prepared from ``LayoutSettings``."""

    settings: LayoutSettings
    design: word_styles.WordDesign
    fonts: PdfFonts
    styles: PdfStyles
    texts: GeneratedTexts

    @property
    def page(self) -> word_styles.PageSetup:
        return self.design.page

    @property
    def frame_width(self) -> float:
        return self.page.text_width_pt

    @property
    def frame_height(self) -> float:
        return self.page.text_height_pt


def prepare(settings: LayoutSettings) -> LayoutContext:
    """Read the template's design and register the fonts."""
    design = word_styles.read(settings.variant)
    fonts = register(settings.fonts or bundled())
    styles = PdfStyles(design, fonts, settings.justify)
    return LayoutContext(settings, design, fonts, styles, TEXTS[settings.language])


@dataclass
class Story:
    """The flowables of a document and the footnote area the page template draws."""

    flowables: list[Flowable]
    footnotes: fl.FootnoteArea
    context: LayoutContext
    outline: list[fl.Outline] = field(default_factory=list[fl.Outline])
    """The bookmarks in document order."""


def build_story(
    tokens: list[Token],
    document: MarkdownDocument,
    context: LayoutContext,
    notes: Notes | None = None,
) -> Story:
    """The flowables of the body ``tokens`` (``markdown.parser`` on the body, after
    ``layout_syntax.check`` and the typography); images come from ``document.resources``."""
    builder = StoryBuilder(document, context, notes if notes is not None else Notes())
    return builder.build(tokens)


@dataclass
class _Entry:
    flowable: Flowable
    keep: bool = False
    """Stays with the start of what follows (headings, a table's title)."""


class StoryBuilder:
    def __init__(self, document: MarkdownDocument, context: LayoutContext, notes: Notes) -> None:
        self.document = document
        self.context = context
        self.settings = context.settings
        self.styles = context.styles
        self.texts = context.texts
        self.notes = notes
        self.out: list[_Entry] = []
        self.numbers = [0, 0, 0]
        self.figures = 0
        self.tables = 0
        self.container_depth = 0
        self.anchors: dict[int, str] = {}
        self.outline: list[fl.Outline] = []
        self.footnote_definitions: dict[int, list[Token]] = {}
        self.footnote_numbers: dict[int, int] = {}
        """The number of each ``footnote_ref`` (by ``id``): every reference gets the next one."""
        footnote = self.styles.footnote.style
        self.area = fl.FootnoteArea(
            gap=float(footnote.leading),
            rule_width=min(FOOTNOTE_RULE_PT, context.frame_width),
            rule_color=color(None),
        )
        self.inline_writer = InlineWriter(
            self.styles, (), notes, self.settings.line_offset, self._footnote_number
        )

    # ------------------------------------------------------------------ entry

    def build(self, tokens: list[Token]) -> Story:
        end = next((i for i, t in enumerate(tokens) if t.type == "footnote_block_open"), None)
        if end is not None:
            self._collect_footnotes(tokens[end:])
            tokens = tokens[:end]
        self._collect_anchors(tokens)
        self.inline_writer.anchors = set(self.anchors.values())
        i = 0
        while i < len(tokens):
            i = self.block(tokens, i)
        return Story(self._with_keeps(), self.area, self.context, self.outline)

    def line(self, token: Token) -> int | None:
        return line_of(token, self.settings.line_offset)

    def add(self, flowable: Flowable, keep: bool = False) -> None:
        self.out.append(_Entry(flowable, keep))

    # ------------------------------------------------------------------ blocks

    def block(self, tokens: list[Token], i: int, style: BlockStyle | None = None) -> int:
        """Lay out the block starting at ``tokens[i]``; returns the index after it."""
        token = tokens[i]
        match token.type:
            case "heading_open":
                return self.heading(tokens, i)
            case "paragraph_open":
                return self.paragraph_block(tokens, i, style)
            case "bullet_list_open" | "ordered_list_open":
                return self.list_block(tokens, i, 0, None)
            case "table_open":
                return self.table_block(tokens, i)
            case "fence" | "code_block":
                return self.fence(tokens, i)
            case "html_block":
                if not html.is_comment(token.content):
                    html.note_raw_html(self.notes, self.line(token), "the PDF")
                return i + 1
            case "blockquote_open" if ALERT in token.meta:
                kind = str(token.meta[ALERT])
                important = layout_syntax.is_important(kind, FORMAT)
                box = self.styles.note_important if important else self.styles.note
                rule = word.NOTE_IMPORTANT if important else word.NOTE
                end = _block_end(tokens, i)
                self.note_box(tokens, i + 1, end - 1, box, rule, self.texts.alert(kind))
                return end
            case "blockquote_open":
                return self.container(tokens, i, "blockquote_close", self.styles.quote)
            case "container_layout_open":
                return self.layout_container(tokens, i)
            case "hr":
                self.horizontal_rule()
                return i + 1
            case "dl_open":
                return self.definition_list(tokens, i)
            case _:
                return i + 1

    def heading(self, tokens: list[Token], i: int) -> int:
        token = tokens[i]
        level = int(token.tag[1])
        inline, _ = layout_syntax.without_attributes(tokens[i + 1], level, FORMAT)
        anchor = self.anchors.get(id(token))
        if self.container_depth:
            # A heading in a box or container: bold text without number (as in Word).
            self.paragraph(inline, self.styles.normal_bold, keep=True, anchor=anchor)
            return i + 3
        if level > 3:
            self.paragraph(inline, self.styles.sub_heading, keep=True, anchor=anchor)
            return i + 3
        self.numbers[level - 1] += 1
        for deeper in range(level, 3):
            self.numbers[deeper] = 0
        number = ".".join(str(n) for n in self.numbers[:level])
        style = self.styles.headings[level - 1]
        level_format = self.styles.design.level(self.styles.format(style.style.name))
        text = _plain_text(inline)
        outline_level = min(level - 1, (self.outline[-1].level + 1) if self.outline else 0)
        outline = fl.Outline(
            f"{number} {text}".strip(),
            outline_level,
            heading=level,
            number=number,
            text=text,
            anchor=anchor,
        )
        self.outline.append(outline)
        number_color = style.style.textColor
        if level_format is not None and level_format.color is not None:
            number_color = color(level_format.color)
        marker = fl.Marker(
            fl.MarkerKind.TEXT,
            number_color,
            x=0.0,
            text=number,
            font=self.styles.fonts.name(FontFace.BOLD if style.bold else FontFace.REGULAR),
        )
        self.paragraph(inline, style, keep=True, marker=marker, anchor=anchor, outline=outline)
        return i + 3

    def paragraph(
        self,
        inline: Token,
        style: BlockStyle,
        *,
        keep: bool = False,
        marker: fl.Marker | None = None,
        rule: fl.Rule | None = None,
        anchor: str | None = None,
        outline: fl.Outline | None = None,
        paragraph_style: ParagraphStyle | None = None,
        prefix: str = "",
        skip_checkbox: bool = False,
    ) -> fl.PtaParagraph:
        options = InlineOptions(
            bold=style.bold, italic=style.italic, caps=style.caps, skip_checkbox=skip_checkbox
        )
        markup = prefix + self.inline_writer.markup(inline, options)
        paragraph = fl.PtaParagraph(
            markup,
            paragraph_style or style.style,
            marker=marker,
            rule=rule,
            anchor=anchor,
            outline=outline,
        )
        if options.footnotes:
            self.add(fl.FootnoteAnchor(self.area, self._footnotes(options.footnotes), paragraph))
        self.add(paragraph, keep=keep)
        return paragraph

    def paragraph_block(self, tokens: list[Token], i: int, style: BlockStyle | None) -> int:
        inline = tokens[i + 1]
        children = inline.children or []
        after = tokens[i + 3] if i + 3 < len(tokens) else None
        if (
            style is None
            and block_shapes.is_table_caption(inline, self.texts)
            and self._previous_is_table()
        ):
            self.caption(self.texts.table, inline)
            return i + 3
        if style is None and (images := layout_tokens.only_images(inline)) is not None:
            self.picture_row(images, inline)
            return i + 3
        if style is None and block_shapes.only_images(children):
            lines = child_lines(inline, self.settings.line_offset)
            for image, line in zip(children, lines, strict=True):
                if image.type == "image":
                    self.figure(image, line)
            return i + 3
        if style is None and block_shapes.only_strong(children):
            keep = after is not None and after.type == "table_open"
            bold = BlockStyle(self.styles.normal_bold.style)  # bold from the markup already
            self.paragraph(inline, bold, keep=keep)
            return i + 3
        self.paragraph(inline, style or self.styles.normal)
        return i + 3

    def container(self, tokens: list[Token], i: int, close: str, style: BlockStyle | None) -> int:
        depth = 0
        j = i + 1
        while j < len(tokens):
            if tokens[j].type == tokens[i].type:
                depth += 1
            if tokens[j].type == close:
                if depth == 0:
                    return j + 1
                depth -= 1
            j = self.block(tokens, j, style) if tokens[j].type != close else j + 1
        return j

    def layout_container(self, tokens: list[Token], i: int) -> int:
        """A ``:::`` container shown plainly, as in Word (the slide-layout syntax in PDF comes
        with E05-S04): its content as ordinary blocks, speaker notes left out, timelines and
        Gantt charts as their lists with a ``code-not-drawn`` note."""
        name, _ = container(tokens[i])
        end = _block_end(tokens, i)
        if name == layout_syntax.NOTES:
            self.notes.add(
                NoteCodes.NOTES_DROPPED,
                self.line(tokens[i]),
                "Speaker notes (::: notes) are left out of the PDF; they show on the notes "
                "pages of the PowerPoint deck.",
            )
            return end
        if name in DRAWN_CONTAINERS:
            # Read and checked by layout_syntax.check; drawn in the PDF with E05-S04.
            self.notes.add(
                NoteCodes.CODE_NOT_DRAWN,
                self.line(tokens[i]),
                f"The '::: {name}' shows as its content: the PDF does not draw timelines, "
                "Gantt charts, steps and risk matrices yet (E05-S04).",
            )
        if name in (layout_syntax.CONCLUSION, layout_syntax.COMMENT):
            label = (
                self.texts.conclusion if name == layout_syntax.CONCLUSION else self.texts.comment
            )
            self.note_box(tokens, i + 1, end - 1, self.styles.note, word.NOTE, label)
            return end
        self.container_depth += 1
        j = i + 1
        while j < end - 1:
            if name == layout_syntax.COLUMNS and tokens[j].type == "hr":
                j += 1
                continue
            j = self.block(tokens, j)
        self.container_depth -= 1
        return end

    def note_box(
        self,
        tokens: list[Token],
        start: int,
        stop: int,
        box: BlockStyle,
        design: word.NoteStyle,
        label: str,
    ) -> None:
        """The blocks ``tokens[start:stop]`` on grey with a rule on the left, the first
        paragraph starting with ``label`` in bold."""
        rule = fl.Rule(color(design.rule), design.rule_pt)
        prefix = f"<b>{self.inline_writer.text(label, InlineOptions())}:</b> "
        first = True
        j = start
        while j < stop:
            token = tokens[j]
            if token.type == "paragraph_open":
                self.paragraph(tokens[j + 1], box, rule=rule, prefix=prefix if first else "")
                j += 3
            else:
                if first:
                    self._label_only(box, rule, prefix)
                j = self.block(tokens, j, box)
            first = False
        if first:
            self._label_only(box, rule, prefix)

    def _label_only(self, box: BlockStyle, rule: fl.Rule, prefix: str) -> None:
        self.add(fl.PtaParagraph(prefix, box.style, rule=rule))

    def list_block(
        self, tokens: list[Token], i: int, depth: int, list_style: BlockStyle | None
    ) -> int:
        ordered = tokens[i].type == "ordered_list_open"
        close = "ordered_list_close" if ordered else "bullet_list_close"
        if list_style is None:
            # The outermost list decides the style; nested lists go one level down (as Word).
            list_style = self.styles.list_number if ordered else self.styles.list_bullet
        level = self.styles.level(list_style, depth)
        style = self.styles.list_style(list_style, depth)
        hanging = level.hanging_pt if level is not None else 0.0
        counter = 0
        j = i + 1
        while tokens[j].type != close:
            if tokens[j].type != "list_item_open":
                j += 1
                continue
            j += 1
            counter += 1
            first = True
            while tokens[j].type != "list_item_close":
                t = tokens[j]
                if t.type == "paragraph_open":
                    inline = tokens[j + 1]
                    if first:
                        box = _checkbox(inline)
                        marker = self._marker(
                            level, counter, float(style.leftIndent) - hanging, box
                        )
                        self.paragraph(
                            inline,
                            list_style,
                            marker=marker,
                            paragraph_style=style,
                            skip_checkbox=box is not None,
                        )
                        first = False
                    else:
                        indented = self.styles.indented(self.styles.normal, float(style.leftIndent))
                        self.paragraph(inline, indented)
                    j += 3
                elif t.type in ("bullet_list_open", "ordered_list_open"):
                    j = self.list_block(tokens, j, depth + 1, list_style)
                    first = False
                else:
                    j = self.block(tokens, j)
                    first = False
            j += 1
        return j + 1

    def _marker(
        self,
        level: word_styles.NumberingLevel | None,
        counter: int,
        x: float,
        box: bool | None,
    ) -> fl.Marker:
        text_color = color(None)
        if box is not None:
            kind = fl.MarkerKind.CHECKED_BOX if box else fl.MarkerKind.BOX
            return fl.Marker(kind, text_color, x=x)
        if level is None:
            return fl.Marker(fl.MarkerKind.SQUARE, color(colors.PTA_BLUE), x=x)
        level_color = color(level.color) if level.color else text_color
        if level.format == "bullet":
            dash = level.text in ("―", "–", "—", "-")
            kind = fl.MarkerKind.DASH if dash else fl.MarkerKind.SQUARE
            return fl.Marker(kind, level_color, x=x)
        text = re.sub(r"%\d", str(counter), level.text)
        return fl.Marker(
            fl.MarkerKind.TEXT,
            level_color,
            x=x,
            text=text,
            font=self.styles.fonts.name(FontFace.REGULAR),
        )

    def definition_list(self, tokens: list[Token], i: int) -> int:
        j = i + 1
        while tokens[j].type != "dl_close":
            t = tokens[j]
            if t.type == "dt_open":
                self.paragraph(tokens[j + 1], self.styles.normal_bold, keep=True)
                j += 3
            elif t.type == "dd_open":
                j = self.container(tokens, j, "dd_close", None)
            else:
                j += 1
        return j + 1

    # ------------------------------------------------------------------ tables

    def table_block(self, tokens: list[Token], i: int) -> int:
        rows: list[list[tuple[Token, str | None]]] = []
        header_rows = 0
        j = i + 1
        while tokens[j].type != "table_close":
            t = tokens[j]
            if t.type == "tr_open":
                rows.append([])
            elif t.type in ("th_open", "td_open"):
                style = str(t.attrs.get("style", "")) if t.attrs else ""
                align = (
                    style.removeprefix("text-align:") if style.startswith("text-align:") else None
                )
                rows[-1].append((tokens[j + 1], align))
                if t.type == "th_open" and len(rows[-1]) == 1:
                    header_rows += 1
            j += 1
        columns = max(len(r) for r in rows)
        widths = self.column_widths(rows, columns, header_rows)
        table_format = self.styles.design.table
        labels = self.settings.status_labels
        cell_footnotes: list[Token] = []
        cells: list[list[Any]] = []
        commands: list[tuple[Any, ...]] = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), table_format.cell_left_pt),
            ("RIGHTPADDING", (0, 0), (-1, -1), table_format.cell_right_pt),
            ("TOPPADDING", (0, 0), (-1, -1), self.styles.cell_padding[0]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), self.styles.cell_padding[1]),
            ("LINEBELOW", (0, 0), (-1, -1), table_format.rule_pt, color(table_format.rule_color)),
        ]
        if header_rows:
            commands.append(
                ("BACKGROUND", (0, 0), (-1, header_rows - 1), color(table_format.header_fill))
            )
        for r, row in enumerate(rows):
            header = r < header_rows
            base = self.styles.table_header if header else self.styles.table_cell
            if layout_tokens.marked_row([content for content, _ in row]):
                commands.append(("BACKGROUND", (0, r), (-1, r), color(word.MARK_COLOR)))
            line: list[Any] = []
            for c in range(columns):
                if c >= len(row):
                    line.append("")
                    continue
                content, align = row[c]
                style = base.style
                if align in ("right", "center"):
                    alignment = TA_RIGHT if align == "right" else TA_CENTER
                    style = ParagraphStyle(f"{style.name} {align}", style, alignment=alignment)
                label = layout_tokens.label_cell(content)
                quarters = layout_tokens.harvey_cell(content) if not header else None
                if quarters is not None:
                    # A Harvey ball (E15-S02): a small picture, the fonts lack the characters.
                    line.append(
                        fl.HarveyBall(
                            quarters,
                            color(colors.PTA_BLUE),
                            color(colors.DARK_BLUE),
                            color(colors.WHITE),
                        )
                    )
                    commands.append(("ALIGN", (c, r), (c, r), "CENTER"))
                    commands.append(("VALIGN", (c, r), (c, r), "MIDDLE"))
                elif label is not None and label in labels:
                    status = colors.STATUS_COLORS[labels[label]]
                    text = self.inline_writer.status(label, status, InlineOptions())
                    line.append(fl.PtaParagraph(text, style))
                else:
                    options = InlineOptions(bold=base.bold, italic=base.italic)
                    markup = self.inline_writer.markup(content, options)
                    line.append(fl.PtaParagraph(markup, style))
                    cell_footnotes.extend(options.footnotes)
            cells.append(line)
        table = Table(
            cells,
            colWidths=widths,
            repeatRows=header_rows,
            splitByRow=1,
            splitInRow=1,
            hAlign="LEFT",
            style=TableStyle(commands),
        )
        normal = self.styles.normal.style
        table.spaceBefore = float(normal.spaceBefore)
        table.spaceAfter = float(normal.spaceAfter)
        if cell_footnotes:
            # Footnotes of cells go to the foot of the page the table starts on.
            self.add(fl.FootnoteAnchor(self.area, self._footnotes(cell_footnotes), table))
        self.add(table)
        return j + 1

    def column_widths(
        self, rows: list[list[tuple[Token, str | None]]], columns: int, header_rows: int
    ) -> list[float]:
        """Every column at least as wide as its longest word; the rest goes by longest text
        (the rule of ``text_metrics.column_widths``, measured with the real font)."""
        total = self.context.frame_width
        fonts = self.styles.fonts
        size = float(self.styles.table_cell.style.fontSize)

        def words(r: int, c: int) -> list[str]:
            row = rows[r]
            return _plain_text(row[c][0]).split() if c < len(row) else []

        def longest(r: int, c: int) -> float:
            face = (
                FontFace.BOLD
                if r < header_rows and self.styles.table_header.bold
                else FontFace.REGULAR
            )
            return max((fonts.width(w, face, size) for w in words(r, c)), default=0.0)

        minimums = [
            max(longest(r, c) for r in range(len(rows))) + TABLE_CELL_GAP_PT for c in range(columns)
        ]
        spare = total - sum(minimums)
        if spare < 0:
            minimums = [m * total / sum(minimums) for m in minimums]
            spare = 0.0
        weights = [
            float(
                min(
                    max(
                        max((len(_plain_text(row[c][0])) if c < len(row) else 0) for row in rows),
                        3,
                    ),
                    60,
                )
            )
            for c in range(columns)
        ]
        widths = [minimums[c] + spare * weights[c] / sum(weights) for c in range(columns)]
        widths[-1] = total - sum(widths[:-1])
        return widths

    def _previous_is_table(self) -> bool:
        return bool(self.out) and isinstance(self.out[-1].flowable, Table)

    # ------------------------------------------------------------------ figures and captions

    def caption(self, label: str, inline: Token | None, text: str | None = None) -> Flowable:
        if label == self.texts.table:
            self.tables += 1
            number = self.tables
        else:
            self.figures += 1
            number = self.figures
        style = self.styles.caption
        prefix = self.inline_writer.text(f"{label} {number}: ", InlineOptions())
        if inline is not None:
            return self.paragraph(block_shapes.strip_caption_prefix(inline), style, prefix=prefix)
        paragraph = fl.PtaParagraph(
            prefix + self.inline_writer.text(text or "", InlineOptions()), style.style
        )
        self.add(paragraph)
        return paragraph

    def figure(self, image: Token, line: int | None) -> None:
        """An image alone in its paragraph: in the Normal paragraph's spacing, with
        "Abbildung n: …" below from its title or alt text; image and caption stay together."""
        title = str(image.attrs.get("title") or "")
        scale, caption_title = _scale(title)
        scale *= generated_images.scale_of(image)  # {scale=N} (E15-S04)
        text = caption_title or image.content
        caption_height = 0.0
        if text:
            caption_style = self.styles.caption.style
            caption_height = float(caption_style.leading) + float(caption_style.spaceBefore)
        room = self.context.frame_height - self._keep_height() - caption_height
        picture = self.picture(image, line, self.context.frame_width, room, scale)
        if text:
            caption = self.caption(self.texts.figure, None, text=text)
            self.out.pop()
            self.add(KeepTogether([picture, caption]))
        else:
            self.add(picture)

    def picture_row(self, images: list[Token], inline: Token) -> None:
        """Two or more pictures side by side in equal cells, a caption under each, more than
        four on further rows."""
        per_row = word.PICTURES_PER_ROW
        columns = min(len(images), per_row)
        rows = math.ceil(len(images) / per_row)
        width = self.context.frame_width / columns
        room = width - word.PICTURE_GAP_CM * word_styles.POINTS_PER_CM
        lines = child_lines(inline, self.settings.line_offset)
        at = {id(c): line for c, line in zip(inline.children or [], lines, strict=True)}
        cells: list[list[Any]] = [["" for _ in range(columns)] for _ in range(rows)]
        for n, image in enumerate(images):
            r, c = divmod(n, per_row)
            title = str(image.attrs.get("title") or "")
            scale, caption_title = _scale(title)
            scale *= generated_images.scale_of(image)
            picture = self.picture(
                image, at.get(id(image)), room, self.context.frame_height * 0.5, scale
            )
            content: list[Flowable] = [picture]
            text = caption_title or image.content
            if text:
                content.append(self.caption(self.texts.figure, None, text=text))
                self.out.pop()
            cells[r][c] = content
        table = Table(
            cells,
            colWidths=[width] * columns,
            hAlign="LEFT",
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            ),
        )
        self.add(table)

    def picture(
        self,
        image: Token,
        line: int | None,
        max_width: float,
        max_height: float,
        scale: float,
    ) -> Flowable:
        source = str(image.attrs.get("src", ""))
        resource = self.document.find_resource(source)
        if resource is None:
            where = f" (line {line})" if line else ""
            raise DocumentConversionError(
                FORMAT, f"The image '{source}'{where} is not among the document's resources."
            )
        size: tuple[float, float] | None = None
        if generated_images.is_generated(source):
            # A QR code (``generated_images.add_generated``) is 3 cm wide, as in Word.
            edge = generated_images.SIZE_CM * word_styles.POINTS_PER_CM * scale
            size = (edge, edge)
            scale = 1.0
        return self.place(resource, source, line, max_width, max_height, scale, size_pt=size)

    def place(
        self,
        resource: DocumentResource,
        source: str,
        line: int | None,
        max_width: float,
        max_height: float,
        scale: float = 1.0,
        *,
        size_pt: tuple[float, float] | None = None,
    ) -> Flowable:
        """``resource`` at its natural size (pixels at 96 dpi, or ``size_pt``) times ``scale``,
        shrunk to ``max_width`` and to the share of the page Word gives figures, never
        enlarged."""
        where = f" (line {line})" if line else ""
        natural: tuple[float, float] | None = None
        content = resource.content
        if resource.content_type in PILLOW_IMAGES:
            content = _as_png(content)
        elif resource.content_type not in DIRECT_IMAGES:
            converters = self.settings.image_converters
            conversion = convert_image(converters, resource, GENERATOR_SCALE, FORMAT)
            if conversion is None:
                hint = refusal_hint(resource, converters)
                raise DocumentConversionError(
                    FORMAT,
                    f"The image '{source}'{where} is a {resource.content_type}; PDF takes PNG, "
                    f"JPEG, GIF, BMP, TIFF and WebP{hint}.",
                )
            content = conversion.image.content
            natural = (conversion.width, conversion.height)
        try:
            reader = ImageReader(io.BytesIO(content))
            pixels_x, pixels_y = reader.getSize()
        except Exception as error:
            raise DocumentConversionError(
                FORMAT, f"The image '{source}'{where} cannot be read: {error}"
            ) from error
        width_px, height_px = natural or (float(pixels_x), float(pixels_y))
        width = width_px * POINTS_PER_PIXEL * scale
        height = height_px * POINTS_PER_PIXEL * scale
        if size_pt is not None:
            width, height = size_pt[0] * scale, size_pt[1] * scale
        highest = min(max_height, self.context.frame_height * word.FIGURE_HEIGHT_SHARE)
        shrink = min(1.0, max_width / width, highest / height) if width and height else 1.0
        if scale * shrink > MAX_ENLARGEMENT:
            self.notes.add(
                NoteCodes.IMAGE_ENLARGED,
                line,
                f"The image '{source}' is shown at {scale * shrink:.1f} times its size and may "
                "look blurred. Use a larger image.",
            )
        normal = self.styles.normal.style
        return fl.picture(
            io.BytesIO(content),
            width * shrink,
            height * shrink,
            float(normal.spaceBefore),
            float(normal.spaceAfter),
        )

    def _keep_height(self) -> float:
        """The height of the headings right before the block being laid out, which it has to
        share a page with."""
        height = 0.0
        for entry in reversed(self.out):
            if not entry.keep:
                break
            _, h = entry.flowable.wrap(self.context.frame_width, self.context.frame_height)
            height += h + float(entry.flowable.getSpaceAfter())
        return height

    # ------------------------------------------------------------------ other blocks

    def fence(self, tokens: list[Token], i: int) -> int:
        token = tokens[i]
        if token.type == "fence" and token.info.strip():
            graphic = code_blocks.render_graphic(
                self.settings.code_block_renderers,
                self.notes,
                token.info,
                token.content,
                self.line(token),
                FORMAT,
                self.settings.language,
            )
            if isinstance(graphic, ImageGraphic):
                room = self.context.frame_height - self._keep_height()
                picture = self.place(
                    graphic.image,
                    graphic.image.path,
                    self.line(token),
                    self.context.frame_width,
                    room,
                )
                self.add(picture)
                return i + 1
            if graphic is not None:
                code_blocks.note_not_drawn(
                    self.notes,
                    token.info,
                    self.line(token),
                    "the PDF does not draw charts and drawings yet (E05-S04).",
                )
        self.code_block(token)
        return i + 1

    def code_block(self, token: Token) -> None:
        """Code in the code font on grey, line by line; with a known language in the PTA
        colours (E17-S02). Long lines break at any character."""
        lines = token.content.rstrip("\n").split("\n")
        info = token.info.strip() if token.type == "fence" else ""
        spans = code_highlight.highlight_fence(
            info, lines, self.line(token), self.notes, self.settings.highlight
        )
        options = InlineOptions()
        written: list[str] = []
        for n, text in enumerate(lines):
            if spans is None:
                written.append(_code_text(self.inline_writer.text(text, options, code=True)))
                continue
            parts: list[str] = []
            for span in spans[n]:
                piece = _code_text(self.inline_writer.text(span.text, options, code=True))
                look = span.look
                if look.bold:
                    piece = f"<b>{piece}</b>"
                if look.italic:
                    piece = f"<i>{piece}</i>"
                if look.color is not None:
                    piece = f"<font color={hex_attribute(look.color)}>{piece}</font>"
                parts.append(piece)
            written.append("".join(parts))
        self.add(fl.PtaParagraph("<br/>".join(written) or "\u00a0", self.styles.code.style))

    def horizontal_rule(self) -> None:
        """``---``: as Word's empty paragraph with a rule below, in ``GREY_MID``."""
        normal = self.styles.normal.style
        self.add(
            HRFlowable(
                width="100%",
                thickness=0.5,
                color=color(word.HORIZONTAL_RULE_COLOR),
                spaceBefore=float(normal.spaceBefore) + float(normal.leading),
                spaceAfter=float(normal.spaceAfter),
            )
        )

    # ------------------------------------------------------------------ keeps

    def _with_keeps(self) -> list[Flowable]:
        """The flowables with a ``KeepWithStart`` before every run of headings."""
        result: list[Flowable] = []
        n = 0
        entries = self.out
        while n < len(entries):
            if not entries[n].keep:
                result.append(entries[n].flowable)
                n += 1
                continue
            run_end = n
            while run_end < len(entries) and entries[run_end].keep:
                run_end += 1
            keep = [e.flowable for e in entries[n:run_end]]
            following = entries[run_end].flowable if run_end < len(entries) else None
            result.append(fl.KeepWithStart(keep, following))
            result.extend(keep)
            n = run_end
        return result

    # ------------------------------------------------------------------ anchors and footnotes

    def _collect_anchors(self, tokens: list[Token]) -> None:
        anchors = Anchors()
        for i, token in enumerate(tokens):
            if token.type == "heading_open" and i + 1 < len(tokens):
                level = int(token.tag[1])
                inline, _ = layout_syntax.without_attributes(tokens[i + 1], level, FORMAT)
                self.anchors[id(token)] = anchors.add(_plain_text(inline))

    def _collect_footnotes(self, tokens: list[Token]) -> None:
        current: int | None = None
        for token in tokens:
            if token.type == "footnote_open":
                current = int(token.meta["id"])
                self.footnote_definitions[current] = []
            elif token.type == "footnote_close":
                current = None
            elif current is not None:
                self.footnote_definitions[current].append(token)

    def _footnote_number(self, reference: Token) -> int:
        number = self.footnote_numbers.get(id(reference))
        if number is None:
            number = len(self.footnote_numbers) + 1
            self.footnote_numbers[id(reference)] = number
        return number

    def _footnotes(self, references: list[Token]) -> list[Flowable]:
        """The footnote paragraphs of ``references`` ("n text" in "footnote text")."""
        result: list[Flowable] = []
        style = self.styles.footnote
        for reference in references:
            number = self._footnote_number(reference)
            definition = self.footnote_definitions.get(int(reference.meta["id"]), [])
            paragraphs = [t for t in definition if t.type == "inline"] or [None]
            for n, inline in enumerate(paragraphs):
                prefix = f"<super>{number}</super> " if n == 0 else ""
                options = InlineOptions()
                text = self.inline_writer.markup(inline, options) if inline is not None else ""
                result.append(fl.PtaParagraph(prefix + text, style.style))
        return result


def _block_end(tokens: list[Token], i: int) -> int:
    """The index after the block that opens at ``tokens[i]``."""
    if tokens[i].nesting != 1:
        return i + 1
    j = i + 1
    while not (tokens[j].nesting == -1 and tokens[j].level == tokens[i].level):
        j += 1
    return j + 1


def _plain_text(inline: Token) -> str:
    """The text of an inline token without formatting (bookmarks, anchors, column widths)."""
    parts: list[str] = []
    for child in inline.children or []:
        if child.type in ("text", "code_inline"):
            parts.append(child.content)
        elif child.type in ("softbreak", "hardbreak"):
            parts.append(" ")
        elif child.type == "image":
            parts.append(child.content)
    return "".join(parts).strip()


def _checkbox(inline: Token) -> bool | None:
    """Whether a list item starts with a task-list checkbox: True if ticked, None if none."""
    for child in inline.children or []:
        if child.type == "html_inline" and html.is_checkbox(child.content):
            return "checked" in child.content
        if child.type == "text" and not child.content.strip():
            continue
        return None
    return None


def _scale(title: str) -> tuple[float, str]:
    """The ``scale=…`` in an image title and the rest of the title."""
    match = SCALE.search(title)
    if match is None:
        return 1.0, title.strip()
    value = float(match.group(1))
    rest = (title[: match.start()] + title[match.end() :]).strip()
    return (value if value > 0 else 1.0), rest


def _code_text(escaped: str) -> str:
    """Code keeps its spaces: each one a no-break space (the line still breaks anywhere)."""
    return escaped.replace(" ", "\u00a0") or ""


def _as_png(content: bytes) -> bytes:
    with PilImage.open(io.BytesIO(content)) as picture:
        buffer = io.BytesIO()
        picture.save(buffer, "PNG")
        return buffer.getvalue()
