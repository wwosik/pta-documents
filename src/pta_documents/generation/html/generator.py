"""Markdown to a self-contained HTML deck with the slides of the PPTX generator (E10-S01).

The deck is not a second reading of the Markdown: ``PptxGenerator`` writes the PowerPoint deck
(same parser, same fitting, same splits, same errors and notes), and ``HtmlDeckWriter`` draws
its slides — layouts, master, theme and all — on a 1600 px stage. So the HTML deck has the same
slides with the same titles as the PPTX, by construction, and shows the PTA look of the template.
"""

from __future__ import annotations

import io
from typing import BinaryIO, Final

import pptx

from pta_documents.design.variants import TEXTS
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.result import GenerationResult
from pta_documents.generation.html.options import HtmlDeckOptions
from pta_documents.generation.html.writer import HtmlDeckWriter, PageInfo
from pta_documents.generation.pptx import generator as pptx_generator
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.markdown.document import MarkdownDocument, MetadataKeys
from pta_documents.markdown.front_matter import FrontMatter, Keys

FORMAT: Final = DocumentFormat.HTML
OWN_KEYS: Final = (Keys.PROGRESS, Keys.CHAPTERS)
"""The front matter keys only the HTML deck knows."""
VALID_KEYS: Final = (*pptx_generator.VALID_KEYS, *OWN_KEYS)


class HtmlDeckGenerator:
    def generate(
        self,
        document: MarkdownDocument,
        output: BinaryIO,
        options: HtmlDeckOptions | None = None,
    ) -> GenerationResult:
        """Write ``document`` as one HTML file (UTF-8) to ``output``.

        Returns the slides and the notes of the PPTX generator. Raises
        ``DocumentConversionError`` (format ``html``) for mistakes in the Markdown or its front
        matter, with the reasons the PPTX generator gives.
        """
        options = options or HtmlDeckOptions()
        front = FrontMatter.read(document.text, FORMAT)
        front.check_keys(VALID_KEYS, allow_status=True)
        show_progress = front.boolean(Keys.PROGRESS)
        show_chapters = front.boolean(Keys.CHAPTERS)
        # The front matter as PowerPoint reads it: same values, same errors (as 'html').
        slides_options = pptx_generator.apply_front_matter(front, options.slides())
        deck = io.BytesIO()
        try:
            result = PptxGenerator().generate(_without_own_keys(document), deck, options.slides())
        except DocumentConversionError as error:
            raise DocumentConversionError(FORMAT, error.reason) from error
        presentation = pptx.Presentation(io.BytesIO(deck.getvalue()))
        title = (
            front.get(Keys.TITLE)
            or presentation.core_properties.title
            or document.metadata.get(MetadataKeys.TITLE)
            or ""
        )
        info = PageInfo(
            title=title,
            language=slides_options.language.value,
            texts=TEXTS[slides_options.language],
            show_progress=options.show_progress if show_progress is None else show_progress,
            show_chapters=options.show_chapters if show_chapters is None else show_chapters,
        )
        output.write(HtmlDeckWriter(presentation, info).write().encode("utf-8"))
        return result


def _without_own_keys(document: MarkdownDocument) -> MarkdownDocument:
    """The document with the HTML deck's own front matter keys turned into comment lines (the
    line numbers of everything else stay)."""
    lines = document.text.split("\n")
    if not lines or lines[0].strip() != "---":
        return document
    own = tuple(key.lower() for key in OWN_KEYS)
    for index in range(1, len(lines)):
        line = lines[index].strip()
        if line in ("---", "..."):
            break
        key = line.split(":", 1)[0].strip().lower()
        if key in own:
            lines[index] = "# " + lines[index]
    return MarkdownDocument("\n".join(lines), document.resources, document.metadata)
