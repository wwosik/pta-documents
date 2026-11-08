"""The laid-out pages the renderer draws: port of DocLibs ``PageModel.cs``.

A ``Layout`` is what a layout engine hands the renderer — every item already placed, nothing
left to measure. Units are points (1/72 inch), the origin is the top left corner of the page and
y grows downwards (the renderer mirrors it for PDF). Colours are ``RRGGBB`` values of
``design.colors``. Paths use the segments of the drawing model (``drawing.model``, E02-S03).
All types are frozen dataclasses holding tuples.
"""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import Final

from pta_documents.design import colors
from pta_documents.design.fonts import FontFace
from pta_documents.design.variants import Orientation
from pta_documents.drawing.model import PathSegment

POINTS_PER_CM: Final = 72 / 2.54
A4_WIDTH: Final = 21.0 * POINTS_PER_CM
A4_HEIGHT: Final = 29.7 * POINTS_PER_CM


@dataclass(frozen=True, slots=True)
class TextItem:
    """One run of text in one face: ``x`` is its left edge, ``baseline`` its baseline."""

    x: float
    baseline: float
    text: str
    face: FontFace
    size: float
    _: KW_ONLY
    color: str = colors.TEXT_WORD


@dataclass(frozen=True, slots=True)
class LineItem:
    """A straight line from (``x1``, ``y1``) to (``x2``, ``y2``)."""

    x1: float
    y1: float
    x2: float
    y2: float
    width: float
    color: str
    _: KW_ONLY
    dash: tuple[float, ...] | None = None


@dataclass(frozen=True, slots=True)
class RectItem:
    """A rectangle from its top left corner; ``fill`` and ``stroke`` may each be None."""

    x: float
    y: float
    width: float
    height: float
    fill: str | None
    _: KW_ONLY
    stroke: str | None = None
    stroke_width: float = 0
    corner_radius: float = 0


@dataclass(frozen=True, slots=True)
class ImageItem:
    """A PNG or JPEG image stretched over the rectangle; equal ``content`` is embedded once."""

    x: float
    y: float
    width: float
    height: float
    content: bytes


@dataclass(frozen=True, slots=True)
class ShapeItem:
    """A path in page coordinates, filled and/or stroked."""

    segments: tuple[PathSegment, ...]
    fill: str | None
    stroke: str | None
    stroke_width: float
    _: KW_ONLY
    dash: tuple[float, ...] | None = None
    round_joins: bool = False
    even_odd: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "segments", tuple(self.segments))


@dataclass(frozen=True, slots=True)
class LinkItem:
    """A clickable rectangle: to ``url`` (external) or to the ``Anchor`` named ``target``."""

    x: float
    y: float
    width: float
    height: float
    _: KW_ONLY
    url: str | None = None
    target: str | None = None

    def __post_init__(self) -> None:
        if (self.url is None) == (self.target is None):
            raise ValueError("a link needs exactly one of url and target")


type PageItem = TextItem | LineItem | RectItem | ImageItem | ShapeItem | LinkItem


@dataclass(frozen=True, slots=True)
class Anchor:
    """A place internal links jump to: ``name`` (e.g. a heading's slug) at height ``y``."""

    name: str
    y: float


@dataclass(frozen=True, slots=True)
class LaidOutPage:
    items: tuple[PageItem, ...] = ()
    anchors: tuple[Anchor, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))
        object.__setattr__(self, "anchors", tuple(self.anchors))


@dataclass(frozen=True, slots=True)
class Bookmark:
    """An outline entry: ``level`` 1 is the top; it opens ``page`` (index) at height ``y``."""

    title: str
    level: int
    page: int
    y: float


@dataclass(frozen=True, slots=True)
class PageGeometry:
    """The page size and the margins that frame the text area, in points."""

    width: float
    height: float
    left: float
    top: float
    right: float
    bottom: float

    @property
    def text_width(self) -> float:
        return self.width - self.left - self.right

    @property
    def text_height(self) -> float:
        return self.height - self.top - self.bottom

    @staticmethod
    def a4(
        orientation: Orientation, left: float, top: float, right: float, bottom: float
    ) -> PageGeometry:
        """A4 in ``orientation`` with the margins given in points."""
        if orientation is Orientation.PORTRAIT:
            return PageGeometry(A4_WIDTH, A4_HEIGHT, left, top, right, bottom)
        return PageGeometry(A4_HEIGHT, A4_WIDTH, left, top, right, bottom)


@dataclass(frozen=True, slots=True)
class Layout:
    """All pages of a document; every page has the same ``geometry``."""

    geometry: PageGeometry
    pages: tuple[LaidOutPage, ...]
    bookmarks: tuple[Bookmark, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "pages", tuple(self.pages))
        object.__setattr__(self, "bookmarks", tuple(self.bookmarks))
        if not self.pages:
            raise ValueError("a layout has at least one page")
