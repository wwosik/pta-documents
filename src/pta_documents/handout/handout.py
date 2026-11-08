"""A presentation as a handout on the PTA Word template (E16-S03).

The handout is **Markdown** for the DOCX generator, not a second Word writer: ``build_handout``
generates the deck (PPTX, in memory, in the version for the audience) and reads its slides —
layout, title, text, speaker notes — and writes a Markdown document from them: the front matter
of the deck (title, subtitle, author, location, date, marking, language) on the cover, the
title slide small after it, the schedule (E16-S02) or a table of contents, then a ``#`` per
divider slide and per slide its picture with the caption „Folie 3: Titel" and beside or below
it the speaker notes (trainer) or lines to write on (everyone else); the closing slide small at
the end. ``write_handout`` lets the DOCX generator write it, with the two options only the
handout uses: captions without numbers and ``::: columns`` side by side.

=========  ==============================  =============================================
layout     template                        per slide
=========  ==============================  =============================================
``2``      ``quer`` (landscape)            picture left, notes or six lines right
``3``      ``hoch`` (portrait)             picture, below it notes or two lines
``6``      ``hoch``                        two pictures side by side, below them notes or
                                           two lines; three such rows a page
=========  ==============================  =============================================

The pictures come from the preview (E10-S02, ``slide_pictures``: extra ``preview``); without
them (``pictures=None``) the handout has the text of each slide instead — its title, its
paragraphs and its lists — and a note ``handout-without-pictures``. The sizes are worked out
from the page and the paragraph styles of the template (``design.word_styles``), so that two,
three or six slides fill a page; Word lays the pages out itself.

Backup slides (E16-S04) are only in the trainer's handout.

Usage::

    pictures = slide_pictures(document, Audience.KUNDE)  # PreviewUnavailableError without it
    handout = build_handout(document, pictures, HandoutOptions(layout=HandoutLayout.THREE))
    with open("thema-handout.docx", "wb") as output:
        result = write_handout(handout, output)
"""

from __future__ import annotations

import io
import math
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, BinaryIO, Final

import pptx
from PIL import Image, ImageDraw

from pta_documents.design import colors, word_styles
from pta_documents.design import slides as design
from pta_documents.design.variants import Language, WordVariant
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common import audience as audiences
from pta_documents.generation.common import training_schedule
from pta_documents.generation.common.audience import Audience
from pta_documents.generation.common.result import (
    GenerationNote,
    GenerationResult,
    NoteCodes,
    Notes,
)
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.html.generator import HtmlDeckGenerator
from pta_documents.generation.html.options import HtmlDeckOptions
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import text as md
from pta_documents.markdown.document import DocumentResource, MarkdownDocument
from pta_documents.markdown.front_matter import FrontMatter, Keys
from pta_documents.preview import INSTALL_HINT, SlidePicture, render_deck

FORMAT: Final = DocumentFormat.PPTX
PICTURE_FOLDER: Final = "handout"
"""The resource paths of the slide pictures: ``handout/folie-03.png``."""
LINE: Final = "***"
"""A line to write on: a horizontal rule, in Word a paragraph „Standard" with a rule below it.
``***`` rather than ``---``, which separates the columns side by side."""
NATURAL_LINE: Final = 1.33
"""The single line height of Segoe UI in multiples of the font size, for the paragraph
heights."""
PAGE_SLACK_PT: Final = 18.0
"""Room left free on each page, so that rounding in Word does not push a slide over."""
CELL_SLACK_PT: Final = 6.0
"""Room left free in a row side by side (cell margins, the rule of the last line)."""
PICTURE_GAP_PT: Final = 8.5
"""The gap the DOCX generator leaves beside a picture in a cell (0.3 cm)."""
SMALL_PICTURE_PT: Final = 170.0
"""Title and closing slide, small (6 cm)."""
SLIDE_RATIO: Final = 9 / 16
PRINT_DPI: Final = 300
"""Slide pictures are made smaller to this resolution at their size in the handout."""
BORDER_SHARE: Final = 1 / 400
"""The grey frame around a slide picture, as a share of its width (4 px at 1600 px)."""
BODY_PLACEHOLDERS: Final = ("body", "obj")
SKIPPED_PLACEHOLDERS: Final = ("title", "ctrTitle", "ftr", "sldNum", "dt")
TITLE_LAYOUTS: Final = frozenset(design.TITLE_SLIDES.values())


class HandoutLayout(IntEnum):
    """Slides per page (``--layout``)."""

    TWO = 2
    """Landscape, the picture beside the notes or lines."""
    THREE = 3
    """Portrait, the notes or lines below the picture (the default)."""
    SIX = 6
    """Portrait, three rows of two pictures, the notes or lines below each row."""


@dataclass(frozen=True)
class HandoutOptions:
    layout: HandoutLayout = HandoutLayout.THREE
    audience: Audience | None = None
    """The version (E16-S01); it wins over ``fassung:`` of the deck. None: ``fassung:``, else
    ``kunde``. The trainer's handout has the speaker notes (with the planned times, E16-S02)
    and the backup slides; every other one lines to write on."""


@dataclass(frozen=True)
class HandoutTexts:
    slide: str
    schedule: str


TEXTS: Final = {
    Language.DE: HandoutTexts(slide="Folie", schedule="Zeitplan"),
    Language.EN: HandoutTexts(slide="Slide", schedule="Schedule"),
}


@dataclass(frozen=True)
class Handout:
    """What ``build_handout`` makes: the Markdown with the slide pictures as resources."""

    document: MarkdownDocument
    audience: Audience
    layout: HandoutLayout
    pictures: bool
    """Whether the slides are pictures (else their text)."""
    slides: int
    """The slides in the handout."""
    notes: tuple[GenerationNote, ...] = ()
    """The notes of generating the deck and ``handout-without-pictures``."""


class SlideKind(Enum):
    TITLE = "title"
    CHAPTER = "chapter"
    CONTENT = "content"
    CLOSING = "closing"


@dataclass(frozen=True)
class SlideInfo:
    """One slide of the generated deck, as the handout needs it."""

    number: int
    """From 1, as in the deck and the preview."""
    kind: SlideKind
    title: str
    backup: bool
    text: tuple[str, ...]
    """The slide's paragraphs and list items as Markdown blocks (for the text handout)."""
    notes: tuple[str, ...]
    """The speaker notes as Markdown blocks."""


@dataclass(frozen=True)
class _Geometry:
    layout: HandoutLayout
    variant: WordVariant
    picture_pt: float
    """The width of a slide picture."""
    lines: int
    """Lines to write on per slide (per row of two at six a page)."""
    columns: tuple[int, int] | None = None
    """Layout 2: the weights of picture and notes side by side."""


def docx_options() -> DocxOptions:
    """The options the handout is written with: captions without numbers, columns side by
    side (E16-S03)."""
    return DocxOptions(figure_numbers=False, side_by_side_columns=True)


def slide_pictures(
    document: MarkdownDocument, audience: Audience | None = None, scale: int = 1
) -> list[SlidePicture]:
    """One picture per slide of the deck ``document`` in the version for ``audience``: its
    HTML deck (E10-S01) drawn by the preview (E10-S02). Raises ``PreviewUnavailableError``
    without the extra ``preview`` and ``DocumentConversionError`` for mistakes in the deck."""
    deck = io.BytesIO()
    HtmlDeckGenerator().generate(document, deck, HtmlDeckOptions(audience=audience))
    return render_deck(deck.getvalue(), scale=scale)


def build_handout(
    document: MarkdownDocument,
    pictures: Sequence[SlidePicture] | None,
    options: HandoutOptions | None = None,
) -> Handout:
    """The handout of the deck ``document`` as Markdown for the DOCX generator.

    ``pictures`` are the slides' pictures (``slide_pictures``, same version); a slide without
    one shows its text. Raises ``DocumentConversionError`` for mistakes in the deck, as
    generating it would.
    """
    options = options or HandoutOptions()
    front = FrontMatter.read(document.text, FORMAT)
    chosen = audiences.resolve(front, options.audience)
    deck = io.BytesIO()
    result = PptxGenerator().generate(document, deck, PptxOptions(audience=chosen))
    presentation = pptx.Presentation(io.BytesIO(deck.getvalue()))
    slides = read_slides(presentation)
    if chosen is not Audience.TRAINER:
        slides = [s for s in slides if not s.backup]
    schedule = training_schedule.deck_schedule(document, chosen)
    value = front.get(Keys.LANGUAGE)
    language = Language.parse(value, FORMAT) if value is not None else Language.DE
    by_number = {p.number: p.png for p in pictures or ()}
    writer = _Writer(
        geometry(options.layout),
        TEXTS[language],
        chosen is Audience.TRAINER,
        by_number,
    )
    title = (
        front.get(Keys.TITLE)
        or str(presentation.core_properties.title or "")
        or next((s.title for s in slides if s.kind is SlideKind.TITLE), "")
        or writer.texts.slide
    )
    head = _front_matter(front, title, writer.geometry.variant, chosen, schedule is None)
    body = writer.body(slides, schedule)
    notes = Notes()
    for note in result.notes:
        notes.add(note.code, note.line, note.message)
    if pictures is None:
        notes.add(
            NoteCodes.HANDOUT_WITHOUT_PICTURES,
            None,
            "The handout shows the text of each slide instead of its picture. " + INSTALL_HINT,
        )
    text = head + "\n\n" + "\n\n".join(body) + "\n"
    return Handout(
        MarkdownDocument(text, tuple(writer.resources)),
        chosen,
        options.layout,
        pictures is not None,
        len(slides),
        notes.to_tuple(),
    )


def write_handout(handout: Handout, output: BinaryIO) -> GenerationResult:
    """Write ``handout`` with the DOCX generator to ``output``; the result has the handout's
    notes and those of the DOCX generator."""
    result = DocxGenerator().generate(handout.document, output, docx_options())
    return GenerationResult((*handout.notes, *result.notes))


# ---------------------------------------------------------------------- the deck


def read_slides(presentation: Any) -> list[SlideInfo]:
    """The slides of a generated deck (python-pptx ``Presentation``)."""
    raw = list(presentation.slides)
    backup = design.backup_start([(s.slide_layout.name, s.name) for s in raw])
    result: list[SlideInfo] = []
    for index, slide in enumerate(raw):
        layout = str(slide.slide_layout.name)
        if index == 0 and layout in TITLE_LAYOUTS:
            kind = SlideKind.TITLE
        elif layout == design.LAYOUTS.closing:
            kind = SlideKind.CLOSING
        elif layout == design.LAYOUTS.chapter:
            kind = SlideKind.CHAPTER
        else:
            kind = SlideKind.CONTENT
        title_shape = slide.shapes.title
        title = _plain(title_shape.text_frame.text) if title_shape is not None else ""
        result.append(
            SlideInfo(
                number=index + 1,
                kind=kind,
                title=title,
                backup=backup is not None and index >= backup,
                text=tuple(_shape_texts(slide.shapes)) if kind is SlideKind.CONTENT else (),
                notes=tuple(_notes(slide)),
            )
        )
    return result


def _plain(text: str) -> str:
    return " ".join(text.replace("\v", " ").split())


def _placeholder(shape: Any) -> tuple[str, int] | None:
    """Type and index of a placeholder (``p:ph``); None for another shape."""
    element = shape._element
    ph = element.find(".//{http://schemas.openxmlformats.org/presentationml/2006/main}ph")
    if ph is None:
        return None
    return str(ph.get("type", "obj")), int(ph.get("idx", "0"))


def _shape_texts(shapes: Any) -> Iterator[str]:
    """The paragraphs of the slide's shapes (groups included), but title and footer: in a
    body placeholder the PTA levels (``design.TEXT_LEVELS``) as bold line, text and list."""
    for shape in shapes:
        if shape.shape_type is not None and int(shape.shape_type) == 6:  # a group
            yield from _shape_texts(shape.shapes)
            continue
        placeholder = _placeholder(shape)
        kind = placeholder[0] if placeholder else None
        index = placeholder[1] if placeholder else None
        if kind in SKIPPED_PLACEHOLDERS or index in design.PLACEHOLDERS.agenda_numbers:
            continue
        if getattr(shape, "has_table", False) and shape.has_table:
            for row in shape.table.rows:
                cells = [_plain(cell.text) for cell in row.cells]
                if any(cells):
                    yield _escape(" · ".join(c for c in cells if c))
            continue
        if not shape.has_text_frame:
            continue
        levels = design.TEXT_LEVELS
        for paragraph in shape.text_frame.paragraphs:
            text = _plain("".join(run.text for run in paragraph.runs))
            if not text:
                continue
            level = int(paragraph.level)
            if index in design.PLACEHOLDERS.agenda_texts:
                yield "- " + _escape(text)  # an agenda item
            elif kind in BODY_PLACEHOLDERS and level >= levels.bullets[0]:
                yield "  " * (level - levels.bullets[0]) + "- " + _escape(text)
            elif kind in BODY_PLACEHOLDERS and level == levels.subheadline:
                yield f"**{_escape(text)}**"
            else:
                yield _escape(text)


def _notes(slide: Any) -> Iterator[str]:
    """The speaker notes, a block per paragraph, list levels as ``-``."""
    if not slide.has_notes_slide:
        return
    frame = slide.notes_slide.notes_text_frame
    if frame is None:
        return
    for paragraph in frame.paragraphs:
        text = _plain("".join(run.text for run in paragraph.runs))
        if not text:
            continue
        level = int(paragraph.level)
        prefix = "  " * (level - 1) + "- " if level else ""
        yield prefix + _escape(text)


def _escape(text: str) -> str:
    """``text`` as literal Markdown in a paragraph, a caption or a heading."""
    escaped = md.escape(text).replace("]", "\\]").replace("{", "\\{")
    escaped = escaped.replace("==", "\\=\\=").replace(":icon-", "\\:icon-")
    return md.escape_line_start(escaped)


# ---------------------------------------------------------------------- the Markdown


def geometry(layout: HandoutLayout) -> _Geometry:
    """Template, picture width and lines of ``layout``, from the page and the paragraph
    styles of the template: two, three or six slides (with a ``#`` heading) fill a page."""
    variant = WordVariant.LANDSCAPE if layout is HandoutLayout.TWO else WordVariant.PORTRAIT
    styles = word_styles.read(variant)
    page = styles.page

    def height(name: str) -> float:
        style = styles.paragraph(name)
        return style.space_before_pt + style.leading(NATURAL_LINE) + style.space_after_pt

    normal = styles.paragraph("Normal")
    line = height("Normal")
    caption = height("caption")
    around_picture = normal.space_before_pt + normal.space_after_pt
    rows = 2 if layout is HandoutLayout.TWO else 3
    budget = (page.text_height_pt - height("heading 1") - PAGE_SLACK_PT) / rows
    width = page.text_width_pt
    if layout is HandoutLayout.TWO:
        picture = (budget - around_picture - caption - CELL_SLACK_PT) / SLIDE_RATIO
        picture = min(picture, width / 2)
        lines = max(1, math.floor((budget - CELL_SLACK_PT) / line))
        left = round(99 * (picture + PICTURE_GAP_PT * 2) / width)
        return _Geometry(layout, variant, picture, lines, (left, 99 - left))
    lines = 2
    room = budget - around_picture - caption - lines * line
    if layout is HandoutLayout.SIX:
        room -= CELL_SLACK_PT
    picture = room / SLIDE_RATIO
    widest = width / 2 - PICTURE_GAP_PT if layout is HandoutLayout.SIX else width
    return _Geometry(layout, variant, min(picture, widest), lines)


def _front_matter(
    front: FrontMatter, title: str, variant: WordVariant, chosen: Audience, toc: bool
) -> str:
    lines = ["---", f"{Keys.TEMPLATE}: {variant.value}", f"{Keys.TITLE}: {_quoted(title)}"]
    for key in (Keys.SUBTITLE, Keys.AUTHOR, Keys.LOCATION, Keys.DATE, Keys.LANGUAGE):
        if (value := front.get(key)) is not None:
            lines.append(f"{key}: {_quoted(value)}")
    if (value := front.get(Keys.MARKING)) is not None:
        lines.append(f"{Keys.MARKING}: {value}")
    elif audiences.needs_marking(chosen, front):
        lines.append(f"{Keys.MARKING}: intern")
    if toc:
        lines.append(f"{Keys.TOC}: ja")
    # The slides' texts are typeset already, by the PPTX generator.
    lines.append(f"{Keys.TYPOGRAPHY}: nein")
    lines.append("---")
    return "\n".join(lines)


def _quoted(value: str) -> str:
    return f'"{value}"'


@dataclass
class _Writer:
    geometry: _Geometry
    texts: HandoutTexts
    trainer: bool
    pictures: dict[int, bytes]
    resources: list[DocumentResource] = field(default_factory=list[DocumentResource])
    pending: list[SlideInfo] = field(default_factory=list[SlideInfo])
    """Layout 6: the first slide of a row of two."""

    def body(
        self, slides: Sequence[SlideInfo], schedule: training_schedule.Schedule | None
    ) -> list[str]:
        blocks: list[str] = []
        rest = list(slides)
        if rest and rest[0].kind is SlideKind.TITLE:
            blocks.extend(self.small(rest.pop(0)))
        if schedule is not None:
            blocks.append(f"**{self.texts.schedule}**")
            blocks.append(schedule.to_markdown().rstrip("\n"))
        for slide in rest:
            if slide.kind is SlideKind.CHAPTER:
                blocks.extend(self.flush())
                heading = _escape(slide.title) if slide.title else self.caption(slide)
                blocks.append(f"# {heading}")
            if slide.kind is SlideKind.CLOSING:
                blocks.extend(self.flush())
                blocks.extend(self.small(slide))
            else:
                blocks.extend(self.slide(slide))
        blocks.extend(self.flush())
        return blocks

    def caption(self, slide: SlideInfo) -> str:
        label = f"{self.texts.slide} {slide.number}"
        return f"{label}: {_escape(slide.title)}" if slide.title else label

    def picture(self, slide: SlideInfo, width_pt: float) -> str | None:
        """``![Folie 3: Titel](handout/folie-03.png)``, the picture at ``width_pt``; None
        without a picture of the slide."""
        png = self.pictures.get(slide.number)
        if png is None:
            return None
        path = f"{PICTURE_FOLDER}/{picture_name(slide.number)}"
        self.resources.append(DocumentResource(path, "image/png", print_picture(png, width_pt)))
        return f"![{self.caption(slide)}]({path})"

    def lines(self) -> list[str]:
        return [LINE] * self.geometry.lines

    def remarks(self, slide: SlideInfo) -> list[str]:
        """The trainer's speaker notes, or lines to write on."""
        if self.trainer and slide.notes:
            return _tight(slide.notes)
        return self.lines()

    def text(self, slide: SlideInfo) -> list[str]:
        """The slide as text, without its picture: caption bold, then its paragraphs."""
        return [f"**{self.caption(slide)}**", *_tight(slide.text)]

    def text_remarks(self, slide: SlideInfo) -> list[str]:
        """Beside the slide as text: the trainer's notes as a quote (set off from the slide's
        text), or lines to write on."""
        if self.trainer and slide.notes:
            return [_quote(slide.notes)]
        return self.lines()

    def small(self, slide: SlideInfo) -> list[str]:
        """Title or closing slide: small, the notes only for the trainer, no lines."""
        picture = self.picture(slide, min(SMALL_PICTURE_PT, self.geometry.picture_pt))
        notes = self.trainer and slide.notes
        if picture is None:
            return [*self.text(slide), *([_quote(slide.notes)] if notes else [])]
        return [picture, *(_tight(slide.notes) if notes else [])]

    def slide(self, slide: SlideInfo) -> list[str]:
        layout_columns = self.geometry.columns
        picture = self.picture(slide, self.geometry.picture_pt)
        if picture is None:
            return [*self.flush(), *self.text(slide), *self.text_remarks(slide)]
        if layout_columns is not None:
            left, right = layout_columns
            return [
                f"::: columns {left}:{right}\n\n{picture}\n\n---\n\n"
                + "\n\n".join(self.remarks(slide))
                + "\n\n:::"
            ]
        if self.geometry.layout is HandoutLayout.SIX:
            self.pending.append(slide)
            if len(self.pending) < 2:
                return []
            return self.flush()
        return [picture, *self.remarks(slide)]

    def flush(self) -> list[str]:
        """Layout 6: the pending pictures as one row (or one alone), the notes below."""
        if not self.pending:
            return []
        pending, self.pending = self.pending, []
        paths = [f"{PICTURE_FOLDER}/{picture_name(s.number)}" for s in pending]
        row = " ".join(f"![{self.caption(s)}]({p})" for s, p in zip(pending, paths, strict=True))
        blocks = [row]
        if self.trainer and any(s.notes for s in pending):
            for slide in pending:
                if slide.notes:
                    blocks.append(f"**{self.texts.slide} {slide.number}:**")
                    blocks.extend(_tight(slide.notes))
        else:
            blocks.extend(self.lines())
        return blocks


def _tight(blocks: Sequence[str]) -> list[str]:
    """``blocks`` with the items of one list together (a list without blank lines)."""
    result: list[str] = []
    for block in blocks:
        if result and _is_item(block) and _is_item(result[-1].rsplit("\n", 1)[-1]):
            result[-1] += "\n" + block
        else:
            result.append(block)
    return result


def _quote(blocks: Sequence[str]) -> str:
    """``blocks`` as one quote."""
    text = "\n\n".join(_tight(blocks))
    return "\n".join(f"> {line}" if line else ">" for line in text.split("\n"))


def _is_item(block: str) -> bool:
    return block.lstrip(" ").startswith("- ")


def picture_name(number: int) -> str:
    """The file name of a slide picture, as the preview names it."""
    return f"folie-{number:02d}.png"


def print_picture(png: bytes, width_pt: float) -> bytes:
    """The slide picture with a thin grey frame (slides are white on white paper), at most
    ``PRINT_DPI`` and its resolution set so that its natural size is ``width_pt`` wide."""
    with Image.open(io.BytesIO(png)) as opened:
        picture = opened.convert("RGB")
    pixels = math.ceil(width_pt / 72 * PRINT_DPI)
    if picture.width > pixels:
        size = (pixels, round(picture.height * pixels / picture.width))
        picture = picture.resize(size, Image.Resampling.LANCZOS)
    border = max(1, round(picture.width * BORDER_SHARE))
    draw = ImageDraw.Draw(picture)
    for offset in range(border):
        draw.rectangle(
            (offset, offset, picture.width - 1 - offset, picture.height - 1 - offset),
            outline="#" + colors.GREY_MID,
        )
    dpi = picture.width / (width_pt / 72)
    output = io.BytesIO()
    picture.save(output, "PNG", dpi=(dpi, dpi))
    return output.getvalue()
