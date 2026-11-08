"""The PTA page frame of the PDF (E05-S03): cover, table of contents, header and footer.

In place of DocLibs ``LayoutEngine.Cover`` and ``Decorate``: what Word shows around the text of a
PTA document, drawn from the template (``design.word_frame``) on every page once the number of
pages is known.

- **Header** (every page but the cover): title bold in PTA blue and the subtitle, in the width of
  the header table, too long texts cut with „…"; the logo top right; the gradient rule.
- **Footer**: the gradient rule, below it the cells of the footer table — company, „Stand:
  TT.MM.JJJJ", „Seite n | m" (``n`` and ``m`` count every page, the cover included, as Word's
  ``PAGE`` and ``NUMPAGES``).
- **Cover** (``hoch``, ``quer``): page 1 has only the logo and the rule of the template's first
  header and no footer; title, subtitle and „Autor, Ort, Datum" in the styles of the template
  start where Word starts them (below the first header), then a page break.
- **Marking** (``kennzeichnung:``, E12-S03): the text of ``design.word.MARKING`` right-aligned
  below the rule of every header (``word_frame.marking_area``), the cover included, and once more
  below „Autor, Ort, Datum" on the cover; ``entwurf`` also draws the watermark „ENTWURF" behind
  the content of every page (``Watermark``, as ``design.word.WATERMARK``).
- **Table of contents** (``inhaltsverzeichnis: ja``): after the cover „Inhalt" and the headings of
  levels 1 and 2 (as ``TOC \\o "1-2"``) with number, text, page and a link to the heading, then a
  page break.

The layout runs until the page count and the pages of the headings no longer change (two passes
normally, ``MAX_PASSES`` at most): the frame needs the count, the contents the pages.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, Final
from xml.sax.saxutils import escape

from markdown_it.token import Token
from reportlab.lib import colors as rl_colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Flowable, PageBreak

from pta_documents.design import logos, word, word_frame
from pta_documents.design.fonts import FontFace
from pta_documents.design.logos import Logo
from pta_documents.design.variants import Marking
from pta_documents.design.word_frame import (
    Alignment,
    Band,
    FrameField,
    FrameParagraph,
    FrameRule,
    FrameTable,
    PageFrame,
    VerticalAlignment,
)
from pta_documents.generation.common.result import Notes
from pta_documents.generation.pdf.layout import LayoutSettings, build_story, prepare, render
from pta_documents.generation.pdf.layout.document import RenderedPdf
from pta_documents.generation.pdf.layout.flowables import Outline, PtaParagraph
from pta_documents.generation.pdf.layout.fonts import PdfFonts
from pta_documents.generation.pdf.layout.story import LayoutContext
from pta_documents.generation.pdf.layout.styles import BlockStyle, color
from pta_documents.generation.pdf.metadata import PdfInfo
from pta_documents.markdown.document import MarkdownDocument

ELLIPSIS: Final = "…"
"""What ends a header text that is too long for the header table (DocLibs ``Fit``)."""
LOGO_FORM: Final = "PTALogo"
"""The form XObject of the logo: embedded once, shown on every page."""
TOC_LEVELS: Final = (1, 2)
"""The heading levels in the table of contents, as ``TOC \\o "1-2"``."""
TOC_LEADER_LEVELS: Final = (2,)
"""Levels whose page number follows a dotted leader (the tab of „Verzeichnis 2")."""
TOC_PAGE_DIGITS: Final = "0000"
"""The room kept right of a contents entry for its page number."""
TOC_GAP_PT: Final = 4.0
"""Room between the text of a contents entry, the dots and the page number."""
LEADER: Final = "."
FILL_EVEN_ODD: Final = 0
FILL_NON_ZERO: Final = 1
"""reportlab's ``fillMode`` values (``reportlab.pdfgen.canvas``; its stubs lack them)."""
MAX_PASSES: Final = 4


@dataclass(frozen=True)
class FrameInfo:
    """What the frame shows: from the front matter (and the metadata), as in the DOCX."""

    title: str | None = None
    subtitle: str | None = None
    author: str | None = None
    location: str | None = None
    date: dt.date | None = None
    """``datum:``: on the cover (only if given)."""
    as_of: dt.date | None = None
    """The date of „Stand:" in the footer: ``datum`` or the day of creation."""
    company: str | None = None
    """``firma:`` in place of „PTA IT-Beratung"."""
    toc: bool = False
    marking: Marking = Marking.NONE
    """``kennzeichnung:``: the text below the rule of the header and on the cover; ``entwurf``
    adds the watermark."""


def format_date(date: dt.date) -> str:
    """TT.MM.JJJJ, as the DOCX generator writes it."""
    return date.strftime("%d.%m.%Y")


def lay_out(
    tokens: list[Token],
    document: MarkdownDocument,
    settings: LayoutSettings,
    frame_info: FrameInfo,
    notes: Notes | None = None,
    info: PdfInfo | None = None,
) -> RenderedPdf:
    """The PDF of the body ``tokens`` in the PTA page frame of ``settings.variant``."""
    context = prepare(settings)
    frame = word_frame.read(settings.variant, context.design)
    natural = context.fonts.line_height()
    first_top = None
    if frame.first is not None:
        first_top = word_frame.body_top(frame, 1, natural)
    page_count = 0
    heading_pages: Mapping[str, int] = {}
    result: RenderedPdf | None = None
    for _ in range(MAX_PASSES):
        story = build_story(tokens, document, context, notes)
        front = front_matter(context, frame_info, story.outline, heading_pages)
        story = replace(story, flowables=[*front, *story.flowables])
        decorator = PageDecorator(frame, context, frame_info)
        underlay = None
        if frame_info.marking is Marking.DRAFT:
            underlay = Watermark(frame, context.fonts, context.texts.draft)
        result = render(story, info, decorator, page_count, first_top, underlay)
        if result.pages == page_count and result.heading_pages == heading_pages:
            break
        page_count, heading_pages = result.pages, result.heading_pages
    assert result is not None
    return result


# ---------------------------------------------------------------------------- cover and contents


def front_matter(
    context: LayoutContext,
    frame_info: FrameInfo,
    outline: Sequence[Outline],
    heading_pages: Mapping[str, int],
) -> list[Flowable]:
    """The cover (variants with one) and the table of contents (``toc``), each ending with a
    page break."""
    result: list[Flowable] = []
    if context.settings.variant.has_cover:
        result.extend(cover(context, frame_info))
    if frame_info.toc:
        result.extend(contents(context, outline, heading_pages))
    return result


def cover(context: LayoutContext, frame_info: FrameInfo) -> list[Flowable]:
    """„Titel", „Untertitel" and „Autor" with „Autor, Ort, Datum", as ``write_cover`` of the
    DOCX generator."""
    s = word.STYLES
    styles = context.styles
    result: list[Flowable] = [_plain(styles.block(s.title), frame_info.title or "")]
    if frame_info.subtitle:
        result.append(_plain(styles.block(s.subtitle), frame_info.subtitle))
    date = format_date(frame_info.date) if frame_info.date else None
    byline = ", ".join(p for p in (frame_info.author, frame_info.location, date) if p)
    if byline:
        result.append(_plain(styles.block(s.author), byline))
    if frame_info.marking is not Marking.NONE:
        block = styles.block(s.author)
        style = ParagraphStyle(
            f"{block.style.name} marking", block.style, textColor=color(word.MARKING.color)
        )
        text = context.texts.marking(frame_info.marking)
        result.append(PtaParagraph(escape(text.upper() if word.MARKING.caps else text), style))
    result.append(PageBreak())
    return result


def contents(
    context: LayoutContext, outline: Sequence[Outline], heading_pages: Mapping[str, int]
) -> list[Flowable]:
    """„Inhalt" in „Zwischenüberschrift" and an entry per heading of ``TOC_LEVELS``."""
    styles = context.styles
    result: list[Flowable] = [_plain(styles.sub_heading, context.texts.contents)]
    for entry in outline:
        if entry.heading not in TOC_LEVELS or entry.anchor is None:
            continue
        block = styles.block(word.STYLES.toc[entry.heading - 1])
        page = heading_pages.get(entry.anchor)
        result.append(
            ContentsEntry(
                entry.number,
                escape(entry.text),
                "" if page is None else str(page),
                entry.anchor,
                block,
                context,
                leader=entry.heading in TOC_LEADER_LEVELS,
            )
        )
    result.append(PageBreak())
    return result


def _plain(block: BlockStyle, text: str) -> PtaParagraph:
    """A paragraph of plain ``text`` in ``block`` (bold and capitals as the style says)."""
    markup = escape(text.upper() if block.caps else text)
    if block.bold:
        markup = f"<b>{markup}</b>"
    if block.italic:
        markup = f"<i>{markup}</i>"
    return PtaParagraph(markup, block.style)


class ContentsEntry(Flowable):
    """An entry of the table of contents: the number in the hanging indent, the text, the page
    number right (after dots on ``leader`` levels); the whole entry links to the heading."""

    def __init__(
        self,
        number: str,
        markup: str,
        page: str,
        anchor: str,
        block: BlockStyle,
        context: LayoutContext,
        leader: bool,
    ) -> None:
        super().__init__()
        self.number = number
        self.page = page
        self.anchor = anchor
        self.leader = leader
        self.fonts = context.fonts
        style = block.style
        self.size = float(style.fontSize)
        self.text_x = float(style.leftIndent)
        self.number_x = self.text_x + float(style.firstLineIndent)
        self.page_room = self.fonts.width(TOC_PAGE_DIGITS, FontFace.REGULAR, self.size)
        self.color = style.textColor
        self.style = ParagraphStyle(
            f"{style.name} entry",
            style,
            firstLineIndent=0,
            rightIndent=self.page_room + TOC_GAP_PT,
        )
        self.paragraph = PtaParagraph(markup, self.style)
        self.spaceBefore = float(style.spaceBefore)
        self.spaceAfter = float(style.spaceAfter)

    def wrap(self, aW: float, aH: float) -> tuple[float, float]:
        self.width = aW
        _, height = self.paragraph.wrap(aW, aH)
        self.height = height
        return aW, height

    def split(self, availWidth: float, availHeight: float) -> list[Flowable]:
        return []

    def draw(self) -> None:
        canvas: Any = self.canv
        self.paragraph.drawOn(canvas, 0, 0)
        first = self.paragraph.first_baseline()
        lines: Any = getattr(self.paragraph, "blPara", None)
        count = len(lines.lines) if lines is not None and lines.lines else 1
        last = first - (count - 1) * float(self.style.leading)
        regular = self.fonts.name(FontFace.REGULAR)
        canvas.saveState()
        canvas.setFillColor(self.color)
        canvas.setFont(regular, self.size)
        if self.number:
            canvas.drawString(self.number_x, first, self.number)
        if self.page:
            canvas.drawRightString(self.width, last, self.page)
        if self.leader:
            start = self.text_x + self._last_line_width(lines) + TOC_GAP_PT
            end = self.width - self.page_room - TOC_GAP_PT
            dot = pdfmetrics.stringWidth(LEADER, regular, self.size)
            dots = int((end - start) // dot) if dot > 0 else 0
            if dots > 0:
                canvas.drawRightString(end, last, LEADER * dots)
        canvas.restoreState()
        canvas.linkRect("", self.anchor, (0, 0, self.width, self.height), relative=1)

    def _last_line_width(self, lines: Any) -> float:
        available = self.width - self.text_x - float(self.style.rightIndent)
        if lines is None or not lines.lines:
            return 0.0
        last = lines.lines[-1]
        extra = last[0] if isinstance(last, tuple) else getattr(last, "extraSpace", 0.0)
        return max(0.0, available - float(extra))  # type: ignore[arg-type]


# ---------------------------------------------------------------------------- header and footer


class PageDecorator:
    """Draws header and footer of a page (``layout.Decorate``)."""

    def __init__(self, frame: PageFrame, context: LayoutContext, frame_info: FrameInfo) -> None:
        self.frame = frame
        self.context = context
        self.fonts = context.fonts
        self.natural = context.fonts.line_height()
        texts = context.texts
        as_of = frame_info.as_of or frame_info.date or dt.date.today()
        self.texts: dict[FrameField, str | None] = {
            FrameField.TITLE: frame_info.title or "",
            FrameField.SUBTITLE: frame_info.subtitle,
            FrameField.COMPANY: frame_info.company or word.COMPANY_PLACEHOLDER,
            FrameField.AS_OF: f"{texts.as_of}: {format_date(as_of)}",
            FrameField.NONE: "",
        }
        self.page_label = texts.page
        self.marking = texts.marking(frame_info.marking)
        header = context.design.paragraph(word.STYLES.header)
        self.marking_format = replace(
            header,
            size_pt=word.MARKING.size_pt,
            color=word.MARKING.color,
            space_before_pt=0.0,
            space_after_pt=0.0,
        )

    def __call__(self, canvas: Canvas, page: int, count: int) -> None:
        kind = self.frame.kind(page)
        height = self.frame.page.height_pt
        canvas.saveState()
        for band in (kind.header, kind.footer):
            for rule in band.rules:
                self._rule(canvas, rule, height)
            for box in band.pictures:
                self._logo(canvas, box, height)
        self._band(canvas, kind.header, word_frame.header_top(self.frame), page, count)
        footer_top = word_frame.footer_bottom(self.frame) - self._band_height(kind.footer)
        self._band(canvas, kind.footer, footer_top, page, count)
        if self.marking:
            self._marking(canvas)
        canvas.restoreState()

    def _marking(self, canvas: Canvas) -> None:
        """The marking right-aligned in ``word_frame.marking_area``, at the foot of its line
        as Word sets the paragraph of its text box."""
        area = word_frame.marking_area(self.frame)
        fmt = self.marking_format
        text = self.marking.upper() if word.MARKING.caps else self.marking
        font = self.fonts.name(FontFace.REGULAR)
        _, descent = pdfmetrics.getAscentDescent(font, fmt.size_pt)
        baseline = area.y_pt + fmt.leading(self.natural) + descent
        canvas.setFont(font, fmt.size_pt)
        canvas.setFillColor(color(word.MARKING.color))
        canvas.drawRightString(
            area.x_pt + area.width_pt,
            self.frame.page.height_pt - baseline,
            fit(self.fonts.shown(text), font, fmt.size_pt, area.width_pt),
        )

    # -------------------------------------------------------------------- drawings

    def _rule(self, canvas: Canvas, rule: FrameRule, page_height: float) -> None:
        """A gradient rule: the transparent end is mixed with the white page."""
        y = page_height - rule.y_pt
        stops = [_on_white(s.color, s.alpha) for s in rule.stops]
        positions = [s.position for s in rule.stops]
        canvas.saveState()
        path = canvas.beginPath()
        path.rect(rule.x_pt, y - rule.stroke_pt / 2, rule.width_pt, rule.stroke_pt)
        canvas.clipPath(path, stroke=0, fill=0)
        canvas.linearGradient(
            rule.x_pt, y, rule.x_pt + rule.width_pt, y, stops, positions, extend=False
        )
        canvas.restoreState()

    def _logo(self, canvas: Canvas, box: word_frame.Box, page_height: float) -> None:
        width, height = logos.size(Logo.WORD)
        if not canvas.hasForm(LOGO_FORM):
            _define_logo(canvas, width, height)
        canvas.saveState()
        canvas.translate(box.x_pt, page_height - box.y_pt - box.height_pt)
        canvas.scale(box.width_pt / width, box.height_pt / height)
        canvas.doForm(LOGO_FORM)
        canvas.restoreState()

    # -------------------------------------------------------------------- texts

    def _shown(self, paragraph: FrameParagraph) -> bool:
        return paragraph.field is not FrameField.SUBTITLE or bool(self.texts[FrameField.SUBTITLE])

    def _height(self, paragraph: FrameParagraph) -> float:
        return paragraph.height(self.natural) if self._shown(paragraph) else 0.0

    def _row_height(self, row: word_frame.FrameRow) -> float:
        visible = replace(
            row,
            cells=tuple(
                replace(c, paragraphs=tuple(p for p in c.paragraphs if self._shown(p)))
                for c in row.cells
            ),
        )
        return word_frame.row_height(visible, self.natural)

    def _band_height(self, band: Band) -> float:
        total = 0.0
        for block in band.blocks:
            if isinstance(block, FrameTable):
                total += sum(self._row_height(r) for r in block.rows)
            else:
                total += self._height(block)
        return total

    def _band(self, canvas: Canvas, band: Band, top: float, page: int, count: int) -> None:
        y = top
        for block in band.blocks:
            if isinstance(block, FrameTable):
                for row in block.rows:
                    height = self._row_height(row)
                    x = block.x_pt
                    for cell in row.cells:
                        paragraphs = [p for p in cell.paragraphs if self._shown(p)]
                        content = sum(p.height(self.natural) for p in paragraphs)
                        offset = 0.0
                        if cell.v_align is VerticalAlignment.CENTER:
                            offset = (height - content) / 2
                        elif cell.v_align is VerticalAlignment.BOTTOM:
                            offset = height - content
                        line_top = y + offset
                        for p in paragraphs:
                            self._text(canvas, p, x, cell.width_pt, line_top, page, count)
                            line_top += p.height(self.natural)
                        x += cell.width_pt
                    y += height
            else:
                if self._shown(block):
                    width = self.frame.page.text_width_pt
                    self._text(canvas, block, self.frame.page.left_pt, width, y, page, count)
                y += self._height(block)

    def _text(
        self,
        canvas: Canvas,
        paragraph: FrameParagraph,
        x: float,
        width: float,
        top: float,
        page: int,
        count: int,
    ) -> None:
        if paragraph.field is FrameField.PAGE:
            text = f"{self.page_label} {page} | {count}"
        else:
            text = self.texts[paragraph.field] or ""
        if not text:
            return
        fmt = paragraph.format
        font = self.fonts.name(FontFace.BOLD if fmt.bold else FontFace.REGULAR)
        size = fmt.size_pt
        text = fit(self.fonts.shown(text), font, size, width)
        _, descent = pdfmetrics.getAscentDescent(font, size)
        # Word sets the text at the foot of its line: extra line height goes above it.
        baseline = top + fmt.space_before_pt + fmt.leading(self.natural) + descent
        y = self.frame.page.height_pt - baseline
        canvas.setFont(font, size)
        canvas.setFillColor(color(fmt.color))
        match paragraph.align:
            case Alignment.CENTER:
                canvas.drawCentredString(x + width / 2, y, text)
            case Alignment.RIGHT:
                canvas.drawRightString(x + width, y, text)
            case Alignment.LEFT:
                canvas.drawString(x, y, text)


class Watermark:
    """Draws the watermark of ``kennzeichnung: entwurf`` behind the content of a page: the text
    turned by ``word.WATERMARK.angle`` over the middle of the type area, as large as its
    diagonal allows (``word.watermark_size``), in Akzent 5 at half opacity — mixed with the white
    page instead of a soft mask, which looks the same behind the content and keeps PDF/A free of
    transparency."""

    def __init__(self, frame: PageFrame, fonts: PdfFonts, text: str) -> None:
        self.frame = frame
        self.font = fonts.name(FontFace.REGULAR)
        self.text = fonts.shown(text)

    def __call__(self, canvas: Canvas, page: int, count: int) -> None:
        style = word.WATERMARK
        setup = self.frame.page
        width_em = pdfmetrics.stringWidth(self.text, self.font, 1)
        size = word.watermark_size(width_em, setup.text_width_pt, setup.text_height_pt)
        x = setup.left_pt + setup.text_width_pt / 2
        y = setup.height_pt - setup.top_pt - setup.text_height_pt / 2
        canvas.saveState()
        canvas.translate(x, y)
        canvas.rotate(style.angle)
        canvas.setFont(self.font, size)
        canvas.setFillColor(_on_white(style.color, style.opacity))
        canvas.drawCentredString(0, -style.cap_height_em * size / 2, self.text)
        canvas.restoreState()


def fit(text: str, font: str, size: float, width: float) -> str:
    """``text``, cut with „…" so that it is at most ``width`` wide (DocLibs ``Fit``)."""
    if pdfmetrics.stringWidth(text, font, size) <= width:
        return text
    low, high = 0, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        candidate = text[:middle].rstrip() + ELLIPSIS
        if pdfmetrics.stringWidth(candidate, font, size) <= width:
            low = middle
        else:
            high = middle - 1
    return text[:low].rstrip() + ELLIPSIS


def _on_white(value: str, alpha: float) -> rl_colors.Color:
    """``value`` with opacity ``alpha`` over white: the page is white, so no soft mask."""
    base = color(value)
    mix: Any = rl_colors.linearlyInterpolatedColor
    return mix(rl_colors.white, base, 0.0, 1.0, alpha)


def _define_logo(canvas: Canvas, width: float, height: float) -> None:
    """The logo as a form XObject in the units of its ``viewBox`` (y upwards)."""
    canvas.beginForm(LOGO_FORM, 0, 0, width, height)
    for shape in logos.shapes(Logo.WORD):
        path = canvas.beginPath()
        for command, n in shape.segments:
            match command:
                case "M":
                    path.moveTo(n[0], height - n[1])
                case "L":
                    path.lineTo(n[0], height - n[1])
                case "C":
                    path.curveTo(n[0], height - n[1], n[2], height - n[3], n[4], height - n[5])
                case _:
                    path.close()
        canvas.setFillColor(color(shape.fill))
        canvas.drawPath(
            path, stroke=0, fill=1, fillMode=FILL_EVEN_ODD if shape.even_odd else FILL_NON_ZERO
        )
    canvas.endForm()
