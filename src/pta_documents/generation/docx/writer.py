"""Writes the Markdown body into the document, block by block, in the PTA styles.

Every block goes into a style of the PTA template (see ``design/word.py``); direct formatting
is only used for character formats (bold, italic, strikethrough, inline code, links), list
numbering, alignment, indents and the shading of a highlighted table row.

Slide-layout Markdown is shown plainly (E03-S03): containers as ordinary blocks, alerts and boxes
in the styles ``Hinweis``/``Hinweis wichtig``, ``==mark==`` and coloured words in character
styles, image rows as a table without rules, the PTA slide kinds as headings, quotes and lists.
"""

from __future__ import annotations

import io
import math
import re
from dataclasses import dataclass, field
from typing import Any, Final, cast

from docx.document import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.image.exceptions import UnrecognizedImageError
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.packuri import PackURI
from docx.opc.part import Part
from docx.shared import Cm, Emu, Pt, RGBColor
from docx.styles.style import ParagraphStyle
from docx.table import Table
from docx.text.paragraph import Paragraph
from lxml import etree
from markdown_it.token import Token
from PIL import Image

from pta_documents.design import colors, word
from pta_documents.design.colors import STATUS_COLORS, StatusCategory
from pta_documents.design.variants import GeneratedTexts
from pta_documents.drawing import schedule as schedule_drawing
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import (
    block_shapes,
    code_blocks,
    code_highlight,
    generated_images,
    heading_attributes,
    html,
    layout_syntax,
    layout_tokens,
    schedule,
    svg_blip,
    text_metrics,
)
from pta_documents.generation.common.images import GENERATOR_SCALE, convert_image, refusal_hint
from pta_documents.generation.common.openxml import R, field_paragraph_runs, w
from pta_documents.generation.common.renderers import (
    ChartGraphic,
    CodeBlockGraphic,
    DrawingGraphic,
    ImageGraphic,
)
from pta_documents.generation.common.result import NoteCodes, Notes
from pta_documents.generation.common.text_metrics import TextRun
from pta_documents.generation.docx import chart as docx_chart
from pta_documents.generation.docx import drawings as docx_drawings
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.markdown.document import DocumentResource, MarkdownDocument
from pta_documents.markdown.front_matter import FrontMatter
from pta_documents.markdown.parser import (
    ALERT,
    child_lines,
    container,
    create_parser,
    line_of,
)
from pta_documents.markdown.typography import typeset, typeset_text

FORMAT: Final = DocumentFormat.DOCX
EMU_PER_TWIP: Final = 635
EMU_PER_INCH: Final = 914400
LIST_INDENT_CM: Final = (0.6, 1.2, 1.8)
"""Text indents of the three list levels of the PTA numbering (for continuation paragraphs)."""
TABLE_FONT_PT: Final = 10.0
TABLE_CELL_GAP: Final = Cm(0.3)
"""Room between columns when sizing them; the PTA table style has no cell margins."""
EMU_PER_PIXEL: Final = 9525
"""A pixel at 96 dpi: the natural size an image is compared with for ``image-enlarged``."""
MAX_ENLARGEMENT: Final = 2.0
WHAT: Final = "the document"
ABSOLUTE_URI: Final = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
SUPPORTED_IMAGES: Final = ("image/png", "image/jpeg", "image/gif", "image/bmp", "image/tiff")
FOOTNOTES_RT: Final = RT.FOOTNOTES
XML_SPACE: Final = "{http://www.w3.org/XML/1998/namespace}space"
PTA_NAMESPACE: Final = "urn:pta-documents:wordprocessingml"
"""Our own markup in the document, ignorable for Word (``mc:Ignorable``): the language of a code
block, so that the converter writes its fence again (decision 2026-11-07)."""
PTA_PREFIX: Final = "pta"
CODE_LANGUAGE: Final = f"{{{PTA_NAMESPACE}}}codeLanguage"
"""``<pta:codeLanguage pta:val="python"/>`` in the ``w:pPr`` of a code block."""
CODE_LANGUAGE_VALUE: Final = f"{{{PTA_NAMESPACE}}}val"
MC_IGNORABLE: Final = "{http://schemas.openxmlformats.org/markup-compatibility/2006}Ignorable"


@dataclass
class _Format:
    bold: bool = False
    italic: bool = False
    strike: bool = False
    mark: bool = False
    status: StatusCategory | None = None


@dataclass
class _Inline:
    """Where inline content goes and how runs look there."""

    target: etree._Element
    part: Part
    paragraph: Paragraph | None
    format: _Format = field(default_factory=_Format)
    plain_bold: bool = False
    """The paragraph style is bold already: do not set bold directly."""
    images: bool = True
    line_breaks: bool = False
    """Soft line breaks are line breaks (contact lines), not spaces."""
    photo_width: int | None = None
    """The width pictures are shown at, at most (contact photos); None: the text width."""


class BodyWriter:
    def __init__(
        self,
        document: Document,
        source: MarkdownDocument,
        front: FrontMatter,
        options: DocxOptions,
        texts: GeneratedTexts,
        notes: Notes | None = None,
    ) -> None:
        self.document = document
        self.notes = notes if notes is not None else Notes()
        self.source = source
        self.front = front
        self.options = options
        self.texts = texts
        self.figures = 0
        self.tables = 0
        self.drawings = 0
        """Drawings of the code-block renderers so far, for the names of their SVGs."""
        self.footnote_definitions: dict[int, list[Token]] = {}
        self.footnotes_part: Part | None = None
        self.footnotes_root: etree._Element | None = None
        self.next_footnote_id = 1
        self.style_ids: dict[str, str] = {}
        self.labels = front.status_labels()
        if options.typography:
            # Label cells are typeset like any text, so the labels must be too.
            self.labels = {typeset_text(k, options.language): v for k, v in self.labels.items()}
        self.container_depth = 0
        """How deep the writer is in ``:::`` containers: headings there are no headings."""
        self.kind: str | None = None
        """The PTA slide kind of the ``##`` section being written (E04-S04)."""
        section = document.sections[0]
        page_width = int(section.page_width or 0)
        margins = int(section.left_margin or 0) + int(section.right_margin or 0)
        page_height = int(section.page_height or 0)
        vertical = int(section.top_margin or 0) + int(section.bottom_margin or 0)
        self.text_width = page_width - margins
        self.text_height = page_height - vertical
        self.today = schedule.reference_day(options.date)
        """What ``heute`` in a timeline or Gantt chart is (E15-S01)."""

    # ------------------------------------------------------------------ entry

    def write(self) -> None:
        env: dict[str, object] = {}
        tokens = create_parser().parse(self.front.body, env)
        layout_syntax.check(tokens, FORMAT, self.front.body_line, self.today)
        self.source = generated_images.add_generated(
            self.source, tokens, FORMAT, self.front.body_line
        )
        if self.options.typography:
            typeset(tokens, self.options.language)
        end = next((i for i, t in enumerate(tokens) if t.type == "footnote_block_open"), None)
        if end is not None:
            self._collect_footnotes(tokens[end:])
            tokens = tokens[:end]
        i = 0
        while i < len(tokens):
            i = self.block(tokens, i)
        self._save_footnotes()

    # ------------------------------------------------------------------ blocks

    def block(self, tokens: list[Token], i: int, style: str | None = None) -> int:
        """Write the block starting at ``tokens[i]``; returns the index after it."""
        token = tokens[i]
        match token.type:
            case "heading_open":
                level = int(token.tag[1])
                # Heading attributes are checked, but have no effect in Word, but for the kinds.
                inline, attributes = layout_syntax.without_attributes(tokens[i + 1], level, FORMAT)
                if self.container_depth or (self.kind == heading_attributes.CONTACT and level > 2):
                    # A card or a person: no number and no entry in the table of contents.
                    paragraph = self.paragraph(word.STYLES.normal_bold)
                    paragraph.paragraph_format.keep_with_next = True
                    self.inline(paragraph, inline, plain_bold=True)
                    return i + 3
                if attributes is not None and attributes.kind is not None and token.level == 0:
                    return self.slide_kind(tokens, i, inline, attributes.kind)
                styles = word.STYLES
                heading = styles.headings[level - 1] if level <= 3 else styles.sub_heading
                paragraph = self.paragraph(heading)
                self.inline(paragraph, inline)
                return i + 3
            case "paragraph_open":
                return self.paragraph_block(tokens, i, style)
            case "bullet_list_open" | "ordered_list_open":
                return self.list_block(tokens, i, depth=0, list_style=None, num_id=None)
            case "table_open":
                return self.table_block(tokens, i)
            case "fence" | "code_block":
                graphic = self.draw(token) if token.type == "fence" else None
                if graphic is None:
                    self.code_block(token)
                    return i + 1
                caption, after = self._figure_caption(tokens, i + 1, token.level)
                self.graphic_figure(graphic, token, caption)
                return after
            case "html_block":
                if not html.is_comment(token.content):
                    html.note_raw_html(self.notes, self.line(token), WHAT)
                return i + 1
            case "blockquote_open" if ALERT in token.meta:
                kind = str(token.meta[ALERT])
                important = layout_syntax.is_important(kind, FORMAT)
                style = word.STYLES.note_important if important else word.STYLES.note
                end = _block_end(tokens, i)
                self.note_box(tokens, i + 1, end - 1, style, self.texts.alert(kind))
                return end
            case "blockquote_open":
                return self.container(tokens, i, "blockquote_close", word.STYLES.quote)
            case "container_layout_open":
                return self.layout_container(tokens, i)
            case "hr":
                self.horizontal_rule()
                return i + 1
            case "dl_open":
                return self.definition_list(tokens, i)
            case _:
                return i + 1

    def line(self, token: Token) -> int | None:
        return line_of(token, self.front.body_line)

    def draw(self, fence: Token) -> CodeBlockGraphic | None:
        """The graphic the code-block renderers make of ``fence``; None: it stays code."""
        return code_blocks.render_graphic(
            self.options.code_block_renderers,
            self.notes,
            fence.info,
            fence.content,
            self.line(fence),
            FORMAT,
            self.options.language,
        )

    def _figure_caption(self, tokens: list[Token], i: int, level: int) -> tuple[Token | None, int]:
        """The inline of an ``Abbildung: …`` paragraph at ``tokens[i]`` (directly after a
        graphic, at its level) and the index after it; else None and ``i``."""
        if (
            i + 2 < len(tokens)
            and tokens[i].type == "paragraph_open"
            and tokens[i].level == level
            and self._is_figure_caption(tokens[i + 1])
        ):
            return tokens[i + 1], i + 3
        return None, i

    def _is_figure_caption(self, inline: Token) -> bool:
        return block_shapes.is_figure_caption(inline, self.texts)

    def container(self, tokens: list[Token], i: int, close: str, style: str | None) -> int:
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
        """A ``:::`` container: its content as ordinary blocks, one after the other."""
        name, _ = container(tokens[i])
        end = _block_end(tokens, i)
        if name == layout_syntax.NOTES:
            self.notes.add(
                NoteCodes.NOTES_DROPPED,
                self.line(tokens[i]),
                "Speaker notes (::: notes) are left out of the Word document; they show on the "
                "notes pages of the PowerPoint deck.",
            )
            return end
        if name == layout_syntax.TIMELINE:
            offset = self.front.body_line
            self.timeline(schedule.read_timeline(tokens, i, FORMAT, offset, self.today), tokens[i])
            return end
        if name == layout_syntax.GANTT:
            language = self.options.language
            offset = self.front.body_line
            self.gantt(schedule.read_gantt(tokens, i, FORMAT, offset, self.today, language))
            return end
        if name in (layout_syntax.CONCLUSION, layout_syntax.COMMENT):
            conclusion = name == layout_syntax.CONCLUSION
            label = self.texts.conclusion if conclusion else self.texts.comment
            self.note_box(tokens, i + 1, end - 1, word.STYLES.note, label)
            return end
        self.container_depth += 1
        j = i + 1
        first = True
        while j < end - 1:
            token = tokens[j]
            if name == layout_syntax.COLUMNS and token.type == "hr":
                j += 1  # the line between two columns
                continue
            if name == layout_syntax.STATEMENT and first and token.type == "paragraph_open":
                paragraph = self.paragraph(word.STYLES.normal_bold)
                self.inline(paragraph, tokens[j + 1], plain_bold=True)
                j += 3
            else:
                j = self.block(tokens, j)
            first = False
        self.container_depth -= 1
        return end

    def timeline(self, timeline: schedule.Timeline, token: Token) -> None:
        """A ``::: timeline`` as a picture as wide as the text (E15-S01), drawn like the
        drawings of the code-block renderers (SVG with a PNG beside it)."""
        line = self.line(token)
        picture = schedule_drawing.timeline(timeline, self.text_width / EMU_PER_PIXEL)
        self.drawings += 1
        conversion = docx_drawings.convert(
            picture, layout_syntax.TIMELINE, line, self.drawings, self.options.image_converters
        )
        paragraph = self.paragraph(word.STYLES.normal)
        self.insert_picture(
            paragraph,
            conversion.image,
            conversion.image.path,
            timeline.alt,
            "",
            line,
            natural=(conversion.width, conversion.height),
            svg=conversion.svg,
        )

    def gantt(self, gantt: schedule.Gantt) -> None:
        """A ``::: gantt`` as a table in the PTA table style (E15-S01): the task, who (if the
        Markdown has the column), then a narrow column per week, month or quarter; the columns a
        task runs in are shaded (light blue for another owner than the first), a milestone is a
        diamond, the column of today has a dark blue rule on its right."""
        owner = gantt.owner_heading is not None
        units = gantt.units
        columns = 1 + int(owner) + len(units)
        table = self.document.add_table(rows=1 + len(gantt.rows), cols=columns)
        table.style = word.STYLES.table
        table.autofit = False
        name_width = int(self.text_width * word.GANTT_NAME_SHARE)
        owner_width = int(self.text_width * word.GANTT_OWNER_SHARE) if owner else 0
        unit_width = (self.text_width - name_width - owner_width) // len(units)
        widths = [name_width] + ([owner_width] if owner else []) + [unit_width] * len(units)
        _set_table_width(table, widths)
        _repeat_header(table, 0)
        first = 1 + int(owner)
        heads = [gantt.name_heading] + ([gantt.owner_heading or ""] if owner else [])
        heads += [unit.label for unit in units]
        today = gantt.today_unit
        for r in range(len(gantt.rows) + 1):
            row = gantt.rows[r - 1] if r else None
            for c in range(columns):
                cell = table.cell(r, c)
                cell.width = Emu(widths[c])
                paragraph = cell.paragraphs[0]
                properties = cell._tc.get_or_add_tcPr()
                if c >= first:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if row is None:
                    paragraph.add_run(heads[c])
                elif c == 0:
                    paragraph.add_run(row.name)
                elif owner and c == 1:
                    paragraph.add_run(row.owner or "")
                elif gantt.covers(row, units[c - first]):
                    if row.is_milestone:
                        run = paragraph.add_run(word.GANTT_MILESTONE)
                        run.font.color.rgb = RGBColor.from_string(colors.DARK_BLUE)
                    else:
                        secondary = gantt.is_secondary(row)
                        _shade(properties, colors.LIGHT_BLUE if secondary else colors.PTA_BLUE)
                if today is not None and c == first + today:
                    # After the shading: both go right after the width, the borders first.
                    _right_rule(properties, colors.DARK_BLUE)

    def note_box(self, tokens: list[Token], start: int, stop: int, style: str, label: str) -> None:
        """The blocks ``tokens[start:stop]`` in the note ``style``, the first paragraph starting
        with ``label`` in bold."""
        first = True
        j = start
        while j < stop:
            token = tokens[j]
            if token.type == "paragraph_open":
                paragraph = self.paragraph(style)
                if first:
                    self._label(paragraph, label)
                self.inline(paragraph, tokens[j + 1])
                j += 3
            else:
                if first:
                    self._label(self.paragraph(style), label)
                j = self.block(tokens, j, style)
            first = False
        if first:
            self._label(self.paragraph(style), label)

    def _label(self, paragraph: Paragraph, label: str) -> None:
        context = _Inline(paragraph._p, self.document.part, paragraph)
        context.format.bold = True
        self._run(context, label + ":")
        context.format.bold = False
        self._run(context, " ")

    def slide_kind(self, tokens: list[Token], i: int, inline: Token, kind: str) -> int:
        """A ``##`` section of a PTA slide kind (E04-S04), shown plainly: the agenda as a heading
        with its list (without one: the chapters after it), the interim conclusion as bold text,
        the quote and its source as quotes, the contacts as a heading with a bold line per
        person, the photo small and each line on its own."""
        end = i + 3
        while end < len(tokens) and not (
            tokens[end].type == "heading_open"
            and tokens[end].level == 0
            and tokens[end].tag in ("h1", "h2")
        ):
            end += 1
        style: str | None = None
        match kind:
            case heading_attributes.INTERIM:
                paragraph = self.paragraph(word.STYLES.normal_bold)
                self.inline(paragraph, inline, plain_bold=True)
            case heading_attributes.QUOTE:
                style = word.STYLES.quote
                self.inline(self.paragraph(style), inline)
            case _:
                self.inline(self.paragraph(word.STYLES.headings[1]), inline)
        if kind == heading_attributes.AGENDA and all(
            t.type == "html_block" and html.is_comment(t.content) for t in tokens[i + 3 : end]
        ):
            self.chapters(tokens, end)
        self.kind = kind
        j = i + 3
        while j < end:
            j = self.block(tokens, j, style)
        self.kind = None
        return end

    def chapters(self, tokens: list[Token], start: int) -> None:
        """The ``#`` headings from ``tokens[start]`` on (the closing one aside) as a numbered
        list: the agenda without a list of its own."""
        num_id: str | None = None
        for i in range(start, len(tokens)):
            token = tokens[i]
            if token.type != "heading_open" or token.tag != "h1" or token.level != 0:
                continue
            inline, attributes = layout_syntax.without_attributes(tokens[i + 1], 1, FORMAT)
            if attributes is not None and attributes.closing:
                continue
            style = word.STYLES.list_number
            num_id = num_id or self._new_num(style)
            paragraph = self.paragraph(style)
            _set_numbering(paragraph, num_id, 0)
            self.inline(paragraph, inline)

    def paragraph_block(self, tokens: list[Token], i: int, style: str | None) -> int:
        inline = tokens[i + 1]
        children = inline.children or []
        after = tokens[i + 3] if i + 3 < len(tokens) else None

        if self.kind == heading_attributes.CONTACT and style is None:
            paragraph = self.paragraph(word.STYLES.normal)
            context = _Inline(
                paragraph._p,
                self.document.part,
                paragraph,
                line_breaks=True,
                photo_width=int(Cm(word.CONTACT_PHOTO_CM)),
            )
            self._inline_children(context, inline)
            return i + 3
        if style is None and self._is_table_caption(inline) and self._previous_is_table():
            self.caption(self.texts.table, inline, strip_prefix=True)
            return i + 3
        if style is None and (images := layout_tokens.only_images(inline)) is not None:
            lines = child_lines(inline, self.front.body_line)
            at = {id(c): line for c, line in zip(children, lines, strict=True)}
            self.picture_row([(image, at[id(image)]) for image in images])
            return i + 3
        if style is None and block_shapes.only_images(children):
            lines = child_lines(inline, self.front.body_line)
            for image, line in zip(children, lines, strict=True):
                if image.type == "image":
                    self.figure(image, line)
            return i + 3
        if style is None and block_shapes.only_strong(children):
            paragraph = self.paragraph(word.STYLES.normal_bold)
            self.inline(paragraph, inline, plain_bold=True)
            if after is not None and after.type == "table_open":
                paragraph.paragraph_format.keep_with_next = True
            return i + 3
        paragraph = self.paragraph(style or word.STYLES.normal)
        self.inline(paragraph, inline)
        return i + 3

    def list_block(
        self,
        tokens: list[Token],
        i: int,
        depth: int,
        list_style: str | None,
        num_id: str | None,
    ) -> int:
        ordered = tokens[i].type == "ordered_list_open"
        close = "ordered_list_close" if ordered else "bullet_list_close"
        if list_style is None:
            # The outermost list decides the style; nested lists keep it and go one level down.
            list_style = word.STYLES.list_number if ordered else word.STYLES.list_bullet
            num_id = self._new_num(list_style) if ordered else self._style_num(list_style)
        assert num_id is not None
        level = min(depth, 2)
        j = i + 1
        while tokens[j].type != close:
            if tokens[j].type != "list_item_open":
                j += 1
                continue
            j += 1
            first = True
            while tokens[j].type != "list_item_close":
                t = tokens[j]
                if t.type == "paragraph_open":
                    if first:
                        paragraph = self.paragraph(list_style)
                        _set_numbering(paragraph, num_id, level)
                        self.inline(paragraph, tokens[j + 1])
                        first = False
                    else:
                        paragraph = self.paragraph(word.STYLES.normal)
                        paragraph.paragraph_format.left_indent = Cm(LIST_INDENT_CM[level])
                        self.inline(paragraph, tokens[j + 1])
                    j += 3
                elif t.type in ("bullet_list_open", "ordered_list_open"):
                    j = self.list_block(tokens, j, depth + 1, list_style, num_id)
                    first = False
                else:
                    j = self.block(tokens, j)
                    first = False
            j += 1
        return j + 1

    def definition_list(self, tokens: list[Token], i: int) -> int:
        j = i + 1
        while tokens[j].type != "dl_close":
            t = tokens[j]
            if t.type == "dt_open":
                paragraph = self.paragraph(word.STYLES.normal_bold)
                self.inline(paragraph, tokens[j + 1], plain_bold=True)
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
        table = self.document.add_table(rows=len(rows), cols=columns)
        table.style = word.STYLES.table
        table.autofit = False
        widths = text_metrics.column_widths(
            [[_plain_runs(cell) for cell, _ in row] for row in rows],
            self.text_width,
            TABLE_FONT_PT,
            int(TABLE_CELL_GAP),
            header=header_rows > 0,
        )
        _set_table_width(table, widths)
        for r, row in enumerate(rows):
            if r < header_rows:
                _repeat_header(table, r)
            marked = layout_tokens.marked_row([content for content, _ in row])
            for c in range(columns):
                cell = table.cell(r, c)
                cell.width = Emu(widths[c])
                if marked:
                    _shade(cell._tc.get_or_add_tcPr(), word.MARK_COLOR)
                if c >= len(row):
                    continue
                content, align = row[c]
                paragraph = cell.paragraphs[0]
                if align == "right":
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                elif align == "center":
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                label = layout_tokens.label_cell(content)
                if label is not None and label in self.labels:
                    # A status label: in the character style of its category, not as code.
                    context = _Inline(paragraph._p, self.document.part, paragraph)
                    context.format.status = self.labels[label]
                    self._run(context, label)
                else:
                    self.inline(paragraph, content)
        return j + 1

    def picture_row(self, images: list[tuple[Token, int | None]]) -> None:
        """Two or more pictures side by side: a table without rules over the text width, equal
        cells, a caption under each picture in its cell, more than four on further rows."""
        per_row = word.PICTURES_PER_ROW
        columns = min(len(images), per_row)
        rows = math.ceil(len(images) / per_row)
        table = self.document.add_table(rows=rows, cols=columns)
        table.style = self._ensure_picture_row_style()
        table.autofit = False
        width = self.text_width // columns
        _set_table_width(table, [width] * columns)
        room = width - int(Cm(word.PICTURE_GAP_CM))
        for n, (image, line) in enumerate(images):
            r, c = divmod(n, per_row)
            cell = table.cell(r, c)
            paragraph = cell.paragraphs[0]
            self.picture(paragraph, image, line, room)
            text = str(image.attrs.get("title") or "") or image.content
            if text:
                paragraph.paragraph_format.keep_with_next = True
                caption = cell.add_paragraph(
                    style=cast(ParagraphStyle, self.document.styles[word.STYLES.caption])
                )
                self.caption(self.texts.figure, None, text=text, paragraph=caption)
        for r, row in enumerate(table.rows):
            for c in range(columns):
                table.cell(r, c).width = Emu(width)
            etree.SubElement(row._tr.get_or_add_trPr(), w("cantSplit"))
            if r < rows - 1:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        paragraph.paragraph_format.keep_with_next = True

    def _previous_is_table(self) -> bool:
        body: etree._Element = self.document.element.body  # type: ignore[attr-defined]
        last = [child for child in body if child.tag != w("sectPr")]
        return bool(last) and last[-1].tag == w("tbl")

    def _is_table_caption(self, inline: Token) -> bool:
        return block_shapes.is_table_caption(inline, self.texts)

    # ------------------------------------------------------------------ figures and captions

    def figure(self, image: Token, line: int | None) -> None:
        paragraph = self.paragraph(word.STYLES.normal)
        self.picture(paragraph, image, line)
        text = str(image.attrs.get("title") or "") or image.content
        if text:
            paragraph.paragraph_format.keep_with_next = True
            self.caption(self.texts.figure, None, text=text)

    def graphic_figure(
        self, graphic: CodeBlockGraphic, fence: Token, caption: Token | None
    ) -> None:
        """A graphic of a code-block renderer in its own paragraph (E03-S04), below it
        "Abbildung n: …" from ``caption`` (an ``Abbildung: …`` paragraph after the block) or
        the chart's title; without either no caption. Graphic and caption stay together."""
        info = fence.info.strip()
        line = self.line(fence)
        paragraph = self.paragraph(word.STYLES.normal)
        title: str | None = None
        source: str | None = None
        match graphic:
            case ChartGraphic(chart=spec):
                width, height = self.chart_size()
                docx_chart.add_chart(paragraph, spec, width, height, spec.title or info)
                title, source = spec.title, spec.source
            case DrawingGraphic(drawing=drawing):
                self.drawings += 1
                conversion = docx_drawings.convert(
                    drawing, info, line, self.drawings, self.options.image_converters
                )
                self.insert_picture(
                    paragraph,
                    conversion.image,
                    conversion.image.path,
                    info,
                    "",
                    line,
                    natural=(conversion.width, conversion.height),
                    svg=conversion.svg,
                )
            case ImageGraphic(image=image):
                self.place_picture(paragraph, image, image.path, info, "", line)
        if caption is not None or title or source:
            paragraph.paragraph_format.keep_with_next = True
        if caption is not None:
            self.caption(self.texts.figure, caption, strip_prefix=True)
        elif title:
            self.caption(self.texts.figure, None, text=title)
        if source:
            _append_text(self.paragraph(word.STYLES.caption)._p, source)

    def chart_size(self) -> tuple[int, int]:
        """A chart is as wide as the text and at most 5:8 as high, but never higher than 80 %
        of the text height (E03-S04), in EMU."""
        width = self.text_width
        height = min(
            round(width * word.CHART_HEIGHT_RATIO),
            int(self.text_height * word.FIGURE_HEIGHT_SHARE),
        )
        return width, height

    def caption(
        self,
        label: str,
        inline: Token | None,
        strip_prefix: bool = False,
        text: str | None = None,
        paragraph: Paragraph | None = None,
    ) -> None:
        if label == self.texts.table:
            self.tables += 1
            number = self.tables
        else:
            self.figures += 1
            number = self.figures
        paragraph = paragraph or self.paragraph(word.STYLES.caption)
        _append_text(paragraph._p, f"{label} ")
        for run in field_paragraph_runs(f"SEQ {label} \\* ARABIC", str(number)):
            paragraph._p.append(run)
        _append_text(paragraph._p, ": ")
        if inline is not None:
            if strip_prefix:
                inline = block_shapes.strip_caption_prefix(inline)
            self.inline(paragraph, inline)
        elif text:
            _append_text(paragraph._p, text)

    def picture(
        self, paragraph: Paragraph, image: Token, line: int | None, width: int | None = None
    ) -> None:
        source = str(image.attrs.get("src", ""))
        resource = self.source.find_resource(source)
        if resource is None:
            where = f" (line {line})" if line else ""
            raise DocumentConversionError(
                FORMAT, f"The image '{source}'{where} is not among the document's resources."
            )
        title = str(image.attrs.get("title") or "")
        scale = generated_images.scale_of(image)
        self.place_picture(paragraph, resource, source, image.content, title, line, width, scale)

    def place_picture(
        self,
        paragraph: Paragraph,
        resource: DocumentResource,
        source: str,
        alt: str,
        title: str,
        line: int | None,
        max_width: int | None = None,
        scale: float = 1.0,
    ) -> None:
        """``resource`` as a picture in ``paragraph``, ``scale`` times its size; a format DOCX
        does not take goes through the image converters and is placed at its natural size
        (never wider than ``max_width``, default the text width)."""
        where = f" (line {line})" if line else ""
        natural: tuple[float, float] | None = None
        svg: bytes | None = None
        if resource.content_type not in SUPPORTED_IMAGES:
            converters = self.options.image_converters
            conversion = convert_image(converters, resource, GENERATOR_SCALE, FORMAT)
            if conversion is None:
                hint = refusal_hint(resource, converters)
                raise DocumentConversionError(
                    FORMAT,
                    f"The image '{source}'{where} is a {resource.content_type}; DOCX takes PNG, "
                    f"JPEG, GIF, BMP and TIFF{hint}.",
                )
            resource = conversion.image
            natural = (conversion.width, conversion.height)
            svg = conversion.svg
        self.insert_picture(
            paragraph,
            resource,
            source,
            alt,
            title,
            line,
            max_width,
            natural=natural,
            svg=svg,
            scale=scale,
        )

    def insert_picture(
        self,
        paragraph: Paragraph,
        resource: DocumentResource,
        source: str,
        alt: str,
        title: str,
        line: int | None,
        max_width: int | None = None,
        *,
        natural: tuple[float, float] | None = None,
        svg: bytes | None = None,
        scale: float = 1.0,
    ) -> None:
        """``resource`` (PNG, JPEG …) as a picture in ``paragraph``, at its ``natural`` size in
        pixels if given (times ``scale``), with ``svg`` beside it (``asvg:svgBlip``) if given."""
        width, height = self._image_size(resource.content, natural, max_width, scale)
        with Image.open(io.BytesIO(resource.content)) as opened:
            factor = width / (opened.size[0] * EMU_PER_PIXEL)
        if factor > MAX_ENLARGEMENT:
            self.notes.add(
                NoteCodes.IMAGE_ENLARGED,
                line,
                f"The image '{source}' is shown at {factor:.1f} times its size (below "
                f"{96 / factor:.0f} dpi) and may look blurred. Use a larger image.",
            )
        run = paragraph.add_run()
        try:
            run.add_picture(io.BytesIO(resource.content), width=Emu(width), height=Emu(height))
        except UnrecognizedImageError:
            # python-docx only knows JPEGs with a JFIF or Exif header (not e.g. ICC first).
            run._r.clear()
            run.add_picture(
                io.BytesIO(_reencode(resource.content)), width=Emu(width), height=Emu(height)
            )
        if svg is not None:
            svg_blip.attach(run._r, run.part, svg, _svg_part(run.part))
        for doc_pr in run._r.iter(
            "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr"
        ):
            doc_pr.set("descr", alt)
            if title:
                doc_pr.set("title", title)

    def _image_size(
        self,
        content: bytes,
        natural: tuple[float, float] | None = None,
        max_width: int | None = None,
        factor: float = 1.0,
    ) -> tuple[int, int]:
        """The size of the picture in EMU: from its pixels and dpi, or its ``natural`` size in
        pixels at 96 dpi, times ``factor`` (``scale=N`` of a QR code); never wider than the text
        or higher than 80 % of the page."""
        if natural is not None:
            width = natural[0] * EMU_PER_PIXEL
            height = natural[1] * EMU_PER_PIXEL
        else:
            with Image.open(io.BytesIO(content)) as picture:
                pixels_x, pixels_y = picture.size
                dpi = picture.info.get("dpi", (96, 96))
            dpi_x = float(dpi[0]) or 96.0
            dpi_y = float(dpi[1]) or 96.0
            width = pixels_x / dpi_x * EMU_PER_INCH
            height = pixels_y / dpi_y * EMU_PER_INCH
        width *= factor
        height *= factor
        widest = min(self.text_width, max_width or self.text_width)
        scale = min(1.0, widest / width, self.text_height * word.FIGURE_HEIGHT_SHARE / height)
        return int(width * scale), int(height * scale)

    # ------------------------------------------------------------------ other blocks

    def code_block(self, token: Token) -> None:
        """A code block in the style "Code"; with a known language, its tokens in the PTA
        colours (E17-S02). The language of a fence goes into the paragraph properties."""
        paragraph = self.paragraph(self._ensure_code_style())
        lines = token.content.rstrip("\n").split("\n")
        info = token.info.strip() if token.type == "fence" else ""
        spans = code_highlight.highlight_fence(
            info, lines, self.line(token), self.notes, self.options.highlight
        )
        for n, text in enumerate(lines):
            if n:
                etree.SubElement(etree.SubElement(paragraph._p, w("r")), w("br"))
            if spans is None:
                _append_text(paragraph._p, text)
            else:
                for span in spans[n]:
                    _append_code_span(paragraph._p, span)
        if info:
            p_pr = paragraph._p.get_or_add_pPr()
            etree.SubElement(p_pr, CODE_LANGUAGE).set(CODE_LANGUAGE_VALUE, info)
            _order_ppr(p_pr)

    def horizontal_rule(self) -> None:
        paragraph = self.paragraph(word.STYLES.normal)
        p_pr = paragraph._p.get_or_add_pPr()
        borders = etree.SubElement(p_pr, w("pBdr"))
        bottom = etree.SubElement(borders, w("bottom"))
        for name, value in (
            ("val", "single"),
            ("sz", "4"),
            ("space", "1"),
            ("color", word.HORIZONTAL_RULE_COLOR),
        ):
            bottom.set(w(name), value)
        _order_ppr(p_pr)

    # ------------------------------------------------------------------ paragraphs and styles

    def paragraph(self, style: str) -> Paragraph:
        if style == word.STYLES.quote:
            self._ensure_quote_style()
        elif style == word.STYLES.note:
            self._ensure_note_style(style, word.NOTE)
        elif style == word.STYLES.note_important:
            self._ensure_note_style(style, word.NOTE_IMPORTANT)
        return self.document.add_paragraph(style=cast(ParagraphStyle, self.document.styles[style]))

    def _ensure_code_style(self) -> str:
        name = word.STYLES.code
        if name not in [s.name for s in self.document.styles]:
            style = cast(
                ParagraphStyle, self.document.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            )
            style.base_style = self.document.styles[word.STYLES.normal]
            style.font.name = word.CODE.font
            style.font.size = Pt(word.CODE.size_pt)
            element: Any = style.element
            p_pr = element.get_or_add_pPr()
            shading = etree.SubElement(p_pr, w("shd"))
            shading.set(w("val"), "clear")
            shading.set(w("color"), "auto")
            shading.set(w("fill"), word.CODE.background)
            spacing = etree.SubElement(p_pr, w("spacing"))
            spacing.set(w("line"), "240")
            spacing.set(w("lineRule"), "auto")
            _order_ppr(p_pr)
            r_pr = element.get_or_add_rPr()
            fonts = r_pr.find(w("rFonts"))
            if fonts is not None:
                fonts.set(w("cs"), word.CODE.font)
                fonts.set(w("eastAsia"), word.CODE.font)
        return name

    def _ensure_quote_style(self) -> None:
        name = word.STYLES.quote
        if name not in [s.name for s in self.document.styles]:
            style = cast(
                ParagraphStyle, self.document.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            )
            style.base_style = self.document.styles[word.STYLES.normal]
            style.paragraph_format.left_indent = Cm(word.QUOTE_INDENT_CM)

    def _has_style(self, name: str) -> bool:
        return name in [s.name for s in self.document.styles]

    def _ensure_note_style(self, name: str, design: word.NoteStyle) -> None:
        """A paragraph style for alerts and boxes, on ``Standard``: a rule on the left and a
        light grey area."""
        if self._has_style(name):
            return
        style = cast(ParagraphStyle, self.document.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH))
        style.base_style = self.document.styles[word.STYLES.normal]
        element: Any = style.element
        p_pr = element.get_or_add_pPr()
        borders = etree.SubElement(p_pr, w("pBdr"))
        left = etree.SubElement(borders, w("left"))
        left.set(w("val"), "single")
        left.set(w("sz"), str(int(design.rule_pt * 8)))
        left.set(w("space"), str(int(design.indent_pt)))
        left.set(w("color"), design.rule)
        _shade(p_pr, design.background)
        indent = etree.SubElement(p_pr, w("ind"))
        indent.set(w("left"), str(int(design.indent_pt * 20)))
        _order_ppr(p_pr)

    def _character_style(
        self, name: str, color: str | None = None, shading: str | None = None
    ) -> str:
        """The id of the character style ``name``, added when missing: bold in ``color``, or
        on ``shading``."""
        if not self._has_style(name):
            style = self.document.styles.add_style(name, WD_STYLE_TYPE.CHARACTER)
            element: Any = style.element
            r_pr = element.get_or_add_rPr()
            if color is not None:
                etree.SubElement(r_pr, w("b"))
                etree.SubElement(r_pr, w("bCs"))
                etree.SubElement(r_pr, w("color")).set(w("val"), color)
            if shading is not None:
                _shade(r_pr, shading)
        return self.style_id(name)

    def _ensure_picture_row_style(self) -> str:
        name = word.STYLES.picture_row
        if not self._has_style(name):
            # python-docx makes table styles paragraph styles (_TableStyle).
            style = cast(ParagraphStyle, self.document.styles.add_style(name, WD_STYLE_TYPE.TABLE))
            style.base_style = self.document.styles[word.TABLE_BASE_STYLE]
            element: Any = style.element
            tbl_pr = etree.SubElement(element, w("tblPr"))
            borders = etree.SubElement(tbl_pr, w("tblBorders"))
            for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
                etree.SubElement(borders, w(side)).set(w("val"), "nil")
        return name

    def style_id(self, name: str) -> str:
        if name not in self.style_ids:
            self.style_ids[name] = str(self.document.styles[name].style_id)
        return self.style_ids[name]

    # ------------------------------------------------------------------ inline

    def inline(self, paragraph: Paragraph, token: Token, plain_bold: bool = False) -> None:
        context = _Inline(paragraph._p, self.document.part, paragraph, plain_bold=plain_bold)
        self._inline_children(context, token)

    def _inline_children(self, context: _Inline, token: Token, skip: tuple[str, ...] = ()) -> None:
        """The children of the inline ``token`` (without those of a type in ``skip``)."""
        stack: list[etree._Element] = []
        token = layout_syntax.coloured(token, FORMAT)
        children = token.children or []
        for child, line in zip(children, child_lines(token, self.front.body_line), strict=True):
            if child.type in skip:
                continue
            match child.type:
                case "text" if layout_syntax.STATUS in child.meta:
                    status = context.format.status
                    context.format.status = child.meta[layout_syntax.STATUS]
                    self._run(context, child.content)
                    context.format.status = status
                case "text":
                    self._run(context, child.content)
                case "softbreak" if context.line_breaks:
                    etree.SubElement(self._new_run(context), w("br"))
                case "softbreak":
                    self._run(context, " ")
                case "mark_open":
                    context.format.mark = True
                case "mark_close":
                    context.format.mark = False
                case "hardbreak":
                    etree.SubElement(self._new_run(context), w("br"))
                case "code_inline":
                    self._run(context, child.content, code=True)
                case "strong_open":
                    context.format.bold = True
                case "strong_close":
                    context.format.bold = False
                case "em_open":
                    context.format.italic = True
                case "em_close":
                    context.format.italic = False
                case "s_open":
                    context.format.strike = True
                case "s_close":
                    context.format.strike = False
                case "link_open":
                    href = str(child.attrs.get("href", ""))
                    if ABSOLUTE_URI.match(href):
                        r_id = context.part.relate_to(href, RT.HYPERLINK, is_external=True)
                        link = etree.SubElement(context.target, w("hyperlink"))
                        link.set(f"{{{R}}}id", r_id)
                        link.set(w("history"), "1")
                        stack.append(context.target)
                        context.target = link
                    else:
                        stack.append(context.target)
                case "link_close":
                    if stack:
                        context.target = stack.pop()
                case "image":
                    if context.images and context.paragraph is not None:
                        self.picture(context.paragraph, child, line, context.photo_width)
                    else:
                        self._run(context, child.content)
                case "footnote_ref":
                    self._footnote_reference(context, child)
                case "html_inline":
                    if html.is_checkbox(child.content):
                        self._run(context, "☒" if "checked" in child.content else "☐")
                    elif html.is_line_break(child.content):
                        etree.SubElement(self._new_run(context), w("br"))
                    elif not html.is_comment(child.content):
                        html.note_raw_html(self.notes, line, WHAT)
                case _:
                    if child.content:
                        self._run(context, child.content)

    def _new_run(self, context: _Inline) -> etree._Element:
        return etree.SubElement(context.target, w("r"))

    def _run(self, context: _Inline, text: str, code: bool = False) -> None:
        if not text:
            return
        run = self._new_run(context)
        r_pr = etree.Element(w("rPr"))
        status = context.format.status
        style: str | None = None
        if context.target.tag == w("hyperlink"):
            style = self.style_id(word.STYLES.hyperlink)
        elif status is not None:
            style = self._character_style(
                word.STYLES.status_style(status), color=STATUS_COLORS[status]
            )
        elif context.format.mark:
            style = self._character_style(word.STYLES.mark, shading=word.MARK_COLOR)
        if style is not None:
            etree.SubElement(r_pr, w("rStyle")).set(w("val"), style)
        if code:
            fonts = etree.SubElement(r_pr, w("rFonts"))
            for attribute in ("ascii", "hAnsi", "cs", "eastAsia"):
                fonts.set(w(attribute), word.INLINE_CODE_FONT)
        if context.format.bold and not context.plain_bold and status is None:
            etree.SubElement(r_pr, w("b"))
        if context.format.italic:
            etree.SubElement(r_pr, w("i"))
        if context.format.strike:
            etree.SubElement(r_pr, w("strike"))
        if len(r_pr):
            run.append(r_pr)
        t = etree.SubElement(run, w("t"))
        t.text = text
        t.set(XML_SPACE, "preserve")

    # ------------------------------------------------------------------ footnotes

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

    def _footnotes(self) -> tuple[Part, etree._Element]:
        if self.footnotes_part is None or self.footnotes_root is None:
            part = self.document.part.part_related_by(FOOTNOTES_RT)
            root = etree.fromstring(part.blob)
            ids = [int(f.get(w("id"), "0")) for f in root.iterfind(w("footnote"))]
            self.next_footnote_id = max([*ids, 0]) + 1
            self.footnotes_part, self.footnotes_root = part, root
        return self.footnotes_part, self.footnotes_root

    def _footnote_reference(self, context: _Inline, token: Token) -> None:
        part, root = self._footnotes()
        footnote_id = self.next_footnote_id
        self.next_footnote_id += 1
        reference_style = self.style_id(word.STYLES.footnote_reference)

        run = self._new_run(context)
        r_pr = etree.SubElement(run, w("rPr"))
        etree.SubElement(r_pr, w("rStyle")).set(w("val"), reference_style)
        etree.SubElement(run, w("footnoteReference")).set(w("id"), str(footnote_id))

        footnote = etree.SubElement(root, w("footnote"))
        footnote.set(w("id"), str(footnote_id))
        definition = self.footnote_definitions.get(int(token.meta["id"]), [])
        paragraphs = [t for t in definition if t.type == "inline"] or [None]
        for n, inline in enumerate(paragraphs):
            p = etree.SubElement(footnote, w("p"))
            p_pr = etree.SubElement(p, w("pPr"))
            etree.SubElement(p_pr, w("pStyle")).set(
                w("val"), self.style_id(word.STYLES.footnote_text)
            )
            if n == 0:
                mark = etree.SubElement(p, w("r"))
                etree.SubElement(etree.SubElement(mark, w("rPr")), w("rStyle")).set(
                    w("val"), reference_style
                )
                etree.SubElement(mark, w("footnoteRef"))
                _append_text(p, " ")
            if inline is not None:
                inner = _Inline(p, part, None, images=False)
                self._inline_children(inner, inline, skip=("footnote_anchor",))

    def _save_footnotes(self) -> None:
        if self.footnotes_part is not None and self.footnotes_root is not None:
            blob = etree.tostring(
                self.footnotes_root, xml_declaration=True, encoding="UTF-8", standalone=True
            )
            self.footnotes_part._blob = blob  # type: ignore[attr-defined]

    # ------------------------------------------------------------------ numbering

    def _style_num(self, style: str) -> str:
        element = self.document.styles[style].element
        num = element.find(f"{w('pPr')}/{w('numPr')}/{w('numId')}")
        if num is None:
            raise DocumentConversionError(FORMAT, f"The style '{style}' has no numbering.")
        return str(num.get(w("val")))

    def _new_num(self, style: str) -> str:
        """A new numbering instance of the style's list, so that the list starts at 1."""
        numbering = self.document.part.numbering_part.element
        base = self._style_num(style)
        source = numbering.find(f"{w('num')}[@{w('numId')}='{base}']")
        if source is None:
            raise DocumentConversionError(FORMAT, f"The numbering {base} of '{style}' is missing.")
        abstract = source.find(w("abstractNumId"))
        assert abstract is not None
        ids = [int(n.get(w("numId"), "0")) for n in numbering.iterfind(w("num"))]
        new_id = str(max(ids) + 1)
        num = etree.Element(w("num"))
        num.set(w("numId"), new_id)
        etree.SubElement(num, w("abstractNumId")).set(w("val"), str(abstract.get(w("val"))))
        override = etree.SubElement(num, w("lvlOverride"))
        override.set(w("ilvl"), "0")
        etree.SubElement(override, w("startOverride")).set(w("val"), "1")
        last = numbering.findall(w("num"))[-1]
        last.addnext(num)
        return new_id


# ---------------------------------------------------------------------- helpers


def _svg_part(owner: Any) -> svg_blip.PartFactory:
    """Makes SVG parts in the package of ``owner`` (python-docx: blob before package)."""

    def new_part(partname: str, blob: bytes) -> Part:
        return Part(PackURI(partname), svg_blip.CONTENT_TYPE, blob, owner.package)

    return new_part


def _reencode(content: bytes) -> bytes:
    """The picture saved again by Pillow: JPEG with a JFIF header, everything else as PNG."""
    with Image.open(io.BytesIO(content)) as picture:
        buffer = io.BytesIO()
        if picture.format == "JPEG":
            picture.save(buffer, "JPEG", quality=92, dpi=picture.info.get("dpi", (96, 96)))
        else:
            picture.save(buffer, "PNG")
        return buffer.getvalue()


def _block_end(tokens: list[Token], i: int) -> int:
    """The index after the block that opens at ``tokens[i]``."""
    if tokens[i].nesting != 1:
        return i + 1
    j = i + 1
    while not (tokens[j].nesting == -1 and tokens[j].level == tokens[i].level):
        j += 1
    return j + 1


def _shade(properties: etree._Element, fill: str) -> None:
    """Shading of ``fill`` in paragraph, run or cell properties (in schema order for cells)."""
    shading = etree.SubElement(properties, w("shd"))
    shading.set(w("val"), "clear")
    shading.set(w("color"), "auto")
    shading.set(w("fill"), fill)
    if properties.tag == w("tcPr"):
        width = properties.find(w("tcW"))
        if width is not None:
            width.addnext(shading)


def _right_rule(properties: etree._Element, color: str) -> None:
    """A rule on the right of a cell (the column of today in a Gantt table), in schema order."""
    borders = etree.Element(w("tcBorders"))
    right = etree.SubElement(borders, w("right"))
    right.set(w("val"), "single")
    right.set(w("sz"), str(word.GANTT_TODAY_RULE))
    right.set(w("space"), "0")
    right.set(w("color"), color)
    width = properties.find(w("tcW"))
    if width is not None:
        width.addnext(borders)
    else:
        properties.insert(0, borders)


def _plain_runs(token: Token) -> list[TextRun]:
    runs: list[TextRun] = []
    bold = False
    for child in token.children or []:
        if child.type == "strong_open":
            bold = True
        elif child.type == "strong_close":
            bold = False
        elif child.type in ("softbreak",):
            runs.append(TextRun(" ", bold))
        elif child.type == "hardbreak":
            runs.append(text_metrics.BREAK)
        elif child.content:
            runs.append(TextRun(child.content, bold))
    return runs


def _append_code_span(parent: etree._Element, span: code_highlight.CodeSpan) -> None:
    run = etree.SubElement(parent, w("r"))
    look = span.look
    if look.color is not None or look.bold or look.italic:
        r_pr = etree.SubElement(run, w("rPr"))
        if look.bold:
            etree.SubElement(r_pr, w("b"))
        if look.italic:
            etree.SubElement(r_pr, w("i"))
        if look.color is not None:
            etree.SubElement(r_pr, w("color")).set(w("val"), look.color)
    t = etree.SubElement(run, w("t"))
    t.text = span.text
    t.set(XML_SPACE, "preserve")


def declare_own_namespace(document: Document) -> None:
    """Declare ``PTA_NAMESPACE`` on the document element and make it ignorable, when the body
    uses it (code languages). Word skips what it does not know only if it is told so."""
    root: etree._Element = document.part.element  # type: ignore[attr-defined]
    if next(root.iter(CODE_LANGUAGE), None) is None:
        return
    etree.cleanup_namespaces(
        root, top_nsmap={PTA_PREFIX: PTA_NAMESPACE}, keep_ns_prefixes=[p for p in root.nsmap if p]
    )
    ignorable = (root.get(MC_IGNORABLE) or "").split()
    if PTA_PREFIX not in ignorable:
        root.set(MC_IGNORABLE, " ".join([*ignorable, PTA_PREFIX]))


def _append_text(parent: etree._Element, text: str) -> None:
    run = etree.SubElement(parent, w("r"))
    t = etree.SubElement(run, w("t"))
    t.text = text
    t.set(XML_SPACE, "preserve")


def _set_numbering(paragraph: Paragraph, num_id: str, level: int) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    num_pr = etree.SubElement(p_pr, w("numPr"))
    etree.SubElement(num_pr, w("ilvl")).set(w("val"), str(level))
    etree.SubElement(num_pr, w("numId")).set(w("val"), num_id)
    _order_ppr(p_pr)


_PPR_ORDER: Final = (
    "pStyle",
    "keepNext",
    "keepLines",
    "pageBreakBefore",
    "framePr",
    "widowControl",
    "numPr",
    "suppressLineNumbers",
    "pBdr",
    "shd",
    "tabs",
    "suppressAutoHyphens",
    "kinsoku",
    "wordWrap",
    "overflowPunct",
    "topLinePunct",
    "autoSpaceDE",
    "autoSpaceDN",
    "bidi",
    "adjustRightInd",
    "snapToGrid",
    "spacing",
    "ind",
    "contextualSpacing",
    "mirrorIndents",
    "suppressOverlap",
    "jc",
    "textDirection",
    "textAlignment",
    "textboxTightWrap",
    "outlineLvl",
    "divId",
    "cnfStyle",
    "rPr",
    "sectPr",
    "pPrChange",
)


def _order_ppr(p_pr: etree._Element) -> None:
    """Sort the children of a ``w:pPr`` into schema order (Word is strict about it)."""

    def key(child: etree._Element) -> int:
        name = etree.QName(child).localname
        return _PPR_ORDER.index(name) if name in _PPR_ORDER else len(_PPR_ORDER)

    children = sorted(p_pr, key=key)
    for child in children:
        p_pr.append(child)


def _set_table_width(table: Table, widths: list[int]) -> None:
    tbl_pr = table._tbl.tblPr
    width = tbl_pr.find(w("tblW"))
    if width is None:
        width = etree.SubElement(tbl_pr, w("tblW"))
    width.set(w("w"), str(sum(widths) // EMU_PER_TWIP))
    width.set(w("type"), "dxa")
    layout = tbl_pr.find(w("tblLayout"))
    if layout is None:
        layout = etree.SubElement(tbl_pr, w("tblLayout"))
    layout.set(w("type"), "fixed")
    _order_tblpr(tbl_pr)
    for column, grid in zip(widths, table._tbl.tblGrid.iterfind(w("gridCol")), strict=False):
        grid.set(w("w"), str(column // EMU_PER_TWIP))


_TBLPR_ORDER: Final = (
    "tblStyle",
    "tblpPr",
    "tblOverlap",
    "bidiVisual",
    "tblStyleRowBandSize",
    "tblStyleColBandSize",
    "tblW",
    "jc",
    "tblCellSpacing",
    "tblInd",
    "tblBorders",
    "shd",
    "tblLayout",
    "tblCellMar",
    "tblLook",
    "tblCaption",
    "tblDescription",
)


def _order_tblpr(tbl_pr: etree._Element) -> None:
    def key(child: etree._Element) -> int:
        name = etree.QName(child).localname
        return _TBLPR_ORDER.index(name) if name in _TBLPR_ORDER else len(_TBLPR_ORDER)

    for child in sorted(tbl_pr, key=key):
        tbl_pr.append(child)


def _repeat_header(table: Table, row: int) -> None:
    tr = table.rows[row]._tr
    tr_pr = tr.get_or_add_trPr()
    etree.SubElement(tr_pr, w("tblHeader"))
