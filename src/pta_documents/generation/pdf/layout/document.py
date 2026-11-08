"""The pages: reportlab's document template on the type area of the PTA Word template.

One frame per page, as large as the type area of the template's ``w:sectPr`` (portrait
3.50/2.00/2.20/2.20 cm, landscape 4.20/2.50/2.20/2.20 cm, top/bottom/left/right). Footnotes are
drawn at the foot of their page, above the bottom margin, with a rule over them. Page frames
(header, footer, cover — E05-S03) come in through ``decorate``, called for every page once the
number of pages is known (DocLibs ``Decorate``); ``underlay`` draws behind the content of every
page as it begins (the watermark of ``kennzeichnung: entwurf``, E12-S03). The first page may start
lower than the others (``first_top_pt``: the cover, whose header reaches below the top margin in
Word).
"""

from __future__ import annotations

import io
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Final

from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Spacer

from pta_documents.design.word_styles import PageSetup
from pta_documents.generation.pdf.layout.flowables import PtaParagraph
from pta_documents.generation.pdf.layout.story import Story
from pta_documents.generation.pdf.metadata import PRODUCER, PdfInfo

Decorate = Callable[[Canvas, int, int], None]
"""Draws the frame of page ``n`` (1-based) of ``count`` pages on the canvas."""

RULE_PT: Final = 0.5


@dataclass(frozen=True)
class RenderedPdf:
    content: bytes
    pages: int
    heading_pages: Mapping[str, int] = field(default_factory=dict[str, int])
    """The page (1-based) of every bookmarked heading, by its anchor (table of contents)."""


class _Template(BaseDocTemplate):
    def __init__(
        self,
        output: io.BytesIO,
        story: Story,
        info: PdfInfo,
        decorate: Decorate | None,
        page_count: int,
        first_top_pt: float | None = None,
        underlay: Decorate | None = None,
    ) -> None:
        page = story.context.page
        super().__init__(
            output,
            pagesize=(page.width_pt, page.height_pt),
            leftMargin=page.left_pt,
            rightMargin=page.right_pt,
            topMargin=page.top_pt,
            bottomMargin=page.bottom_pt,
            title=info.title or "",
            author=info.author or "",
            subject=info.subject or "",
            creator=PRODUCER,
            producer=PRODUCER,
            lang=info.language_tag,
            invariant=1,  # fixed dates and ids: the same input gives the same bytes
            initialFontName=story.context.fonts.text,
            initialFontSize=10,
            initialLeading=12,
            pageCompression=1,
        )
        self.story = story
        templates = [
            PageTemplate(
                "body",
                [_frame(page, page.top_pt)],
                onPage=self._page_start,
                onPageEnd=self._page_end,
            )
        ]
        if first_top_pt is not None:
            first = PageTemplate(
                "first",
                [_frame(page, first_top_pt)],
                onPage=self._page_start,
                onPageEnd=self._page_end,
                autoNextPageTemplate="body",
            )
            templates.insert(0, first)
        self.addPageTemplates(templates)
        self.decorate = decorate
        self.underlay = underlay
        self.page_count = page_count
        self.heading_pages: dict[str, int] = {}

    def afterFlowable(self, flowable: Any) -> None:
        if isinstance(flowable, PtaParagraph) and flowable.outline and flowable.anchor:
            self.heading_pages.setdefault(flowable.anchor, self.page)

    def handle_frameBegin(self, resume: int = 0, pageTopFlowables: Any = None) -> None:
        # The footnotes of the last page raised the frame's bottom: a new page starts full.
        frame: Any = self.frame
        frame._geom()
        super().handle_frameBegin(resume, pageTopFlowables)

    def _page_start(self, canvas: Canvas, _doc: Any) -> None:
        if self.underlay is not None:
            canvas.saveState()
            canvas.setFont(self.story.context.fonts.text, 10)
            self.underlay(canvas, self.page, self.page_count)
            canvas.restoreState()

    def _page_end(self, canvas: Canvas, _doc: Any) -> None:
        self._draw_footnotes(canvas)
        canvas.showOutline()
        if self.decorate is not None:
            # A frame drawn without setting a font must not fall back on Helvetica.
            canvas.setFont(self.story.context.fonts.text, 10)
            self.decorate(canvas, self.page, self.page_count)

    def _draw_footnotes(self, canvas: Canvas) -> None:
        area = self.story.footnotes
        notes = area.take()
        if not notes:
            return
        page = self.story.context.page
        width = page.text_width_pt
        heights = [n.wrap(width, page.text_height_pt)[1] for n in notes]
        y = page.bottom_pt + sum(heights) + sum(float(n.getSpaceBefore()) for n in notes[1:])
        canvas.saveState()
        canvas.setStrokeColor(area.rule_color)
        canvas.setLineWidth(RULE_PT)
        rule_y = y + area.gap / 2
        canvas.line(page.left_pt, rule_y, page.left_pt + area.rule_width, rule_y)
        canvas.restoreState()
        for n, (note, height) in enumerate(zip(notes, heights, strict=True)):
            if n:
                y -= float(note.getSpaceBefore())
            y -= height
            note.drawOn(canvas, page.left_pt, y)


def _frame(page: PageSetup, top_pt: float) -> Frame:
    """The frame of the type area, starting ``top_pt`` below the top of the page."""
    return Frame(
        page.left_pt,
        page.bottom_pt,
        page.text_width_pt,
        page.height_pt - top_pt - page.bottom_pt,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="body",
        # Space after a paragraph and space before the next add up, as in Word.
        overlapAttachedSpace=0,
    )


def render(
    story: Story,
    info: PdfInfo | None = None,
    decorate: Decorate | None = None,
    page_count: int = 0,
    first_top_pt: float | None = None,
    underlay: Decorate | None = None,
) -> RenderedPdf:
    """Lay ``story`` out on pages and write the PDF (not yet PDF/A: the generator passes it
    through ``pdfa.to_pdfa``). The bookmarks show when the PDF opens; ``decorate`` draws every
    page's frame with ``page_count`` as the number of pages (``layout`` finds it with a first
    pass); ``first_top_pt`` lets the first page start lower than the top margin; ``underlay``
    draws behind the content of every page."""
    output = io.BytesIO()
    template = _Template(
        output, story, info or PdfInfo(), decorate, page_count, first_top_pt, underlay
    )
    # An empty document is one empty page, as in Word.
    template.build(list(story.flowables) or [Spacer(0, 0)])
    return RenderedPdf(output.getvalue(), template.page, dict(template.heading_pages))
