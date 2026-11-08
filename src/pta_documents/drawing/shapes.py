"""Outlines of the shapes PowerPoint has as presets: chevrons and pie slices (E15-S02).

Each returns a ``DrawingShape`` whose ``path`` is the outline (for SVG and every output that
draws paths) and whose ``kind`` lets a deck use PowerPoint's own shape with the same geometry.
"""

from __future__ import annotations

import math

from pta_documents.drawing.model import (
    ClosePath,
    CubicTo,
    DrawingPath,
    DrawingShape,
    LineTo,
    MoveTo,
    PathSegment,
    ShapeKind,
)


def chevron(
    x: float,
    y: float,
    width: float,
    height: float,
    depth: float,
    fill: str | None,
    *,
    first: bool = False,
) -> DrawingShape:
    """An arrow pointing right, ``depth`` pixels deep at its point; with a notch of the same
    depth on its left, or straight there when it is the ``first`` of a row (a home plate)."""
    depth = min(depth, width)
    middle = y + height / 2
    notch = x if first else x + depth
    segments: list[PathSegment] = [
        MoveTo(x, y),
        LineTo(x + width - depth, y),
        LineTo(x + width, middle),
        LineTo(x + width - depth, y + height),
        LineTo(x, y + height),
        LineTo(notch, middle),
        ClosePath(),
    ]
    if first:
        # A straight left side: no point in the middle of it.
        segments.pop(5)
    return DrawingShape(
        DrawingPath(tuple(segments)),
        fill,
        None,
        0,
        kind=ShapeKind.HOME_PLATE if first else ShapeKind.CHEVRON,
        point_depth=depth,
    )


def pie(
    cx: float,
    cy: float,
    radius: float,
    start: float,
    end: float,
    fill: str | None,
) -> DrawingShape:
    """The slice of the circle around (``cx``, ``cy``) from ``start`` clockwise to ``end``,
    degrees from three o'clock (y grows downwards, so clockwise on screen)."""
    sweep = (end - start) % 360 or 360
    pieces = max(1, math.ceil(sweep / 90 - 1e-9))
    step = math.radians(sweep / pieces)
    k = 4 / 3 * math.tan(step / 4) * radius

    def at(angle: float) -> tuple[float, float]:
        return cx + radius * math.cos(angle), cy + radius * math.sin(angle)

    angle = math.radians(start)
    sx, sy = at(angle)
    segments: list[PathSegment] = [MoveTo(cx, cy), LineTo(sx, sy)]
    for _ in range(pieces):
        following = angle + step
        x0, y0 = at(angle)
        x1, y1 = at(following)
        segments.append(
            CubicTo(
                x0 - k * math.sin(angle),
                y0 + k * math.cos(angle),
                x1 + k * math.sin(following),
                y1 - k * math.cos(following),
                x1,
                y1,
            )
        )
        angle = following
    segments.append(ClosePath())
    return DrawingShape(
        DrawingPath(tuple(segments)),
        fill,
        None,
        0,
        kind=ShapeKind.PIE,
        angles=(start % 360, end % 360),
    )
