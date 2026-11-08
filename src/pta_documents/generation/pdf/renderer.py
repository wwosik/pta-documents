"""Draw a ``Layout`` with reportlab: port of DocLibs ``PdfRenderer.cs``.

The renderer only draws what the layout placed; it measures nothing. The result is a plain
PDF — ``pdfa.to_pdfa`` makes it PDF/A-2b. reportlab subsets the TrueType fonts itself (no
copies per 255 characters as in DocLibs) and runs in its invariant mode, so equal input gives
equal bytes. The canvas starts in the regular text face, so none of the 14 standard fonts is
ever referenced.
"""

from __future__ import annotations

import io
import math
from collections.abc import Sequence
from typing import Any, Final

from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as reportlab_canvas

from pta_documents.design.fonts import SYNTHETIC_ITALIC_ANGLE, FontFace
from pta_documents.drawing.model import ClosePath, CubicTo, LineTo, MoveTo
from pta_documents.generation.pdf.fonts import PdfFonts
from pta_documents.generation.pdf.metadata import PRODUCER, PdfInfo
from pta_documents.generation.pdf.page_model import (
    Bookmark,
    ImageItem,
    Layout,
    LineItem,
    LinkItem,
    PageItem,
    RectItem,
    ShapeItem,
    TextItem,
)

CANVAS: Final[Any] = reportlab_canvas.Canvas
"""reportlab is untyped; its inferred parameter types are wrong (``initialFontName``)."""
FILL_EVEN_ODD: Final = 0
FILL_NON_ZERO: Final = 1
"""The ``fillMode`` values of reportlab's ``drawPath``."""
ROUND_JOIN: Final = 1
MITER_JOIN: Final = 0
_SLANT: Final = math.tan(math.radians(SYNTHETIC_ITALIC_ANGLE))


def render(layout: Layout, fonts: PdfFonts, info: PdfInfo) -> bytes:
    """The pages of ``layout`` as PDF bytes (not yet PDF/A)."""
    output = io.BytesIO()
    geometry = layout.geometry
    canvas = CANVAS(
        output,
        pagesize=(geometry.width, geometry.height),
        invariant=1,
        pageCompression=1,
        initialFontName=fonts.name(FontFace.REGULAR),
        initialFontSize=10,
    )
    canvas.setTitle(info.title or "")
    canvas.setAuthor(info.author or "")
    canvas.setSubject(info.subject or "")
    canvas.setCreator(PRODUCER)
    canvas.setProducer(PRODUCER)
    anchors = _anchor_keys(layout)
    bookmarks = list(enumerate(layout.bookmarks))
    images: dict[bytes, Any] = {}
    for number, page in enumerate(layout.pages):
        painter = _Painter(canvas, fonts, geometry.height, anchors, images)
        for item in page.items:
            painter.draw(item)
        for anchor in page.anchors:
            canvas.bookmarkHorizontal(anchors[anchor.name], 0, geometry.height - anchor.y)
        for index, bookmark in bookmarks:
            if bookmark.page == number:
                canvas.bookmarkHorizontal(_bookmark_key(index), 0, geometry.height - bookmark.y)
        canvas.showPage()
    for index, level in enumerate(nest(layout.bookmarks)):
        canvas.addOutlineEntry(layout.bookmarks[index].title, _bookmark_key(index), level)
    if layout.bookmarks:
        canvas.showOutline()
    canvas.save()
    return output.getvalue()


def nest(bookmarks: Sequence[Bookmark]) -> list[int]:
    """The outline level (0 = top) of each bookmark: port of DocLibs ``Nest``.

    A bookmark is at most one level below the one before it, so a ``###`` right after a ``#``
    hangs under the ``#`` instead of under a missing ``##``.
    """
    levels: list[int] = []
    previous = -1
    for bookmark in bookmarks:
        level = max(0, min(bookmark.level - 1, previous + 1))
        levels.append(level)
        previous = level
    return levels


def _bookmark_key(index: int) -> str:
    return f"bookmark-{index}"


def _anchor_keys(layout: Layout) -> dict[str, str]:
    """A PDF destination name per anchor; an unknown link target is a layout bug."""
    keys: dict[str, str] = {}
    for page in layout.pages:
        for anchor in page.anchors:
            keys.setdefault(anchor.name, f"anchor-{len(keys)}")
    for page in layout.pages:
        for item in page.items:
            if isinstance(item, LinkItem) and item.target is not None and item.target not in keys:
                raise ValueError(f"the link target {item.target!r} is no anchor of the layout")
    return keys


def _color(value: str) -> Any:
    return HexColor("#" + value)


class _Painter:
    """Draws the items of one page; y is mirrored here and nowhere else."""

    def __init__(
        self,
        canvas: Any,
        fonts: PdfFonts,
        height: float,
        anchors: dict[str, str],
        images: dict[bytes, Any],
    ) -> None:
        self.canvas = canvas
        self.fonts = fonts
        self.height = height
        self.anchors = anchors
        self.images = images

    def y(self, value: float) -> float:
        return self.height - value

    def draw(self, item: PageItem) -> None:
        match item:
            case TextItem():
                self.text(item)
            case LineItem():
                self.line(item)
            case RectItem():
                self.rect(item)
            case ImageItem():
                self.image(item)
            case ShapeItem():
                self.shape(item)
            case LinkItem():
                self.link(item)

    def text(self, item: TextItem) -> None:
        if not item.text:
            return
        text = self.canvas.beginText()
        text.setFont(self.fonts.name(item.face), item.size)
        text.setFillColor(_color(item.color))
        if self.fonts.synthetic_italic(item.face):
            text.setTextTransform(1, 0, _SLANT, 1, item.x, self.y(item.baseline))
        else:
            text.setTextOrigin(item.x, self.y(item.baseline))
        text.textOut(item.text)
        self.canvas.drawText(text)

    def _stroke(self, color: str, width: float, dash: tuple[float, ...] | None) -> None:
        self.canvas.setStrokeColor(_color(color))
        self.canvas.setLineWidth(width)
        self.canvas.setDash(list(dash) if dash else [])

    def line(self, item: LineItem) -> None:
        self._stroke(item.color, item.width, item.dash)
        self.canvas.line(item.x1, self.y(item.y1), item.x2, self.y(item.y2))

    def rect(self, item: RectItem) -> None:
        fill = item.fill is not None
        stroke = item.stroke is not None and item.stroke_width > 0
        if not fill and not stroke:
            return
        if item.fill is not None:
            self.canvas.setFillColor(_color(item.fill))
        if item.stroke is not None:
            self._stroke(item.stroke, item.stroke_width, None)
        bottom = self.y(item.y + item.height)
        if item.corner_radius > 0:
            self.canvas.roundRect(
                item.x,
                bottom,
                item.width,
                item.height,
                item.corner_radius,
                stroke=int(stroke),
                fill=int(fill),
            )
        else:
            self.canvas.rect(
                item.x, bottom, item.width, item.height, stroke=int(stroke), fill=int(fill)
            )

    def image(self, item: ImageItem) -> None:
        reader = self.images.get(item.content)
        if reader is None:
            reader = ImageReader(io.BytesIO(item.content))
            self.images[item.content] = reader
        self.canvas.drawImage(
            reader, item.x, self.y(item.y + item.height), item.width, item.height, mask="auto"
        )

    def shape(self, item: ShapeItem) -> None:
        fill = item.fill is not None
        stroke = item.stroke is not None and item.stroke_width > 0
        if not item.segments or (not fill and not stroke):
            return
        path = self.canvas.beginPath()
        for segment in item.segments:
            match segment:
                case MoveTo(x, y):
                    path.moveTo(x, self.y(y))
                case LineTo(x, y):
                    path.lineTo(x, self.y(y))
                case CubicTo(x1, y1, x2, y2, x, y):
                    path.curveTo(x1, self.y(y1), x2, self.y(y2), x, self.y(y))
                case ClosePath():
                    path.close()
        self.canvas.saveState()
        if item.fill is not None:
            self.canvas.setFillColor(_color(item.fill))
        if item.stroke is not None:
            self._stroke(item.stroke, item.stroke_width, item.dash)
        self.canvas.setLineJoin(ROUND_JOIN if item.round_joins else MITER_JOIN)
        self.canvas.drawPath(
            path,
            stroke=int(stroke),
            fill=int(fill),
            fillMode=FILL_EVEN_ODD if item.even_odd else FILL_NON_ZERO,
        )
        self.canvas.restoreState()

    def link(self, item: LinkItem) -> None:
        rect = (item.x, self.y(item.y + item.height), item.x + item.width, self.y(item.y))
        if item.url is not None:
            self.canvas.linkURL(item.url, rect, relative=0, thickness=0)
        elif item.target is not None:
            self.canvas.linkRect("", self.anchors[item.target], Rect=rect, relative=0, thickness=0)
