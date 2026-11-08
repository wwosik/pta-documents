"""Markdown to PDF/A-2b in the PTA design: port of DocLibs ``PdfGenerator.cs``.

The steps: front matter (the keys of the DOCX generator), parsing and ``layout_syntax.check``,
the fonts (``design.fonts.resolve``), the layout (``BODY_LAYOUT``), drawing with reportlab
(``renderer.render``) and PDF/A-2b with pikepdf (``pdfa.to_pdfa``).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import replace
from typing import BinaryIO, Final

from pta_documents.design import fonts as design_fonts
from pta_documents.design.fonts import FontFace
from pta_documents.design.variants import TEXTS, Language, WordVariant
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import layout_syntax
from pta_documents.generation.common.result import GenerationResult, Notes
from pta_documents.generation.pdf import simple_layout
from pta_documents.generation.pdf.body import BodyLayout, BodySource
from pta_documents.generation.pdf.fonts import PdfFonts
from pta_documents.generation.pdf.metadata import PdfInfo
from pta_documents.generation.pdf.options import PdfOptions
from pta_documents.generation.pdf.pdfa import to_pdfa
from pta_documents.generation.pdf.renderer import render
from pta_documents.markdown.document import MarkdownDocument, MetadataKeys
from pta_documents.markdown.front_matter import FrontMatter, Keys
from pta_documents.markdown.parser import parse

FORMAT: Final = DocumentFormat.PDF
VALID_KEYS: Final = (
    Keys.TEMPLATE,
    Keys.TITLE,
    Keys.SUBTITLE,
    Keys.AUTHOR,
    Keys.LOCATION,
    Keys.DATE,
    Keys.COMPANY,
    Keys.LANGUAGE,
    Keys.CHECK,
    Keys.TOC,
)
BODY_LAYOUT: Final[BodyLayout] = simple_layout.lay_out
"""The layout engine; E05-S02 puts its own here."""
MISSING_EFFECT: Final = "shows as '?' in the PDF"


class PdfGenerator:
    def generate(
        self,
        document: MarkdownDocument,
        output: BinaryIO,
        options: PdfOptions | None = None,
    ) -> GenerationResult:
        """Write ``document`` as a PDF/A-2b to ``output``.

        Returns the notes on what had to be worked around and the number of pages. Raises
        ``DocumentConversionError`` for mistakes in the Markdown or its front matter.
        """
        notes = Notes()
        front = FrontMatter.read(document.text, FORMAT)
        front.check_keys(VALID_KEYS, allow_status=True)
        front.status_labels()  # raises for an unknown category or a label in two
        options = apply_front_matter(front, options or PdfOptions())
        title = front.get(Keys.TITLE) or document.metadata.get(MetadataKeys.TITLE)
        author = front.get(Keys.AUTHOR) or document.metadata.get(MetadataKeys.AUTHOR)
        if options.variant.has_cover and not title:
            raise DocumentConversionError(
                FORMAT,
                f"The template '{options.variant.value}' has a cover page and needs a title: "
                f"add '{Keys.TITLE}: …' to the front matter.",
            )
        tokens = parse(front.body)
        layout_syntax.check(tokens, FORMAT, front.body_line)

        fonts = PdfFonts(design_fonts.resolve(system_fonts=options.system_fonts))
        notes.characters(
            front.body,
            front.body_line,
            lambda c: fonts.has_glyph(c, FontFace.REGULAR) and fonts.has_glyph(c, FontFace.BOLD),
            lambda c: fonts.has_glyph(c, FontFace.MONO),
            MISSING_EFFECT,
        )
        source = BodySource(tokens, document, front, options, TEXTS[options.language], notes)
        layout = BODY_LAYOUT(source, fonts)
        info = PdfInfo(
            title=title,
            author=author,
            subject=front.get(Keys.SUBTITLE),
            language=options.language,
            created=options.created or dt.datetime.now(dt.UTC),
        )
        output.write(to_pdfa(render(layout, fonts, info), info))
        return GenerationResult(notes.to_tuple(), pages=len(layout.pages))


def apply_front_matter(front: FrontMatter, options: PdfOptions) -> PdfOptions:
    if (value := front.get(Keys.TEMPLATE)) is not None:
        try:
            variant = WordVariant.parse(value)
        except DocumentConversionError as error:  # parse() names DOCX, the Word templates
            raise DocumentConversionError(FORMAT, error.reason) from None
        options = replace(options, variant=variant)
    if (value := front.get(Keys.LANGUAGE)) is not None:
        options = replace(options, language=Language.parse(value, FORMAT))
    if (value := front.date()) is not None:
        options = replace(options, date=value)
    if (value := front.get(Keys.COMPANY)) is not None:
        options = replace(options, company=value)
    if (value := front.boolean(Keys.TOC)) is not None:
        options = replace(options, toc=value)
    return options
