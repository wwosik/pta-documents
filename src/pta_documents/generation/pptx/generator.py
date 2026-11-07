"""Markdown to PPTX on the PTA PowerPoint template."""

from __future__ import annotations

import datetime as dt
import io
from dataclasses import replace
from typing import BinaryIO, Final

import pptx

from pta_documents.design import slides as design
from pta_documents.design import templates
from pta_documents.design.variants import TEXTS, Language, SlidesVariant
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common.result import GenerationResult, Notes
from pta_documents.generation.pptx.model import Run, TitleSlide, plain_text
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.generation.pptx.parser import DeckParser
from pta_documents.generation.pptx.writer import DeckInfo, DeckWriter
from pta_documents.markdown.document import MarkdownDocument, MetadataKeys
from pta_documents.markdown.front_matter import FrontMatter, Keys

FORMAT: Final = DocumentFormat.PPTX
VALID_KEYS: Final = (
    Keys.TEMPLATE,
    Keys.TITLE,
    Keys.SUBTITLE,
    Keys.AUTHOR,
    Keys.LOCATION,
    Keys.DATE,
    Keys.LANGUAGE,
    Keys.FOOTER,
    Keys.TITLE_SLIDE,
)


class PptxGenerator:
    def generate(
        self,
        document: MarkdownDocument,
        output: BinaryIO,
        options: PptxOptions | None = None,
    ) -> GenerationResult:
        """Write ``document`` as a PPTX to ``output``.

        Returns the number of slides and the notes on what had to be worked around (slides
        split, HTML left out, …), see ``GenerationResult``. Raises ``DocumentConversionError``
        for mistakes in the Markdown or its front matter.
        """
        notes = Notes()
        front = FrontMatter.read(document.text, FORMAT)
        front.check_keys(VALID_KEYS, allow_status=True)
        options = apply_front_matter(front, options or PptxOptions())
        slides = DeckParser(document, front.body, front.body_line, notes).parse()

        first = next((s for s in slides if isinstance(s, TitleSlide)), None)
        title = (
            front.get(Keys.TITLE)
            or (plain_text(first.title) if first else None)
            or document.metadata.get(MetadataKeys.TITLE)
        )
        if first is None and front.get(Keys.TITLE):
            # No '#' heading, but a title in the front matter: the deck still gets its cover.
            slides.insert(0, TitleSlide((Run(title or ""),)))
        author = front.get(Keys.AUTHOR) or document.metadata.get(MetadataKeys.AUTHOR)
        byline = ", ".join(
            part
            for part in (
                author,
                front.get(Keys.LOCATION),
                options.date.strftime("%d.%m.%Y") if options.date else None,
            )
            if part
        )
        footer_title = options.footer or title
        info = DeckInfo(
            title=title,
            subtitle=front.get(Keys.SUBTITLE),
            byline=byline or None,
            footer=design.FOOTER_PREFIX + footer_title if footer_title else "PTA",
        )

        presentation = pptx.Presentation(
            io.BytesIO(templates.slides_template(options.variant, options.language))
        )
        DeckWriter(presentation, options, TEXTS[options.language], info, notes).write(slides)

        properties = presentation.core_properties
        now = dt.datetime.now(dt.UTC).replace(microsecond=0, tzinfo=None)
        properties.title = title or ""
        properties.author = author or ""
        properties.last_modified_by = author or ""
        properties.revision = 1
        properties.created = now
        properties.modified = now
        presentation.save(output)
        return GenerationResult(notes.to_tuple(), slides=len(presentation.slides))


def apply_front_matter(front: FrontMatter, options: PptxOptions) -> PptxOptions:
    if (value := front.get(Keys.TEMPLATE)) is not None:
        options = replace(options, variant=SlidesVariant.parse(value))
    if (value := front.get(Keys.LANGUAGE)) is not None:
        options = replace(options, language=Language.parse(value, FORMAT))
    if (value := front.get(Keys.FOOTER)) is not None:
        options = replace(options, footer=value)
    if (value := front.get(Keys.TITLE_SLIDE)) is not None:
        options = replace(
            options,
            title_slide=front.one_of(
                Keys.TITLE_SLIDE, value, ((name, name) for name in design.TITLE_SLIDES)
            ),
        )
    if (value := front.date()) is not None:
        options = replace(options, date=value)
    return options
