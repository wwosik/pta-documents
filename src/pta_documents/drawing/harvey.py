"""A Harvey ball as a ``Drawing`` (E15-S02): a circle with a dark blue rim, filled in PTA blue
``quarters`` quarters clockwise from twelve o'clock (``[3/4]`` in a table cell)."""

from __future__ import annotations

from typing import Final

from pta_documents.design import colors
from pta_documents.drawing.model import Drawing, DrawingItem, DrawingPath, DrawingShape, ShapeKind
from pta_documents.drawing.schedule import px
from pta_documents.drawing.shapes import pie
from pta_documents.drawing.svg_geometry import ellipse

DIAMETER: Final = px(0.45 / 2.54 * 72)
"""0.45 cm."""
RIM: Final = px(1)
"""The rim: 1 pt."""
TWELVE: Final = 270
"""Twelve o'clock in degrees clockwise from three o'clock."""
QUARTERS: Final = 4


def ball(quarters: int, diameter: float = DIAMETER) -> Drawing:
    """The ball filled ``quarters`` (0 to 4) quarters, ``diameter`` pixels wide."""
    if not 0 <= quarters <= QUARTERS:
        raise ValueError(f"a Harvey ball has 0 to {QUARTERS} quarters, not {quarters}")
    r = (diameter - RIM) / 2
    c = diameter / 2

    def circle(fill: str | None, stroke: str | None, width: float) -> DrawingShape:
        return DrawingShape(
            DrawingPath(tuple(ellipse(c, c, r, r))), fill, stroke, width, kind=ShapeKind.ELLIPSE
        )

    items: list[DrawingItem] = []
    if quarters == QUARTERS:
        items.append(circle(colors.PTA_BLUE, None, 0))
    else:
        items.append(circle(colors.WHITE, None, 0))
        if quarters:
            items.append(pie(c, c, r, TWELVE, TWELVE + quarters * 90, colors.PTA_BLUE))
    items.append(circle(None, colors.DARK_BLUE, RIM))
    return Drawing(diameter, diameter, tuple(items))
