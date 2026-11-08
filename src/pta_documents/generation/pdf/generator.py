"""Markdown to PDF/A-2b in the PTA design: port of DocLibs ``PdfGenerator.cs``.

The steps: front matter (the keys of the DOCX generator), parsing, ``layout_syntax.check``,
generated images (QR codes) and the typography, the fonts (``design.fonts.resolve``), the
layout engine of E05-S02 in the page frame of E05-S03 (``frame.lay_out``: reportlab platypus on
the styles and the type area of the PTA Word template, with cover, table of contents, header and
footer) and PDF/A-2b with pikepdf (``pdfa.to_pdfa``).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import replace
from typing import BinaryIO, Final

from pta_documents.design import fonts as design_fonts
from pta_documents.design.fonts import FontFace
from pta_documents.design.variants import Language, Marking, WordVariant
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import generated_images, layout_syntax, schedule
from pta_documents.generation.common.result import GenerationResult, Notes
from pta_documents.generation.pdf.frame import FrameInfo, lay_out
from pta_documents.generation.pdf.layout import LayoutSettings
from pta_documents.generation.pdf.layout.fonts import ALIASES, question_mark
from pta_documents.generation.pdf.metadata import PdfInfo
from pta_documents.generation.pdf.options import PdfOptions
from pta_documents.generation.pdf.pdfa import to_pdfa
from pta_documents.markdown.document import MarkdownDocument, MetadataKeys
from pta_documents.markdown.front_matter import FrontMatter, Keys
from pta_documents.markdown.parser import create_parser
from pta_documents.markdown.typography import typeset, typeset_text

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
    Keys.TYPOGRAPHY,
    Keys.HIGHLIGHT,
    Keys.CHECK,
    Keys.TOC,
    Keys.MARKING,
)
MISSING_EFFECT: Final = "shows as '?' in the PDF"
REPLACED_EFFECT: Final = "is replaced in the PDF (replace_unsupported)"


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
        labels = front.status_labels()  # raises for an unknown category or a label in two
        options = apply_front_matter(front, options or PdfOptions())
        title = front.get(Keys.TITLE) or document.metadata.get(MetadataKeys.TITLE)
        author = front.get(Keys.AUTHOR) or document.metadata.get(MetadataKeys.AUTHOR)
        if options.variant.has_cover and not title:
            raise DocumentConversionError(
                FORMAT,
                f"The template '{options.variant.value}' has a cover page and needs a title: "
                f"add '{Keys.TITLE}: …' to the front matter.",
            )
        tokens = create_parser().parse(front.body)
        today = schedule.reference_day(options.date)
        layout_syntax.check(tokens, FORMAT, front.body_line, today)
        document = generated_images.add_generated(document, tokens, FORMAT, front.body_line, notes)
        if options.typography:
            typeset(tokens, options.language)
            # Label cells are typeset like any text, so the labels must be too.
            labels = {typeset_text(k, options.language): v for k, v in labels.items()}

        fonts = design_fonts.resolve(system_fonts=options.system_fonts)

        def shown(char: str, *faces: FontFace) -> bool:
            code = ord(char)
            return code in ALIASES or all(fonts.has_glyph(code, face) for face in faces)

        if options.replace_unsupported is not None:
            # Without a replacement the layout stops at the first such character instead.
            notes.characters(
                front.body,
                front.body_line,
                lambda c: shown(c, FontFace.REGULAR, FontFace.BOLD),
                lambda c: shown(c, FontFace.MONO),
                MISSING_EFFECT if options.replace_unsupported is question_mark else REPLACED_EFFECT,
            )
        settings = LayoutSettings(
            variant=options.variant,
            language=options.language,
            fonts=fonts,
            highlight=options.highlight,
            image_converters=options.image_converters,
            code_block_renderers=options.code_block_renderers,
            line_offset=front.body_line,
            status_labels=labels,
            replace_unsupported=options.replace_unsupported,
            today=today,
        )
        subtitle = front.get(Keys.SUBTITLE)
        info = PdfInfo(
            title=title,
            author=author,
            subject=subtitle,
            language=options.language,
            created=options.created or dt.datetime.now(dt.UTC),
        )
        frame_info = FrameInfo(
            title=title,
            subtitle=subtitle,
            author=author,
            location=front.get(Keys.LOCATION),
            date=options.date,
            # „Stand:" is ``datum`` or the day of creation (Word: the day of generation).
            as_of=options.date or (options.created.date() if options.created else dt.date.today()),
            company=options.company,
            toc=options.toc,
            marking=options.marking,
        )
        pdf = lay_out(tokens, document, settings, frame_info, notes, info)
        output.write(to_pdfa(pdf.content, info))
        return GenerationResult(notes.to_tuple(), pages=pdf.pages)


def apply_front_matter(front: FrontMatter, options: PdfOptions) -> PdfOptions:
    if (value := front.get(Keys.TEMPLATE)) is not None:
        try:
            variant = WordVariant.parse(value)
        except DocumentConversionError as error:  # parse() names DOCX, the Word templates
            raise DocumentConversionError(FORMAT, error.reason) from None
        options = replace(options, variant=variant)
    if (value := front.get(Keys.LANGUAGE)) is not None:
        options = replace(options, language=Language.parse(value, FORMAT))
    if (value := front.boolean(Keys.TYPOGRAPHY)) is not None:
        options = replace(options, typography=value)
    if (value := front.boolean(Keys.HIGHLIGHT)) is not None:
        options = replace(options, highlight=value)
    if (value := front.date()) is not None:
        options = replace(options, date=value)
    if (value := front.get(Keys.COMPANY)) is not None:
        options = replace(options, company=value)
    if (value := front.boolean(Keys.TOC)) is not None:
        options = replace(options, toc=value)
    if (value := front.get(Keys.MARKING)) is not None:
        options = replace(options, marking=Marking.parse(value, FORMAT))
    return options
