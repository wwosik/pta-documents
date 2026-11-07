"""Writes the Markdown body into the document, block by block, in the PTA styles.

Every block goes into a style of the PTA template (see ``design/word.py``); direct formatting
is only used for character formats (bold, italic, strikethrough, inline code, links), list
numbering, alignment and indents.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from typing import Any, Final, cast

from docx.document import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.image.exceptions import UnrecognizedImageError
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.part import Part
from docx.shared import Cm, Emu, Pt
from docx.styles.style import ParagraphStyle
from docx.table import Table
from docx.text.paragraph import Paragraph
from lxml import etree
from markdown_it.token import Token
from PIL import Image

from pta_documents.design import word
from pta_documents.design.variants import GeneratedTexts
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import (
    code_blocks,
    html,
    layout_syntax,
    text_metrics,
)
from pta_documents.generation.common.images import GENERATOR_SCALE, convert_image
from pta_documents.generation.common.openxml import R, field_paragraph_runs, w
from pta_documents.generation.common.renderers import ImageGraphic
from pta_documents.generation.common.result import NoteCodes, Notes
from pta_documents.generation.common.text_metrics import TextRun
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.markdown.document import DocumentResource, MarkdownDocument
from pta_documents.markdown.front_matter import FrontMatter
from pta_documents.markdown.parser import child_lines, create_parser, line_of

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


@dataclass
class _Format:
    bold: bool = False
    italic: bool = False
    strike: bool = False


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
        self.footnote_definitions: dict[int, list[Token]] = {}
        self.footnotes_part: Part | None = None
        self.footnotes_root: etree._Element | None = None
        self.next_footnote_id = 1
        self.style_ids: dict[str, str] = {}
        section = document.sections[0]
        page_width = int(section.page_width or 0)
        margins = int(section.left_margin or 0) + int(section.right_margin or 0)
        page_height = int(section.page_height or 0)
        vertical = int(section.top_margin or 0) + int(section.bottom_margin or 0)
        self.text_width = page_width - margins
        self.text_height = page_height - vertical

    # ------------------------------------------------------------------ entry

    def write(self) -> None:
        env: dict[str, object] = {}
        tokens = create_parser().parse(self.front.body, env)
        layout_syntax.check(tokens, FORMAT, self.front.body_line)
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
                styles = word.STYLES
                heading = styles.headings[level - 1] if level <= 3 else styles.sub_heading
                paragraph = self.paragraph(heading)
                # Heading attributes are checked, but have no effect in Word.
                inline, _ = layout_syntax.without_attributes(tokens[i + 1], level, FORMAT)
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
                if graphic is not None:
                    paragraph = self.paragraph(word.STYLES.normal)
                    self.place_picture(
                        paragraph,
                        graphic.image,
                        graphic.image.path,
                        token.info.strip(),
                        "",
                        self.line(token),
                    )
                else:
                    self.code_block(token.content)
                return i + 1
            case "html_block":
                if not html.is_comment(token.content):
                    html.note_raw_html(self.notes, self.line(token), WHAT)
                return i + 1
            case "blockquote_open":
                return self.container(tokens, i, "blockquote_close", word.STYLES.quote)
            case "hr":
                self.horizontal_rule()
                return i + 1
            case "dl_open":
                return self.definition_list(tokens, i)
            case _:
                return i + 1

    def line(self, token: Token) -> int | None:
        return line_of(token, self.front.body_line)

    def draw(self, fence: Token) -> ImageGraphic | None:
        """The image the code-block renderers make of ``fence``; None: it stays code."""
        return code_blocks.draw(
            self.options.code_block_renderers,
            self.notes,
            fence.info,
            fence.content,
            self.line(fence),
            FORMAT,
            self.options.language,
        )

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

    def paragraph_block(self, tokens: list[Token], i: int, style: str | None) -> int:
        inline = tokens[i + 1]
        children = inline.children or []
        after = tokens[i + 3] if i + 3 < len(tokens) else None

        if style is None and self._is_table_caption(inline) and self._previous_is_table():
            self.caption(self.texts.table, inline, strip_prefix=True)
            return i + 3
        if style is None and _only_images(children):
            lines = child_lines(inline, self.front.body_line)
            for image, line in zip(children, lines, strict=True):
                if image.type == "image":
                    self.figure(image, line)
            return i + 3
        if style is None and _only_strong(children):
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
            for c in range(columns):
                cell = table.cell(r, c)
                cell.width = Emu(widths[c])
                if c >= len(row):
                    continue
                content, align = row[c]
                paragraph = cell.paragraphs[0]
                if align == "right":
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                elif align == "center":
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                self.inline(paragraph, content)
        return j + 1

    def _previous_is_table(self) -> bool:
        body: etree._Element = self.document.element.body  # type: ignore[attr-defined]
        last = [child for child in body if child.tag != w("sectPr")]
        return bool(last) and last[-1].tag == w("tbl")

    def _is_table_caption(self, inline: Token) -> bool:
        prefixes = (self.texts.table + ":", "Tabelle:", "Table:")
        return inline.content.startswith(prefixes)

    # ------------------------------------------------------------------ figures and captions

    def figure(self, image: Token, line: int | None) -> None:
        paragraph = self.paragraph(word.STYLES.normal)
        self.picture(paragraph, image, line)
        text = str(image.attrs.get("title") or "") or image.content
        if text:
            paragraph.paragraph_format.keep_with_next = True
            self.caption(self.texts.figure, None, text=text)

    def caption(
        self,
        label: str,
        inline: Token | None,
        strip_prefix: bool = False,
        text: str | None = None,
    ) -> None:
        if label == self.texts.table:
            self.tables += 1
            number = self.tables
        else:
            self.figures += 1
            number = self.figures
        paragraph = self.paragraph(word.STYLES.caption)
        _append_text(paragraph._p, f"{label} ")
        for run in field_paragraph_runs(f"SEQ {label} \\* ARABIC", str(number)):
            paragraph._p.append(run)
        _append_text(paragraph._p, ": ")
        if inline is not None:
            if strip_prefix:
                inline = _strip_caption_prefix(inline)
            self.inline(paragraph, inline)
        elif text:
            _append_text(paragraph._p, text)

    def picture(self, paragraph: Paragraph, image: Token, line: int | None) -> None:
        source = str(image.attrs.get("src", ""))
        resource = self.source.find_resource(source)
        if resource is None:
            where = f" (line {line})" if line else ""
            raise DocumentConversionError(
                FORMAT, f"The image '{source}'{where} is not among the document's resources."
            )
        title = str(image.attrs.get("title") or "")
        self.place_picture(paragraph, resource, source, image.content, title, line)

    def place_picture(
        self,
        paragraph: Paragraph,
        resource: DocumentResource,
        source: str,
        alt: str,
        title: str,
        line: int | None,
    ) -> None:
        """``resource`` as a picture in ``paragraph``; a format DOCX does not take goes through
        the image converters and is placed at its natural size."""
        where = f" (line {line})" if line else ""
        natural: tuple[float, float] | None = None
        if resource.content_type not in SUPPORTED_IMAGES:
            converters = self.options.image_converters
            conversion = convert_image(converters, resource, GENERATOR_SCALE, FORMAT)
            if conversion is None:
                nobody = ", and no image converter takes it" if converters else ""
                raise DocumentConversionError(
                    FORMAT,
                    f"The image '{source}'{where} is a {resource.content_type}; DOCX takes PNG, "
                    f"JPEG, GIF, BMP and TIFF{nobody}.",
                )
            resource = conversion.image
            natural = (conversion.width, conversion.height)
        width, height = self._image_size(resource.content, natural)
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
        for doc_pr in run._r.iter(
            "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr"
        ):
            doc_pr.set("descr", alt)
            if title:
                doc_pr.set("title", title)

    def _image_size(
        self, content: bytes, natural: tuple[float, float] | None = None
    ) -> tuple[int, int]:
        """The size of the picture in EMU: from its pixels and dpi, or its ``natural`` size in
        pixels at 96 dpi; never wider than the text or higher than 80 % of the page."""
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
        scale = min(1.0, self.text_width / width, self.text_height * 0.8 / height)
        return int(width * scale), int(height * scale)

    # ------------------------------------------------------------------ other blocks

    def code_block(self, content: str) -> None:
        paragraph = self.paragraph(self._ensure_code_style())
        lines = content.rstrip("\n").split("\n")
        for n, text in enumerate(lines):
            if n:
                etree.SubElement(etree.SubElement(paragraph._p, w("r")), w("br"))
            _append_text(paragraph._p, text)

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
        # Coloured words are bold; their status character styles come with E03-S03.
        token = layout_syntax.coloured(token, FORMAT)
        children = token.children or []
        for child, line in zip(children, child_lines(token, self.front.body_line), strict=True):
            if child.type in skip:
                continue
            match child.type:
                case "text" if layout_syntax.STATUS in child.meta:
                    bold = context.format.bold
                    context.format.bold = True
                    self._run(context, child.content)
                    context.format.bold = bold
                case "text":
                    self._run(context, child.content)
                case "softbreak":
                    self._run(context, " ")
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
                        self.picture(context.paragraph, child, line)
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
        if context.target.tag == w("hyperlink"):
            etree.SubElement(r_pr, w("rStyle")).set(w("val"), self.style_id(word.STYLES.hyperlink))
        if code:
            fonts = etree.SubElement(r_pr, w("rFonts"))
            for attribute in ("ascii", "hAnsi", "cs", "eastAsia"):
                fonts.set(w(attribute), word.INLINE_CODE_FONT)
        if context.format.bold and not context.plain_bold:
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


def _reencode(content: bytes) -> bytes:
    """The picture saved again by Pillow: JPEG with a JFIF header, everything else as PNG."""
    with Image.open(io.BytesIO(content)) as picture:
        buffer = io.BytesIO()
        if picture.format == "JPEG":
            picture.save(buffer, "JPEG", quality=92, dpi=picture.info.get("dpi", (96, 96)))
        else:
            picture.save(buffer, "PNG")
        return buffer.getvalue()


def _only_images(children: list[Token]) -> bool:
    images = [c for c in children if c.type == "image"]
    rest = [c for c in children if c.type != "image"]
    return bool(images) and all(
        c.type == "softbreak" or (c.type == "text" and not c.content.strip()) for c in rest
    )


def _only_strong(children: list[Token]) -> bool:
    children = [c for c in children if not (c.type == "text" and not c.content)]
    if (
        len(children) < 3
        or children[0].type != "strong_open"
        or children[-1].type != "strong_close"
    ):
        return False
    depth = 0
    for n, child in enumerate(children):
        if child.type == "strong_open":
            depth += 1
        elif child.type == "strong_close":
            depth -= 1
            if depth == 0 and n != len(children) - 1:
                return False
    return True


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


def _strip_caption_prefix(inline: Token) -> Token:
    children = list(inline.children or [])
    if children and children[0].type == "text":
        first = children[0]
        content = first.content.split(":", 1)[1].lstrip() if ":" in first.content else first.content
        children[0] = first.copy(content=content)
    return inline.copy(children=children)


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
