"""Check a Markdown document without writing it: errors, notes, style notes and statistics.

``check()`` is what ``./run.sh check`` runs (E08-S02). Errors and notes come from a trial run of
the generator into memory — the same code path as ``generate``, so the check never says less or
other than generating would. Style notes come from ``style_rules`` on the Markdown, the
statistics from the trial deck (PowerPoint) or the Markdown (Word, which counts its pages only
when it lays the document out).

Usage::

    result = check(document, DocumentFormat.PPTX, CheckOptions(sources=True))
    if not result.ok:
        print(result.errors)
    for note in result.notes:  # generator and style notes, by line
        print(note)
    print(result.stats)
"""

from __future__ import annotations

import io
import math
import statistics
from dataclasses import dataclass, field
from typing import Final

import pptx
from lxml import etree
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.slide import Slide as PptxSlide

from pta_documents.design import slides as design
from pta_documents.design.variants import TEXTS
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.layout_syntax import NOTES
from pta_documents.generation.common.result import GenerationNote, GenerationResult
from pta_documents.generation.common.style_rules import (
    StyleLimits,
    close_of,
    inline_text,
    style_notes,
    words,
)
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.markdown.document import MarkdownDocument
from pta_documents.markdown.front_matter import FrontMatter
from pta_documents.markdown.parser import CONTAINER_OPEN, container, parse

DRAWING: Final = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
A: Final = f"{DRAWING}t"
MINUTES_PER_SLIDE: Final = 2
"""Rule of thumb: talking time per content slide."""
NOTES_WORDS_PER_MINUTE: Final = 120
"""Rule of thumb: how fast speaker notes are read out."""
WORDS_PER_PAGE: Final = 350
"""Rule of thumb: words on a page of the PTA Word template."""
PAGES_PER_BLOCK: Final = 0.5
"""Rule of thumb: the page a table or figure takes."""
_NOT_COUNTED: Final = (
    PP_PLACEHOLDER.TITLE,
    PP_PLACEHOLDER.CENTER_TITLE,
    PP_PLACEHOLDER.FOOTER,
    PP_PLACEHOLDER.SLIDE_NUMBER,
    PP_PLACEHOLDER.DATE,
)
_TITLE_TYPES: Final = (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE)


@dataclass(frozen=True)
class CheckOptions:
    """What to check besides what generating would report."""

    sources: bool = False
    """Check that images name their author or source (``style-image-source``); the tool turns
    it on for a folder with a ``QUELLEN.md`` (decision 2026-11-07)."""
    skip: tuple[str, ...] = ()
    """Style codes not to check, on top of the front matter key ``pruefung``."""
    limits: StyleLimits = field(default_factory=StyleLimits)


@dataclass(frozen=True)
class DeckStats:
    """The figures of a deck, counted on the trial deck."""

    slides: int
    title: int
    chapters: int
    content: int
    """Content slides, continued slides ("(Forts.)") included."""
    continued: int
    closing: int
    words: int
    """Words on all slides (titles, footers and speaker notes not counted)."""
    words_min: int
    """The fewest words on a content slide."""
    words_median: int
    words_max: int
    notes_words: int
    """Words in the speaker notes."""

    @property
    def minutes(self) -> int:
        """Rough talking time: two minutes per content slide plus the notes at 120 words a
        minute — a rule of thumb that catches 60 slides for 30 minutes, nothing finer."""
        return MINUTES_PER_SLIDE * self.content + math.ceil(
            self.notes_words / NOTES_WORDS_PER_MINUTE
        )

    def lines(self) -> tuple[str, str]:
        """Two lines for people."""
        return (
            f"{self.slides} slides: {self.title} title, {self.chapters} chapters, "
            f"{self.content} content ({self.continued} continued), {self.closing} closing",
            f"{self.words} words, per content slide {self.words_min}/{self.words_median}/"
            f"{self.words_max} (min/median/max), {self.notes_words} in notes; about "
            f"{self.minutes} minutes (rule of thumb: 2 per content slide plus notes at "
            f"{NOTES_WORDS_PER_MINUTE} words a minute)",
        )


@dataclass(frozen=True)
class ReportStats:
    """The figures of a Word document, counted on the Markdown."""

    words: int
    """Words of the text (code blocks, front matter and speaker notes not counted)."""
    headings: int
    tables: int
    figures: int

    @property
    def pages(self) -> int:
        """Rough page count: 350 words a page plus half a page per table and figure; Word
        counts the real number only when it opens the document."""
        return max(
            1,
            math.ceil(self.words / WORDS_PER_PAGE + PAGES_PER_BLOCK * (self.tables + self.figures)),
        )

    def lines(self) -> tuple[str, str]:
        """Two lines for people."""
        return (
            f"{self.words} words, {self.headings} headings, {self.tables} tables, "
            f"{self.figures} figures",
            f"about {self.pages} pages (rule of thumb: {WORDS_PER_PAGE} words a page plus half a "
            "page per table and figure; Word counts when it opens the document)",
        )


type CheckStats = DeckStats | ReportStats


@dataclass(frozen=True)
class CheckResult:
    """What ``check()`` found."""

    errors: tuple[str, ...] = ()
    """The reasons of ``DocumentConversionError``s: the document cannot be generated."""
    notes: tuple[GenerationNote, ...] = ()
    """The generator's notes and the style notes, by line."""
    stats: CheckStats | None = None
    """None when the document has errors."""

    @property
    def ok(self) -> bool:
        """No errors (notes do not count)."""
        return not self.errors

    def codes(self) -> list[str]:
        return [note.code for note in self.notes]


def check(
    document: MarkdownDocument, format: DocumentFormat, options: CheckOptions | None = None
) -> CheckResult:
    """Check ``document`` for ``format`` (``DOCX`` or ``PPTX``) without writing a file."""
    options = options or CheckOptions()
    if format not in (DocumentFormat.DOCX, DocumentFormat.PPTX):
        raise ValueError(f"check() takes DOCX or PPTX, not {format}")
    errors: list[str] = []
    generated: GenerationResult | None = None
    output = io.BytesIO()
    try:
        if format is DocumentFormat.PPTX:
            generated = PptxGenerator().generate(document, output)
        else:
            generated = DocxGenerator().generate(document, output)
    except DocumentConversionError as error:
        errors.append(error.reason)
    style: tuple[GenerationNote, ...] = ()
    try:
        style = style_notes(
            document,
            format,
            sources=options.sources,
            skip=options.skip,
            limits=options.limits,
        )
    except DocumentConversionError as error:
        if error.reason not in errors:
            errors.append(error.reason)
    notes = tuple(
        sorted(
            (*(generated.notes if generated else ()), *style),
            key=lambda note: note.line or 0,
        )
    )
    stats: CheckStats | None = None
    if not errors:
        stats = (
            deck_stats(output.getvalue())
            if format is DocumentFormat.PPTX
            else report_stats(document, format)
        )
    return CheckResult(tuple(errors), notes, stats)


def deck_stats(deck: bytes) -> DeckStats:
    """Count the slides and words of a deck the PPTX generator wrote."""
    presentation = pptx.Presentation(io.BytesIO(deck))
    titles = set(design.TITLE_SLIDES.values())
    continued_marks = tuple(" " + texts.continued for texts in TEXTS.values())
    title = chapters = closing = continued = notes_words = 0
    content_words: list[int] = []
    total = 0
    for slide in presentation.slides:
        layout = slide.slide_layout.name
        count = _slide_words(slide)
        total += count
        if slide.has_notes_slide:
            notes_words += words(" ".join(_spoken_texts(slide.notes_slide.element)))
        if layout in titles:
            title += 1
        elif layout == design.LAYOUTS.chapter:
            chapters += 1
        elif layout == design.LAYOUTS.closing:
            closing += 1
        else:
            content_words.append(count)
            if _title(slide).endswith(continued_marks):
                continued += 1
    return DeckStats(
        slides=len(presentation.slides),
        title=title,
        chapters=chapters,
        content=len(content_words),
        continued=continued,
        closing=closing,
        words=total,
        words_min=min(content_words, default=0),
        words_median=int(statistics.median(content_words)) if content_words else 0,
        words_max=max(content_words, default=0),
        notes_words=notes_words,
    )


def _texts(element: etree._Element) -> list[str]:
    # python-pptx's itertext() repeats text; read the a:t elements (ai/Gedächtnis.md).
    return [t.text or "" for t in element.iter(A)]


def _spoken_texts(element: etree._Element) -> list[str]:
    """The texts of the paragraphs of ``element`` that are not all code: a code block in the
    notes (the Markdown source of a slide, E08-S03) is not spoken, inline code is."""
    result: list[str] = []
    for paragraph in element.iter(f"{DRAWING}p"):
        fonts = [run.find(f"{DRAWING}rPr/{DRAWING}latin") for run in paragraph.iter(f"{DRAWING}r")]
        if fonts and all(f is not None and f.get("typeface") == design.CODE_FONT for f in fonts):
            continue
        result.extend(_texts(paragraph))
    return result


def _slide_words(slide: PptxSlide) -> int:
    count = 0
    for shape in slide.shapes:
        if shape.is_placeholder and shape.placeholder_format.type in _NOT_COUNTED:
            continue
        count += words(" ".join(_texts(shape.element)))
    return count


def _title(slide: PptxSlide) -> str:
    for shape in slide.shapes:
        if shape.is_placeholder and shape.placeholder_format.type in _TITLE_TYPES:
            return "".join(_texts(shape.element)).strip()
    return ""


def report_stats(document: MarkdownDocument, format: DocumentFormat) -> ReportStats:
    """Count the words, headings, tables and figures of a Word document's Markdown."""
    tokens = parse(FrontMatter.read(document.text, format).body)
    text_words = headings = tables = figures = 0
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type == CONTAINER_OPEN and container(token)[0] == NOTES:
            i = close_of(tokens, i) + 1
            continue
        if token.type == "heading_open" and token.level == 0:
            headings += 1
        elif token.type == "table_open":
            tables += 1
        elif token.type == "inline":
            text_words += words(inline_text(token))
            figures += sum(1 for child in token.children or [] if child.type == "image")
        i += 1
    return ReportStats(text_words, headings, tables, figures)
