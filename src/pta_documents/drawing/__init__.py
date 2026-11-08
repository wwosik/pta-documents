"""The vector drawing model (``Drawing``) and its SVG output with tooltips (E02-S03).

Renderers build a ``Drawing`` (charts, diagrams, visual building blocks); the generators place it
as shapes, vectors or pictures. ``to_svg`` writes it as a standalone SVG for web pages and as the
first step towards PNG. Pure Python, part of the core: no extra needed.
"""

from pta_documents.drawing.model import (
    Bounds,
    ClosePath,
    CubicTo,
    Drawing,
    DrawingHotspot,
    DrawingHover,
    DrawingItem,
    DrawingPath,
    DrawingShape,
    DrawingSpan,
    DrawingText,
    LineTo,
    MoveTo,
    PathSegment,
    Point,
    ShapeKind,
    TextAnchor,
)
from pta_documents.drawing.svg_output import SvgOptions, estimate_width, to_svg

__all__ = [
    "Bounds",
    "ClosePath",
    "CubicTo",
    "Drawing",
    "DrawingHotspot",
    "DrawingHover",
    "DrawingItem",
    "DrawingPath",
    "DrawingShape",
    "DrawingSpan",
    "DrawingText",
    "LineTo",
    "MoveTo",
    "PathSegment",
    "Point",
    "ShapeKind",
    "SvgOptions",
    "TextAnchor",
    "estimate_width",
    "to_svg",
]
