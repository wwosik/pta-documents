"""A ``Drawing`` of the drawing model as a flowable: vector paths and text on the canvas (E05-S04).

Charts, Mermaid diagrams, financial charts, timelines, steps and risk matrices reach the PDF as a
``Drawing`` (CSS pixels from the top left). ``DrawingFlowable`` paints it with reportlab at
``POINTS_PER_PIXEL`` times ``scale``: shapes as paths (curves, dash patterns, round joins, the
even-odd rule), texts in the text font of the document (Segoe UI or Selawik, bold spans bold,
``mono`` lines in the code font) so that they can be searched and copied. A line with a
``max_width`` is measured with the real font and set smaller, down to ``MIN_TEXT_SCALE``, then
placed by its anchor; characters the fonts lack go through ``PdfFonts.shown`` like any text.
Tooltips and hotspots are for SVG only and left out. The painting was ported from the renderer
of E05-S01 (commit 175e572).
"""

from __future__ import annotations

import io
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Final

from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable

from pta_documents.design.fonts import FontFace
from pta_documents.drawing.model import (
    ClosePath,
    CubicTo,
    Drawing,
    DrawingHotspot,
    DrawingShape,
    DrawingText,
    LineTo,
    MoveTo,
    TextAnchor,
)
from pta_documents.generation.pdf.layout.fonts import PdfFonts

POINTS_PER_PIXEL: Final = 0.75
MIN_TEXT_SCALE: Final = 0.7
"""A line too wide for its ``max_width`` is set smaller, down to this share of its size."""
FILL_EVEN_ODD: Final = 0
FILL_NON_ZERO: Final = 1
"""The ``fillMode`` values of reportlab's ``drawPath``."""
ROUND: Final = 1
BUTT_CAP: Final = 0
MITER_JOIN: Final = 0


def _color(value: str) -> Any:
    return HexColor("#" + value)


class DrawingFlowable(Flowable):
    """``drawing`` at ``scale`` × 0.75 pt per pixel; it never splits."""

    def __init__(
        self,
        drawing: Drawing,
        fonts: PdfFonts,
        scale: float = 1.0,
        *,
        space_before: float = 0.0,
        space_after: float = 0.0,
        name: str = "",
    ) -> None:
        super().__init__()
        self.drawing = drawing
        self.fonts = fonts
        self.factor = POINTS_PER_PIXEL * scale
        self.width = drawing.width * self.factor
        self.height = drawing.height * self.factor
        self.spaceBefore = space_before
        self.spaceAfter = space_after
        self.hAlign = "LEFT"
        self.name = name
        """What the drawing is (the info string of its block), for messages."""
        # Measure every text now: characters the fonts lack fail while building the story.
        self.texts = {id(t): self._layout(t) for t in drawing.items if isinstance(t, DrawingText)}

    def wrap(self, aW: float, aH: float) -> tuple[float, float]:
        return self.width, self.height

    def split(self, availWidth: float, availHeight: float) -> list[Flowable]:
        return []

    def draw(self) -> None:
        canvas: Any = self.canv
        for item in self.drawing.items:
            match item:
                case DrawingShape():
                    self._shape(canvas, item)
                case DrawingText():
                    self._text(canvas, item)
                case DrawingHotspot():
                    pass

    # ------------------------------------------------------------------ geometry

    def x(self, value: float) -> float:
        return value * self.factor

    def y(self, value: float) -> float:
        """y mirrored here and nowhere else: the model counts down from the top."""
        return self.height - value * self.factor

    # ------------------------------------------------------------------ shapes

    def _shape(self, canvas: Any, shape: DrawingShape) -> None:
        fill = shape.fill is not None
        stroke = shape.stroke is not None and shape.stroke_width > 0
        if not shape.path.segments or (not fill and not stroke):
            return
        path = canvas.beginPath()
        for segment in shape.path.segments:
            match segment:
                case MoveTo(x, y):
                    path.moveTo(self.x(x), self.y(y))
                case LineTo(x, y):
                    path.lineTo(self.x(x), self.y(y))
                case CubicTo(x1, y1, x2, y2, x, y):
                    path.curveTo(
                        self.x(x1), self.y(y1), self.x(x2), self.y(y2), self.x(x), self.y(y)
                    )
                case ClosePath():
                    path.close()
        canvas.saveState()
        if shape.fill is not None:
            canvas.setFillColor(_color(shape.fill))
        if shape.stroke is not None:
            canvas.setStrokeColor(_color(shape.stroke))
            canvas.setLineWidth(shape.stroke_width * self.factor)
            canvas.setDash([d * self.factor for d in shape.dash] if shape.dash else [])
        canvas.setLineJoin(ROUND if shape.round_joins else MITER_JOIN)
        canvas.setLineCap(ROUND if shape.round_joins else BUTT_CAP)
        canvas.drawPath(
            path,
            stroke=int(stroke),
            fill=int(fill),
            fillMode=FILL_EVEN_ODD if shape.even_odd else FILL_NON_ZERO,
        )
        canvas.restoreState()

    # ------------------------------------------------------------------ texts

    def _face(self, text: DrawingText, bold: bool) -> FontFace:
        if text.mono:
            return FontFace.MONO_BOLD if bold else FontFace.MONO
        return FontFace.BOLD if bold else FontFace.REGULAR

    def _layout(self, text: DrawingText) -> tuple[float, float, list[tuple[str, FontFace, str]]]:
        """The size in points, the left edge in points and the spans as (text, face, colour)."""
        spans = [
            (self.fonts.shown(s.text, text.mono), self._face(text, s.bold), s.color or text.color)
            for s in text.spans
        ]
        size = text.size * self.factor

        def width(at: float) -> float:
            return sum(self.fonts.width(t, face, at) for t, face, _ in spans)

        measured = width(size)
        if text.max_width is not None and measured > text.max_width * self.factor > 0:
            size *= max(MIN_TEXT_SCALE, text.max_width * self.factor / measured)
            measured = width(size)
        left = self.x(text.x)
        match text.anchor:
            case TextAnchor.MIDDLE:
                left -= measured / 2
            case TextAnchor.END:
                left -= measured
            case TextAnchor.START:
                pass
        return size, left, spans

    def _text(self, canvas: Any, text: DrawingText) -> None:
        size, left, spans = self.texts[id(text)]
        if not any(t for t, _, _ in spans):
            return
        writer = canvas.beginText()
        writer.setTextOrigin(left, self.y(text.baseline))
        for content, face, color in spans:
            if not content:
                continue
            writer.setFont(self.fonts.name(face), size)
            writer.setFillColor(_color(color))
            writer.textOut(content)
        canvas.drawText(writer)


@dataclass(frozen=True)
class SceneImage:
    """A picture of a scene (E09-S04), drawn before the item ``index`` of the drawing: PNG or
    JPEG ``content`` of ``natural`` pixels, fitted into its box (pixels of the drawing), turned
    ``rotation`` degrees clockwise about the box's centre."""

    index: int
    content: bytes
    natural: tuple[float, float]
    box: tuple[float, float, float, float]
    rotation: float = 0.0


class SceneFlowable(DrawingFlowable):
    """A scene's still picture: its drawing with its images among the items, in their order."""

    def __init__(
        self,
        drawing: Drawing,
        images: Sequence[SceneImage],
        fonts: PdfFonts,
        scale: float = 1.0,
        *,
        space_before: float = 0.0,
        space_after: float = 0.0,
        name: str = "",
    ) -> None:
        super().__init__(
            drawing, fonts, scale, space_before=space_before, space_after=space_after, name=name
        )
        self.images = tuple(images)

    def draw(self) -> None:
        canvas: Any = self.canv
        for index, item in enumerate(self.drawing.items):
            self._images_at(canvas, index)
            match item:
                case DrawingShape():
                    self._shape(canvas, item)
                case DrawingText():
                    self._text(canvas, item)
                case DrawingHotspot():
                    pass
        self._images_at(canvas, len(self.drawing.items))

    def _images_at(self, canvas: Any, index: int) -> None:
        for image in self.images:
            if image.index == index:
                self._image(canvas, image)

    def _image(self, canvas: Any, image: SceneImage) -> None:
        x, y, w, h = image.box
        pixels_x, pixels_y = image.natural
        fit = min(w / pixels_x, h / pixels_y) if pixels_x > 0 and pixels_y > 0 else 0
        if fit <= 0:
            return
        width, height = pixels_x * fit * self.factor, pixels_y * fit * self.factor
        cx, cy = self.x(x + w / 2), self.y(y + h / 2)
        canvas.saveState()
        canvas.translate(cx, cy)
        if image.rotation:
            canvas.rotate(-image.rotation)  # clockwise on the page, where y runs up
        canvas.drawImage(
            ImageReader(io.BytesIO(image.content)),
            -width / 2,
            -height / 2,
            width,
            height,
            mask="auto",
        )
        canvas.restoreState()
