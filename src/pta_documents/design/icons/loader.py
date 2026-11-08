"""A bundled icon as a ``Drawing`` (E15-S03): its outlines stroked in one colour.

Reads the subset of SVG the Tabler icons use — ``<path>`` elements with ``d`` on a 24 × 24
``viewBox``, stroked by the root's ``stroke-width`` with round ends — through the path parser of
the SVG reader (``drawing.svg_geometry``, arcs become Bézier curves). The invisible bounding
square of every Tabler icon (``stroke="none"``) is left out; anything else is refused, so a new
icon that needs more is noticed in the tests.
"""

from __future__ import annotations

import xml.etree.ElementTree as ElementTree
from typing import Final

from pta_documents.design import icons
from pta_documents.drawing.model import (
    ClosePath,
    CubicTo,
    Drawing,
    DrawingPath,
    DrawingShape,
    LineTo,
    MoveTo,
    PathSegment,
)
from pta_documents.drawing.svg_geometry import path as parse_path

SVG_NS: Final = "http://www.w3.org/2000/svg"


def drawing(name: str, color: str, size: float = icons.GRID) -> Drawing:
    """The icon ``name`` as a ``Drawing`` of ``size`` × ``size`` CSS pixels: every outline
    stroked in ``color`` (``RRGGBB``), the line scaled with it, not filled.

    Raises ``KeyError`` for an unknown name and ``ValueError`` for SVG outside the subset."""
    scale = size / icons.GRID
    width = icons.STROKE_WIDTH * scale
    items = tuple(
        DrawingShape(
            DrawingPath(tuple(_scaled(segment, scale) for segment in outline)),
            None,
            color,
            width,
            round_joins=True,
        )
        for outline in outlines(name)
    )
    return Drawing(size, size, items)


def outlines(name: str) -> list[list[PathSegment]]:
    """The visible paths of the icon on its 24 × 24 grid."""
    root = ElementTree.fromstring(icons.svg(name))
    if root.tag != f"{{{SVG_NS}}}svg":
        raise ValueError(f"{name}.svg is not an SVG")
    view_box = root.get("viewBox", "")
    if view_box.split() != ["0", "0", str(icons.GRID), str(icons.GRID)]:
        raise ValueError(f"{name}.svg has the viewBox {view_box!r}, not 0 0 24 24")
    result: list[list[PathSegment]] = []
    for element in root:
        if element.tag != f"{{{SVG_NS}}}path":
            raise ValueError(f"{name}.svg: unexpected element {element.tag}")
        if element.get("stroke") == "none":
            continue  # the invisible square every Tabler icon starts with
        result.append(parse_path(element.get("d", "")))
    return result


def _scaled(segment: PathSegment, scale: float) -> PathSegment:
    match segment:
        case MoveTo(x, y):
            return MoveTo(x * scale, y * scale)
        case LineTo(x, y):
            return LineTo(x * scale, y * scale)
        case CubicTo(x1, y1, x2, y2, x, y):
            return CubicTo(x1 * scale, y1 * scale, x2 * scale, y2 * scale, x * scale, y * scale)
        case ClosePath():
            return segment
