"""The vector drawing model: shapes, texts and hotspots that every output draws natively.

Port of DocLibs ``Drawing.cs``. Charts (E06), Mermaid diagrams (E06-S03), the visual building
blocks (E15) and the logos (``design.logos.drawing``) are a ``Drawing`` before PowerPoint writes
them as shapes, Word and PDF as vectors or pictures and ``to_svg`` as SVG.

Coordinates are CSS pixels (a pixel is 0.75 pt) from the top left corner; colours are RGB hex
``RRGGBB`` without ``#``, values of ``design.colors``. All types are frozen dataclasses holding
tuples, so drawings compare by content and can be hashed.
"""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from enum import StrEnum
from typing import NamedTuple

type Point = tuple[float, float]


@dataclass(frozen=True, slots=True)
class MoveTo:
    """Starts a subpath at a point."""

    x: float
    y: float

    @property
    def points(self) -> tuple[Point, ...]:
        return ((self.x, self.y),)


@dataclass(frozen=True, slots=True)
class LineTo:
    """A straight line to a point."""

    x: float
    y: float

    @property
    def points(self) -> tuple[Point, ...]:
        return ((self.x, self.y),)


@dataclass(frozen=True, slots=True)
class CubicTo:
    """A cubic Bézier curve through two control points to a point."""

    x1: float
    y1: float
    x2: float
    y2: float
    x: float
    y: float

    @property
    def points(self) -> tuple[Point, ...]:
        """The control points and the end point."""
        return ((self.x1, self.y1), (self.x2, self.y2), (self.x, self.y))


@dataclass(frozen=True, slots=True)
class ClosePath:
    """Closes the subpath with a straight line to its start."""

    @property
    def points(self) -> tuple[Point, ...]:
        return ()


type PathSegment = MoveTo | LineTo | CubicTo | ClosePath


class Bounds(NamedTuple):
    """An axis-aligned rectangle: the top left corner and the size."""

    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True, slots=True)
class DrawingPath:
    """An outline of straight and cubic Bézier segments; each subpath starts with a ``MoveTo``."""

    segments: tuple[PathSegment, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "segments", tuple(self.segments))

    @property
    def bounds(self) -> Bounds:
        """The smallest rectangle holding every point, control points included."""
        points = [point for segment in self.segments for point in segment.points]
        if not points:
            return Bounds(0, 0, 0, 0)
        left = min(x for x, _ in points)
        top = min(y for _, y in points)
        return Bounds(left, top, max(x for x, _ in points) - left, max(y for _, y in points) - top)

    @staticmethod
    def rectangle(x: float, y: float, width: float, height: float) -> DrawingPath:
        """A rectangle as a closed path, clockwise from the top left corner."""
        return DrawingPath(
            (
                MoveTo(x, y),
                LineTo(x + width, y),
                LineTo(x + width, y + height),
                LineTo(x, y + height),
                ClosePath(),
            )
        )


@dataclass(frozen=True, slots=True)
class DrawingHover:
    """A tooltip: its text (one line) and the point it is shown above, centred."""

    text: str
    x: float
    """The point the tooltip is centred over."""
    y: float
    """The point the tooltip's bottom sits above."""


class ShapeKind(StrEnum):
    """What a shape is, so decks can use PowerPoint's own shapes for the common ones."""

    PATH = "path"
    """Any outline."""
    RECTANGLE = "rectangle"
    """An axis-aligned rectangle."""
    ROUNDED_RECTANGLE = "rounded-rectangle"
    """An axis-aligned rectangle with corners of ``corner_radius``."""
    ELLIPSE = "ellipse"
    """An axis-aligned ellipse or circle."""


class TextAnchor(StrEnum):
    """Where ``DrawingText.x`` is on the line."""

    START = "start"
    """At the start: the text runs right from it."""
    MIDDLE = "middle"
    END = "end"


@dataclass(frozen=True, slots=True)
class DrawingShape:
    """An outline, filled and stroked.

    ``path`` always holds the outline, whatever ``kind`` says, so an output that does not know
    the kind can draw it; ``kind`` only lets an output use its own shape (rectangle, ellipse).
    """

    path: DrawingPath
    fill: str | None
    """The fill colour; None: not filled."""
    stroke: str | None
    """The line colour; None: no line."""
    stroke_width: float
    """The line width in pixels."""
    _: KW_ONLY
    dash: tuple[float, ...] | None = None
    """Dash and gap lengths in pixels, alternating; None: a solid line."""
    kind: ShapeKind = ShapeKind.PATH
    corner_radius: float = 0
    """The corner radius of a ``ShapeKind.ROUNDED_RECTANGLE``, in pixels."""
    round_joins: bool = False
    """Whether line ends and corners are round rather than butt and mitred."""
    even_odd: bool = False
    """Fill rule ``evenodd`` instead of ``nonzero`` (PTA addition: EMF logos, Mermaid SVGs)."""
    hover: DrawingHover | None = None
    """A tooltip, in SVG only; PowerPoint and PDF ignore it."""

    def __post_init__(self) -> None:
        if self.dash is not None:
            object.__setattr__(self, "dash", tuple(self.dash))


@dataclass(frozen=True, slots=True)
class DrawingSpan:
    """A piece of a ``DrawingText`` in one weight."""

    text: str
    bold: bool = False
    color: str | None = None
    """The span's colour; None: the colour of its line."""


@dataclass(frozen=True, slots=True)
class DrawingText:
    """One line of text in the PTA text font.

    Widths are measured when the drawing is placed, so text is never laid out in pixels here.
    """

    x: float
    """The anchor point, see ``anchor``."""
    baseline: float
    spans: tuple[DrawingSpan, ...]
    size: float
    """The font size in pixels."""
    color: str
    _: KW_ONLY
    anchor: TextAnchor = TextAnchor.START
    max_width: float | None = None
    """The room the line has, in pixels: wider text is drawn smaller, down to 70 % of ``size``,
    and overflows beyond that. None: never shrunk."""
    mono: bool = False
    """Whether the line is in the mono font, like code."""
    hover: DrawingHover | None = None
    """A tooltip, in SVG only; PowerPoint and PDF ignore it."""

    def __post_init__(self) -> None:
        object.__setattr__(self, "spans", tuple(self.spans))

    @staticmethod
    def line(
        x: float,
        baseline: float,
        text: str,
        size: float,
        color: str,
        *,
        bold: bool = False,
        anchor: TextAnchor = TextAnchor.START,
        max_width: float | None = None,
        mono: bool = False,
        hover: DrawingHover | None = None,
    ) -> DrawingText:
        """A line in one weight."""
        return DrawingText(
            x,
            baseline,
            (DrawingSpan(text, bold),),
            size,
            color,
            anchor=anchor,
            max_width=max_width,
            mono=mono,
            hover=hover,
        )

    @property
    def text(self) -> str:
        """The whole line."""
        return "".join(span.text for span in self.spans)


@dataclass(frozen=True, slots=True)
class DrawingHotspot:
    """An invisible circle that only carries a ``hover``, such as a point on a line.

    SVG draws it as a transparent hit area, with a dot of ``dot`` shown while hovered; decks and
    PDFs skip it.
    """

    x: float
    y: float
    radius: float
    """The radius of the hit area in pixels."""
    _: KW_ONLY
    dot: str | None = None
    """The colour of the dot shown while hovered; None: no dot."""
    dot_radius: float = 4
    hover: DrawingHover | None = None


type DrawingItem = DrawingShape | DrawingText | DrawingHotspot


@dataclass(frozen=True, slots=True)
class Drawing:
    """A vector drawing, such as a diagram, in CSS pixels from the top left corner."""

    width: float
    height: float
    items: tuple[DrawingItem, ...]
    """Shapes, texts and hotspots, drawn in order: later items cover earlier ones."""

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))
