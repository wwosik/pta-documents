"""A ``Drawing`` as a group of editable shapes on a slide (port of DocLibs ``DrawingWriter.cs``).

PowerPoint's own rectangles, rounded rectangles and ellipses where the drawing says so, custom
geometry for every other outline, and a text box per line in Segoe UI. Hotspots (tooltips) are
left out: slides have no hover. Used by the financial charts (E06-S02) and Mermaid (E06-S03).
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Final

from lxml import etree
from pptx.slide import Slide as PptxSlide

from pta_documents.design import slides as design
from pta_documents.drawing.model import (
    ClosePath,
    CubicTo,
    Drawing,
    DrawingHotspot,
    DrawingShape,
    DrawingText,
    LineTo,
    MoveTo,
    ShapeKind,
    TextAnchor,
)

A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
EMU_PER_PIXEL: Final = 9525
"""A pixel at 96 dpi (0.75 pt)."""
CHARACTER_WIDTH: Final = 0.5
"""A deck has no font metrics: text is estimated at half its size per character."""
MIN_TEXT_SCALE: Final = 0.7
POINTS_PER_PIXEL: Final = 0.75
MITER_LIMIT: Final = 800_000
"""How far a mitred corner may reach, in thousandths of a percent of the line width."""
ANGLE_UNIT: Final = 60000
"""PowerPoint's angles are in 60000ths of a degree."""
FULL_CIRCLE: Final = 360 * ANGLE_UNIT
GROUP_NAME: Final = "Drawing"
"""The start of the name of every group this writes (``Drawing 12``); the PPTX converter leaves
such groups out."""


def a(name: str) -> str:
    return f"{{{A}}}{name}"


def p(name: str) -> str:
    return f"{{{P}}}{name}"


def fit(drawing: Drawing, width: int, height: int) -> tuple[int, int, float]:
    """The size of ``drawing`` fitted into ``width`` × ``height`` EMU — scaled down, never up —
    and the EMU per pixel it is drawn at."""
    scale = min(
        1.0, width / (drawing.width * EMU_PER_PIXEL), height / (drawing.height * EMU_PER_PIXEL)
    )
    per_pixel = EMU_PER_PIXEL * scale
    return int(drawing.width * per_pixel), int(drawing.height * per_pixel), per_pixel


def place(
    slide: PptxSlide,
    drawing: Drawing,
    left: int,
    top: int,
    width: int,
    height: int,
    alt: str,
    lang: str,
    name: str | None = None,
) -> int:
    """``drawing`` fitted into the box, centred horizontally at its top; returns its height.
    ``name``: the group's name instead of ``Drawing <id>`` (a Harvey ball, E15-S02)."""
    used_width, used_height, per_pixel = fit(drawing, width, height)
    x = left + (width - used_width) // 2
    tree = slide.shapes._spTree
    ids = [int(e.get("id", "0")) for e in tree.iter(p("cNvPr"))]
    counter = iter(range(max(ids, default=1) + 1, 1 << 31))
    tree.append(group(drawing, x, top, per_pixel, lambda: next(counter), alt, lang, name))
    return used_height


def group(
    drawing: Drawing,
    x: int,
    y: int,
    per_pixel: float,
    next_id: Callable[[], int],
    alt: str,
    lang: str,
    name: str | None = None,
) -> etree._Element:
    """The group of shapes, its top left corner at (``x``, ``y``) EMU, ``per_pixel`` EMU a
    pixel, named ``name`` or ``Drawing <id>``."""

    def to_x(px: float) -> int:
        return x + round(px * per_pixel)

    def to_y(px: float) -> int:
        return y + round(px * per_pixel)

    width = max(1, int(drawing.width * per_pixel))
    height = max(1, int(drawing.height * per_pixel))
    number = next_id()
    element = etree.Element(p("grpSp"), nsmap={"a": A, "p": P})
    properties = etree.SubElement(element, p("nvGrpSpPr"))
    etree.SubElement(
        properties, p("cNvPr"), id=str(number), name=name or f"{GROUP_NAME} {number}", descr=alt
    )
    etree.SubElement(properties, p("cNvGrpSpPr"))
    etree.SubElement(properties, p("nvPr"))
    transform = etree.SubElement(etree.SubElement(element, p("grpSpPr")), a("xfrm"))
    etree.SubElement(transform, a("off"), x=str(x), y=str(y))
    etree.SubElement(transform, a("ext"), cx=str(width), cy=str(height))
    etree.SubElement(transform, a("chOff"), x=str(x), y=str(y))
    etree.SubElement(transform, a("chExt"), cx=str(width), cy=str(height))
    for item in drawing.items:
        match item:
            case DrawingShape():
                element.append(_shape(item, next_id(), to_x, to_y, per_pixel))
            case DrawingText():
                element.append(_text(item, next_id(), to_x, to_y, per_pixel, lang))
            case DrawingHotspot():
                pass
    return element


def _properties(parent: etree._Element, number: int, name: str, text_box: bool) -> None:
    properties = etree.SubElement(parent, p("nvSpPr"))
    etree.SubElement(properties, p("cNvPr"), id=str(number), name=f"{name} {number}")
    shape = etree.SubElement(properties, p("cNvSpPr"))
    if text_box:
        shape.set("txBox", "1")
    etree.SubElement(properties, p("nvPr"))


def _transform(parent: etree._Element, left: int, top: int, width: int, height: int) -> None:
    transform = etree.SubElement(parent, a("xfrm"))
    etree.SubElement(transform, a("off"), x=str(left), y=str(top))
    etree.SubElement(transform, a("ext"), cx=str(width), cy=str(height))


def _preset(parent: etree._Element, name: str, *adjust: tuple[str, int]) -> None:
    geometry = etree.SubElement(parent, a("prstGeom"), prst=name)
    values = etree.SubElement(geometry, a("avLst"))
    for guide, value in adjust:
        etree.SubElement(values, a("gd"), name=guide, fmla=f"val {value}")


def _solid(parent: etree._Element, color: str) -> None:
    etree.SubElement(etree.SubElement(parent, a("solidFill")), a("srgbClr"), val=color)


def _shape(
    shape: DrawingShape,
    number: int,
    to_x: Callable[[float], int],
    to_y: Callable[[float], int],
    per_pixel: float,
) -> etree._Element:
    bx, by, bw, bh = _pie_bounds(shape) if shape.kind is ShapeKind.PIE else shape.path.bounds
    left, top = to_x(bx), to_y(by)
    width = max(1, to_x(bx + bw) - left)
    height = max(1, to_y(by + bh) - top)
    element = etree.Element(p("sp"))
    names = {
        ShapeKind.RECTANGLE: "Rectangle",
        ShapeKind.ROUNDED_RECTANGLE: "Rounded Rectangle",
        ShapeKind.ELLIPSE: "Ellipse",
        ShapeKind.PATH: "Freeform",
        ShapeKind.CHEVRON: "Chevron",
        ShapeKind.HOME_PLATE: "Pentagon",
        ShapeKind.PIE: "Pie",
    }
    _properties(element, number, names[shape.kind], text_box=False)
    properties = etree.SubElement(element, p("spPr"))
    _transform(properties, left, top, width, height)
    match shape.kind:
        case ShapeKind.RECTANGLE:
            _preset(properties, "rect")
        case ShapeKind.ELLIPSE:
            _preset(properties, "ellipse")
        case ShapeKind.ROUNDED_RECTANGLE:
            share = shape.corner_radius / max(min(bw, bh), 0.001) * 100000
            _preset(properties, "roundRect", ("adj", int(min(max(share, 0), 50000))))
        case ShapeKind.CHEVRON | ShapeKind.HOME_PLATE:
            # The depth of the point in thousandths of a percent of the shorter side.
            share = shape.point_depth / max(min(bw, bh), 0.001) * 100000
            limit = bw / max(min(bw, bh), 0.001) * 100000
            preset = "chevron" if shape.kind is ShapeKind.CHEVRON else "homePlate"
            _preset(properties, preset, ("adj", int(min(max(share, 0), limit))))
        case ShapeKind.PIE:
            start, end = shape.angles or (0, 0)
            # Angles in 60000ths of a degree, clockwise from three o'clock.
            _preset(
                properties,
                "pie",
                ("adj1", round(start * ANGLE_UNIT) % FULL_CIRCLE),
                ("adj2", round(end * ANGLE_UNIT) % FULL_CIRCLE),
            )
        case ShapeKind.PATH:
            _custom_geometry(properties, shape, left, top, width, height, to_x, to_y)
    if shape.fill is not None:
        _solid(properties, shape.fill)
    else:
        etree.SubElement(properties, a("noFill"))
    _outline(properties, shape, per_pixel)
    return element


def _pie_bounds(shape: DrawingShape) -> tuple[float, float, float, float]:
    """The square around the whole circle of a pie slice (PowerPoint's ``pie`` is drawn in it):
    its path starts at the centre and goes to the circle (``drawing.shapes.pie``)."""
    points = [point for segment in shape.path.segments[:2] for point in segment.points]
    if len(points) < 2:
        return shape.path.bounds
    (cx, cy), (x, y) = points[0], points[1]
    radius = math.hypot(x - cx, y - cy)
    return cx - radius, cy - radius, 2 * radius, 2 * radius


def _custom_geometry(
    parent: etree._Element,
    shape: DrawingShape,
    left: int,
    top: int,
    width: int,
    height: int,
    to_x: Callable[[float], int],
    to_y: Callable[[float], int],
) -> None:
    """Path coordinates are EMU relative to the shape, so the geometry stretches with it."""
    geometry = etree.SubElement(parent, a("custGeom"))
    for name in ("avLst", "gdLst", "ahLst", "cxnLst"):
        etree.SubElement(geometry, a(name))
    etree.SubElement(geometry, a("rect"), l="l", t="t", r="r", b="b")
    path = etree.SubElement(etree.SubElement(geometry, a("pathLst")), a("path"))
    path.set("w", str(width))
    path.set("h", str(height))
    if shape.fill is None:
        path.set("fill", "none")

    def point(parent: etree._Element, px: float, py: float) -> None:
        etree.SubElement(parent, a("pt"), x=str(to_x(px) - left), y=str(to_y(py) - top))

    for segment in shape.path.segments:
        match segment:
            case MoveTo(x, y):
                point(etree.SubElement(path, a("moveTo")), x, y)
            case LineTo(x, y):
                point(etree.SubElement(path, a("lnTo")), x, y)
            case CubicTo(x1, y1, x2, y2, x, y):
                curve = etree.SubElement(path, a("cubicBezTo"))
                point(curve, x1, y1)
                point(curve, x2, y2)
                point(curve, x, y)
            case ClosePath():
                etree.SubElement(path, a("close"))


def _outline(parent: etree._Element, shape: DrawingShape, per_pixel: float) -> None:
    line = etree.SubElement(parent, a("ln"))
    if shape.stroke is None or shape.stroke_width <= 0:
        etree.SubElement(line, a("noFill"))
        return
    line.set("w", str(max(1, round(shape.stroke_width * per_pixel))))
    if shape.round_joins:
        line.set("cap", "rnd")
    _solid(line, shape.stroke)
    if shape.dash:
        # Custom dashes are in thousandths of a percent of the line width.
        dashes = etree.SubElement(line, a("custDash"))
        lengths = shape.dash
        for i in range(0, max(len(lengths), 1), 2):
            gap = lengths[i + 1] if i + 1 < len(lengths) else lengths[i]
            etree.SubElement(
                dashes,
                a("ds"),
                d=str(round(lengths[i] / shape.stroke_width * 100000)),
                sp=str(round(gap / shape.stroke_width * 100000)),
            )
    if shape.round_joins:
        etree.SubElement(line, a("round"))
    else:
        etree.SubElement(line, a("miter"), lim=str(MITER_LIMIT))


def _text(
    text: DrawingText,
    number: int,
    to_x: Callable[[float], int],
    to_y: Callable[[float], int],
    per_pixel: float,
    lang: str,
) -> etree._Element:
    """A text box without insets or wrapping, as wide as the estimated text, aligned by the
    anchor; its top is the baseline less the ascent."""
    size = text.size
    estimate = len(text.text) * size * CHARACTER_WIDTH
    if text.max_width is not None and estimate > text.max_width:
        size *= max(MIN_TEXT_SCALE, text.max_width / estimate)
        estimate = len(text.text) * size * CHARACTER_WIDTH
    width = max(estimate, text.max_width or 0)
    match text.anchor:
        case TextAnchor.MIDDLE:
            left = text.x - width / 2
        case TextAnchor.END:
            left = text.x - width
        case TextAnchor.START:
            left = text.x
    top = text.baseline - size * 0.95
    element = etree.Element(p("sp"))
    _properties(element, number, "Text", text_box=True)
    properties = etree.SubElement(element, p("spPr"))
    box_width = max(1, int(width * per_pixel))
    box_height = max(1, int(size * 1.25 * per_pixel))
    _transform(properties, to_x(left), to_y(top), box_width, box_height)
    _preset(properties, "rect")
    etree.SubElement(properties, a("noFill"))
    body = etree.SubElement(element, p("txBody"))
    body_properties = etree.SubElement(
        body, a("bodyPr"), wrap="none", lIns="0", tIns="0", rIns="0", bIns="0", anchor="t"
    )
    etree.SubElement(body_properties, a("noAutofit"))
    etree.SubElement(body, a("lstStyle"))
    paragraph = etree.SubElement(body, a("p"))
    alignment = {TextAnchor.START: "l", TextAnchor.MIDDLE: "ctr", TextAnchor.END: "r"}
    etree.SubElement(paragraph, a("pPr"), algn=alignment[text.anchor])
    # Points scale with the group: a pixel is 0.75 pt at 9525 EMU a pixel.
    points = size * POINTS_PER_PIXEL * per_pixel / EMU_PER_PIXEL
    font = design.CODE_FONT if text.mono else design.HEADING_FONT
    for span in text.spans:
        run = etree.SubElement(paragraph, a("r"))
        run_properties = etree.SubElement(
            run, a("rPr"), lang=lang, sz=str(max(100, round(points * 100)))
        )
        if span.bold:
            run_properties.set("b", "1")
        _solid(run_properties, span.color or text.color)
        etree.SubElement(run_properties, a("latin"), typeface=font)
        etree.SubElement(run, a("t")).text = _xml_safe(span.text)
    return element


def _xml_safe(text: str) -> str:
    """Text without the control characters XML 1.0 has no place for."""
    return "".join(c for c in text if c in "\t\n\r" or ord(c) >= 0x20)
