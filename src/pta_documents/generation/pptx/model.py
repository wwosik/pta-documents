"""The slides a deck is made of, between parsing the Markdown and writing the PPTX."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Final

from pta_documents.design.colors import StatusCategory
from pta_documents.drawing.model import Drawing
from pta_documents.generation.common.code_highlight import CodeLine
from pta_documents.generation.common.image_attributes import CENTER, Focus
from pta_documents.generation.common.renderers import ChartGraphic
from pta_documents.generation.common.risks import RiskMatrix
from pta_documents.generation.common.schedule import Schedule
from pta_documents.generation.common.slide_transition import SlideTransition
from pta_documents.generation.common.steps import Steps
from pta_documents.generation.common.text_metrics import TextRun
from pta_documents.markdown.document import DocumentResource


class Effect(Enum):
    """How something comes, goes or stands out on its click (E09-S02): the entrances of
    ``{.build=…}``/``{.frag=…}``, ``{.exit}`` and ``{.emphasize}``."""

    FADE = "fade"
    APPEAR = "appear"
    FLY = "fly"
    WIPE = "wipe"
    EXIT = "exit"
    EMPHASIZE = "emphasize"


@dataclass(frozen=True)
class Click:
    """The click of the presentation a block is built on: clicks are numbered across the deck
    in the order of the Markdown; a slide plays its clicks in that order."""

    number: int
    effect: Effect = Effect.FADE


@dataclass(frozen=True)
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    strike: bool = False
    code: bool = False
    link: str | None = None
    is_break: bool = False
    mark: bool = False
    """``==text==``: bold, on the PTA yellow."""
    status: StatusCategory | None = None
    """``[words]{.success}``: bold in the signal colour; with ``label`` the colour of the dot."""
    label: bool = False
    """The dot "●" of a status label (a table cell that is one code span, on a flow slide)."""
    harvey: int | None = None
    """A Harvey ball (a table cell ``[3/4]``, E15-S02): the quarters filled; drawn as shapes
    over the cell, the run itself has no text."""

    def metric(self) -> TextRun:
        if self.is_break:
            return TextRun(is_break=True)
        return TextRun(
            self.text, self.bold or self.mark or (self.status is not None and not self.label)
        )


BREAK = Run("", is_break=True)


class Kind(Enum):
    SUBHEADLINE = "subheadline"
    """Text level 1 of the PTA body: ``###`` and deeper headings."""
    INTRO = "intro"
    """Text level 2: ordinary paragraphs."""
    BULLET = "bullet"
    """Text levels 3-5: bullet list items by depth."""
    NUMBERED = "numbered"
    """Text levels 3-5 with automatic numbers."""


@dataclass(frozen=True)
class Paragraph:
    runs: tuple[Run, ...]
    kind: Kind = Kind.INTRO
    depth: int = 0
    """Nesting depth of list items (0-2)."""
    start: int = 1
    """The first number of a numbered list."""
    icon: str | None = field(default=None, kw_only=True)
    """The icon that is the bullet of a list item (E15-S03): a picture bullet."""
    click: Click | None = field(default=None, kw_only=True)
    """The click it is built on (``{.build}``, ``{.frag}`` …, E09-S02); None: there from the
    start."""

    @property
    def level(self) -> int:
        """Zero-based paragraph level of the PTA body placeholder (``a:pPr/@lvl``)."""
        if self.kind is Kind.SUBHEADLINE:
            return 0
        if self.kind is Kind.INTRO:
            return 1
        return 2 + min(self.depth, 2)

    @property
    def is_bold_only(self) -> bool:
        texts = [r for r in self.runs if not r.is_break and r.text.strip()]
        return bool(texts) and all(r.bold for r in texts)


class Align(Enum):
    DEFAULT = "default"
    LEFT = "l"
    CENTER = "ctr"
    RIGHT = "r"


@dataclass(frozen=True)
class Table:
    rows: tuple[tuple[tuple[Run, ...], ...], ...]
    alignments: tuple[Align, ...]
    has_header: bool
    title: tuple[Run, ...] | None = None
    highlighted: tuple[bool, ...] = ()
    """Per row: its first cell is ``==marked==`` as a whole, and the row is on the PTA yellow."""
    click: Click | None = field(default=None, kw_only=True)
    """The click it is built on (``{.build}``, ``{.frag}`` …, E09-S02); None: there from the
    start."""

    def is_highlighted(self, row: int) -> bool:
        return row < len(self.highlighted) and self.highlighted[row]

    def subset(self, body_rows: list[int], keep_title: bool) -> Table:
        chosen = ([0] if self.has_header else []) + body_rows
        return Table(
            tuple(self.rows[r] for r in chosen),
            self.alignments,
            self.has_header,
            self.title if keep_title else None,
            tuple(self.is_highlighted(r) for r in chosen),
            click=self.click,
        )


PICTURE_TYPES: Final = ("image/png", "image/jpeg", "image/gif", "image/bmp", "image/tiff")
"""The image formats slides take; the parser converts others (image converters) or refuses them."""


@dataclass(frozen=True)
class Image:
    resource: DocumentResource
    alt: str
    line: int | None = None
    """The line of the image in the Markdown, for notes about it."""
    natural: tuple[float, float] | None = field(default=None, kw_only=True)
    """The natural size in pixels of a converted image (its PNG is larger); None: the
    resource's pixels."""
    svg: bytes | None = field(default=None, kw_only=True)
    """The cleaned SVG of a converted SVG image, placed beside the PNG (``asvg:svgBlip``)."""
    fit: bool = field(default=False, kw_only=True)
    """Fitted into a picture placeholder, never cropped (a QR code, E11-S04; ``{fit=contain}``,
    E15-S04)."""
    scale: float = field(default=1.0, kw_only=True)
    """``scale=N``: times the size it would be shown at, never larger than its room."""
    focus: Focus | None = field(default=None, kw_only=True)
    """``{focus=…}``: the point a placeholder's crop keeps in view; None: not written, the
    centre (E15-S04)."""
    round: bool = field(default=False, kw_only=True)
    """``{.round}``: a square around the focus in an ellipse geometry (E15-S04)."""
    click: Click | None = field(default=None, kw_only=True)
    """The click it is built on (``{.build}``, ``{.frag}`` …, E09-S02); None: there from the
    start."""

    @property
    def point(self) -> Focus:
        return self.focus or CENTER


@dataclass(frozen=True)
class Images:
    images: tuple[Image, ...]


@dataclass(frozen=True)
class Code:
    lines: tuple[str, ...]
    spans: tuple[CodeLine, ...] = ()
    """The highlighted spans of each line (E17-S02); empty: in one colour."""
    click: Click | None = field(default=None, kw_only=True)
    """The click it is built on (``{.build}``, ``{.frag}`` …, E09-S02); None: there from the
    start."""

    def part(self, start: int, stop: int) -> Code:
        """Lines ``start`` to ``stop`` (for code split over slides)."""
        return Code(self.lines[start:stop], self.spans[start:stop], click=self.click)


@dataclass(frozen=True)
class Diagram:
    """A drawing a code-block renderer made (a financial chart, E06-S02): a group of editable
    shapes in the content area."""

    drawing: Drawing
    alt: str
    """The info string of its fence, as the group's alternative text."""
    line: int | None = None
    click: Click | None = field(default=None, kw_only=True)
    """The click it is built on (``{.build}``, ``{.frag}`` …, E09-S02); None: there from the
    start."""


Visual = Table | Images | Code | Diagram


@dataclass(frozen=True)
class Separator:
    """A ``---`` line: splits the content of a slide with a named layout."""


@dataclass(frozen=True)
class Chart:
    """A ``chart`` block a renderer drew as a chart: native in its layout's chart placeholder."""

    graphic: ChartGraphic
    line: int | None = None
    click: Click | None = field(default=None, kw_only=True)
    """The click it is built on (``{.build}``, ``{.frag}`` …, E09-S02); None: there from the
    start."""


Item = Paragraph | Table | Images | Code | Diagram | Chart | Separator


@dataclass(frozen=True)
class Slide:
    title: tuple[Run, ...]
    line: int | None = None
    notes: tuple[Paragraph, ...] = field(default=(), kw_only=True)
    """The speaker notes (``::: notes`` of the heading): on every slide written for it."""
    transition: SlideTransition | None = field(default=None, kw_only=True)
    """How the slide comes in (E09-S03): of its heading or chapter; None: the deck's."""


@dataclass(frozen=True)
class TitleSlide(Slide):
    subtitle: tuple[Paragraph, ...] = ()
    layout: str | None = None


@dataclass(frozen=True)
class ChapterSlide(Slide):
    number: int = 1
    layout: str | None = None


@dataclass(frozen=True)
class ClosingSlide(Slide):
    layout: str | None = None


@dataclass(frozen=True)
class ContentSlide(Slide):
    body: tuple[Paragraph, ...] = ()


@dataclass(frozen=True)
class VisualSlide(Slide):
    above: tuple[Paragraph, ...] = ()
    visual: Visual | None = None
    below: tuple[Paragraph, ...] = ()


@dataclass(frozen=True)
class LayoutSlide(Slide):
    """A ``##`` slide on a layout named in its heading; content split at ``---``."""

    layout: str = ""
    segments: tuple[tuple[Item, ...], ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------- PTA slide kinds


@dataclass(frozen=True)
class AgendaSlide(Slide):
    """``## Agenda {.agenda}``: its list, or else the chapters of the deck, numbered 01, 02 …"""

    items: tuple[tuple[Run, ...], ...] = ()
    layout: str = ""


@dataclass(frozen=True)
class InterimSlide(Slide):
    """``## Statement {.interim}``: the heading alone on ``Zwischenfazit 01``/``02``."""

    layout: str = ""


@dataclass(frozen=True)
class QuoteSlide(Slide):
    """``## Quote {.quote}``: the heading on ``Zitat 01``/``02``, a paragraph under it as its
    source."""

    source: tuple[Run, ...] = ()
    layout: str = ""


@dataclass(frozen=True)
class Person:
    """A person of a contact slide: the ``###`` heading and the lines under it."""

    name: tuple[Run, ...]
    photo: Image | None = None
    function: tuple[Run, ...] = ()
    email: tuple[Run, ...] = ()
    phone: tuple[Run, ...] = ()


@dataclass(frozen=True)
class ContactSlide(Slide):
    """``## Contacts {.contact}``: one to five persons on ``Kontakt 0n``, or one person with
    text on ``Kontakt mit Text``."""

    persons: tuple[Person, ...] = ()
    text: tuple[Paragraph, ...] = ()
    layout: str = ""


@dataclass(frozen=True)
class ChartSlide(Slide):
    """One chart (``Titel und Diagramm``), two (``Titel und zwei Diagramme``), or one with text
    (``Titel, Text und Diagramm`` when the text comes first, else ``Titel, Diagramm und
    Text``)."""

    charts: tuple[Chart, ...] = ()
    text: tuple[Paragraph, ...] = ()
    text_first: bool = False


# ---------------------------------------------------------------------- flow slides


# The flow blocks carry the click they are built on as a whole (E09-S02); a text block has
# none, its paragraphs carry theirs.


@dataclass(frozen=True)
class TextBlock:
    paragraphs: tuple[Paragraph, ...]


@dataclass(frozen=True)
class CodeLinesBlock:
    """A code block no renderer took: its lines on a box of their own."""

    lines: tuple[str, ...]
    spans: tuple[CodeLine, ...] = ()
    """As ``Code.spans``."""
    click: Click | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class TableBlock:
    table: Table


@dataclass(frozen=True)
class ImageRowBlock:
    """One image, or a paragraph of nothing but images: side by side in cells of equal width."""

    images: tuple[Image, ...]


@dataclass(frozen=True)
class ColumnsBlock:
    """``::: columns``: its parts (split at ``---``) side by side, widths in the ratio of
    ``widths``."""

    widths: tuple[int, ...]
    columns: tuple[tuple[FlowBlock, ...], ...]
    click: Click | None = field(default=None, kw_only=True)
    clicks: tuple[Click | None, ...] = field(default=(), kw_only=True)
    """``{.build}``: the click of each column."""


@dataclass(frozen=True)
class Card:
    """A card: its ``###`` or bold title, an optional big figure, and its blocks."""

    title: tuple[Run, ...]
    figure: tuple[Run, ...] | None
    blocks: tuple[FlowBlock, ...]
    icon: str | None = field(default=None, kw_only=True)
    """The icon at the start of the title (E15-S03): the card's figure, drawn above the title."""
    click: Click | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class CardsBlock:
    """``::: cards``: boxes side by side, up to four to a row."""

    cards: tuple[Card, ...]
    click: Click | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class Row:
    term: tuple[Run, ...]
    description: tuple[Paragraph, ...]
    click: Click | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class RowsBlock:
    """``::: rows``: the term in the left third, its description beside it, a rule above each."""

    rows: tuple[Row, ...]
    click: Click | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class PanelBlock:
    """``::: panel`` or ``::: panel dark``: an area behind its blocks."""

    dark: bool
    blocks: tuple[FlowBlock, ...]
    click: Click | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class CalloutBlock:
    """``> [!NOTE]`` and the other alerts: an area with a bar on its left, yellow if
    ``important``."""

    important: bool
    blocks: tuple[FlowBlock, ...]
    click: Click | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class StatementBlock:
    """The first paragraph of ``::: statement``, set large."""

    text: tuple[Run, ...]
    click: Click | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class TagsBlock:
    """A paragraph of nothing but code spans: chips that flow and wrap."""

    tags: tuple[str, ...]
    click: Click | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class LabelledTag:
    label: str
    text: tuple[Run, ...]


@dataclass(frozen=True)
class LabelledTagsBlock:
    """A list in a container whose items start with a code span: the span as a chip, the rest
    beside it."""

    items: tuple[LabelledTag, ...]
    click: Click | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class ConclusionBlock:
    """``::: conclusion``: the PTA conclusion box at the foot of the content area."""

    paragraphs: tuple[Paragraph, ...]
    click: Click | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class CommentBlock:
    """``::: comment``: the PTA comment box, a speech bubble on the block before it."""

    paragraphs: tuple[Paragraph, ...]
    click: Click | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class ScheduleBlock:
    """``::: timeline`` or ``::: gantt`` (E15-S01): a group of editable shapes as wide as its
    place on the slide, as high as its content."""

    schedule: Schedule
    click: Click | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class StepsBlock:
    """``::: steps`` (E15-S02): a row of chevrons as wide as its place, as a group of shapes."""

    steps: Steps
    click: Click | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class RiskMatrixBlock:
    """``::: riskmatrix`` (E15-S02): the matrix as a group of shapes, its legend as a table
    to its right."""

    matrix: RiskMatrix
    legend: Table
    click: Click | None = field(default=None, kw_only=True)


FlowBlock = (
    TextBlock
    | CodeLinesBlock
    | TableBlock
    | ImageRowBlock
    | ColumnsBlock
    | CardsBlock
    | RowsBlock
    | PanelBlock
    | CalloutBlock
    | StatementBlock
    | TagsBlock
    | LabelledTagsBlock
    | CommentBlock
    | ScheduleBlock
    | StepsBlock
    | RiskMatrixBlock
)


@dataclass(frozen=True)
class FlowSlide(Slide):
    """A ``##`` section that uses the slide-layout Markdown (containers, alerts, tags, ``.dark``,
    ``kicker``): its blocks stacked top to bottom on ``Nur Titel``."""

    kicker: str | None = None
    dark: bool = False
    blocks: tuple[FlowBlock, ...] = ()
    conclusion: ConclusionBlock | None = None


def plain_text(runs: tuple[Run, ...]) -> str:
    return "".join(" " if r.is_break else r.text for r in runs).strip()


def trim(runs: list[Run]) -> list[Run]:
    """Without leading and trailing whitespace and breaks."""
    result = list(runs)
    while result and (result[0].is_break or not result[0].text.strip()):
        result.pop(0)
    while result and (result[-1].is_break or not result[-1].text.strip()):
        result.pop()
    if result:
        result[0] = replace(result[0], text=result[0].text.lstrip())
        result[-1] = replace(result[-1], text=result[-1].text.rstrip())
    return result
