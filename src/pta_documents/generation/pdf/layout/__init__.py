"""The PDF layout engine (E05-S02): Markdown tokens → pages in the PTA Word design.

Port of DocLibs ``MarkdownParser`` and ``LayoutEngine`` onto reportlab's platypus. The PDF
generator (``generator.PdfGenerator``) calls ``layout``::

    tokens = create_parser().parse(front.body)
    layout_syntax.check(tokens, DocumentFormat.PDF, front.body_line, today)
    document = generated_images.add_generated(document, tokens, DocumentFormat.PDF, offset)
    typeset(tokens, language)  # if typography is on
    settings = LayoutSettings(variant, language, fonts, line_offset=front.body_line, ...)
    pdf = layout(tokens, document, settings, notes, PdfInfo(title, author, ...))
    output.write(to_pdfa(pdf.content, info))

``build_story`` and ``render`` are the two halves of ``layout`` for callers that add flowables
of their own (cover, table of contents: E05-S03). Needs the extra ``pdf`` (reportlab, fontTools).
"""

from __future__ import annotations

from markdown_it.token import Token

from pta_documents.generation.common.result import Notes
from pta_documents.generation.pdf.layout.document import Decorate, RenderedPdf, render
from pta_documents.generation.pdf.layout.fonts import PdfFonts, register
from pta_documents.generation.pdf.layout.story import (
    LayoutContext,
    LayoutSettings,
    Story,
    build_story,
    prepare,
)
from pta_documents.generation.pdf.metadata import PdfInfo
from pta_documents.markdown.document import MarkdownDocument


def layout(
    tokens: list[Token],
    document: MarkdownDocument,
    settings: LayoutSettings,
    notes: Notes | None = None,
    info: PdfInfo | None = None,
    decorate: Decorate | None = None,
) -> RenderedPdf:
    """The PDF of the body ``tokens``. With ``decorate``, the pages are laid out twice: first to
    count them, then with every page's frame drawn knowing the count."""
    context = prepare(settings)
    page_count = 0
    if decorate is not None:
        page_count = render(build_story(tokens, document, context, Notes()), info).pages
    story = build_story(tokens, document, context, notes)
    return render(story, info, decorate, page_count)


__all__ = [
    "Decorate",
    "LayoutContext",
    "LayoutSettings",
    "PdfFonts",
    "PdfInfo",
    "RenderedPdf",
    "Story",
    "build_story",
    "layout",
    "prepare",
    "register",
    "render",
]
