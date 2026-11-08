"""SVG → ``Drawing``: the SVG of a diagram as shapes and texts of the drawing model.

Port of DocLibs ``SvgDrawing.cs`` (E06-S03), widened for the SVG mermaid-cli writes: the basic
shapes, paths, markers (arrowheads, with a ``viewBox`` too), text with ``tspan`` lines and bold
spans, groups with transforms (also the CSS ``transform`` with ``transform-origin``), the
cascade of ``<style>`` rules (``svg_style.Cascade``), ``currentColor``, ``fill-rule`` and
``dominant-baseline``. Drop shadows (``filter``) are left out — drawings have none. Anything
else — an element, attribute value or CSS function it does not know, ``foreignObject``
included — raises ``SvgDrawingError`` rather than being dropped.

Part of the core; only an SVG with CSS rules beyond ``svg { … }`` needs ``cssselect`` (extra
``diagrams``), which is imported when such a rule is read.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterator
from dataclasses import dataclass, replace
from typing import Final

from lxml import etree

from pta_documents.drawing import svg_geometry as geometry
from pta_documents.drawing.model import (
    ClosePath,
    Drawing,
    DrawingItem,
    DrawingPath,
    DrawingShape,
    DrawingSpan,
    DrawingText,
    MoveTo,
    PathSegment,
    Point,
    ShapeKind,
    TextAnchor,
)
from pta_documents.drawing.svg_geometry import Affine, SvgDrawingError
from pta_documents.drawing.svg_style import (
    ROOT_FONT_SIZE,
    Cascade,
    Color,
    SvgStyle,
    named,
    on_white,
    unsupported,
)

__all__ = ["SvgDrawingError", "to_drawing"]

SVG_NAMESPACE: Final = "http://www.w3.org/2000/svg"
SKIPPED: Final = frozenset(
    {
        "style",
        "defs",
        "marker",
        "linearGradient",
        "radialGradient",
        "title",
        "desc",
        "metadata",
        "filter",
        "symbol",
    }
)
"""Elements that hold no drawing of their own; markers and gradients are read where they are
used, symbols only through ``<use>`` (which raises), filters (drop shadows) never."""
SHAPES: Final = frozenset({"rect", "circle", "ellipse", "polygon", "polyline", "path", "line"})
LABEL_GROUP_CLASSES: Final = frozenset({"node", "edge-label"})
"""Groups whose text has the room of the group's first shape (``DrawingText.max_width``)."""
BASELINE_SHIFT: Final = {
    "auto": 0.0,
    "alphabetic": 0.0,
    "baseline": 0.0,
    "central": 0.35,
    "middle": 0.35,
    "hanging": 0.8,
    "text-before-edge": 0.8,
    "before-edge": 0.8,
    "text-after-edge": -0.2,
    "after-edge": -0.2,
    "ideographic": -0.2,
}
"""How far ``dominant-baseline``/``alignment-baseline`` move the alphabetic baseline down, in
em: a deck has no font metrics, these are the usual values of a sans-serif font."""
BLACK: Final = named("black") or "0" * 6

_URL: Final = re.compile(r"^url\(\s*['\"]?#([^)'\"\s]+)['\"]?\s*\)$")
_PERCENT: Final = re.compile(r"^\s*[-+]?(?:\d+\.?\d*|\.\d+)\s*%\s*$")


def to_drawing(svg: str | bytes) -> Drawing:
    """The drawing of ``svg``; ``SvgDrawingError`` when it has something that cannot be drawn,
    or is not well-formed."""
    content = svg.encode("utf-8") if isinstance(svg, str) else svg
    if re.search(rb"<!DOCTYPE", content, re.IGNORECASE):
        raise SvgDrawingError("The diagram's SVG has a DOCTYPE, which is not read.")
    parser = etree.XMLParser(
        resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False
    )
    try:
        root = etree.fromstring(content, parser)
    except etree.XMLSyntaxError as error:
        raise SvgDrawingError(f"The diagram's SVG is not well-formed: {error}") from error
    if root.tag != f"{{{SVG_NAMESPACE}}}svg":
        raise SvgDrawingError("The diagram's SVG has no <svg> root.")
    for element in root.iter():
        if _is_element(element) and element.tag.startswith(f"{{{SVG_NAMESPACE}}}"):
            element.tag = etree.QName(element).localname
    style_sheet = "".join(e.text or "" for e in root.iter("style"))
    style = SvgStyle.read(root.get("style"), style_sheet)
    converter = _Converter(style, Cascade(root, style_sheet), root)
    return converter.convert()


@dataclass(frozen=True, slots=True)
class _Paint:
    """The inherited presentation properties; colours are None for ``none``."""

    fill: Color | None
    stroke: Color | None
    stroke_width: float
    dash: tuple[float, ...] | None
    round_joins: bool
    font_size: float
    bold: bool
    anchor: TextAnchor
    fill_opacity: float
    stroke_opacity: float
    color: Color
    even_odd: bool
    baseline: str

    @staticmethod
    def initial() -> _Paint:
        """SVG's initial values: black fill, no stroke, 16 px text."""
        return _Paint(
            (BLACK, 1.0),
            None,
            1,
            None,
            False,
            ROOT_FONT_SIZE,
            False,
            TextAnchor.START,
            1,
            1,
            (BLACK, 1.0),
            False,
            "auto",
        )

    @property
    def fill_color(self) -> str | None:
        return _resolved(self.fill, self.fill_opacity)

    @property
    def stroke_color(self) -> str | None:
        return _resolved(self.stroke, self.stroke_opacity)


def _resolved(color: Color | None, opacity: float) -> str | None:
    if color is None:
        return None
    return on_white(color[0], color[1] * opacity)


class _Converter:
    def __init__(self, style: SvgStyle, cascade: Cascade, root: etree._Element) -> None:
        self.style = style
        self.cascade = cascade
        self.root = root
        self.items: list[DrawingItem] = []
        for gradient in root.iter("linearGradient", "radialGradient"):
            identifier = gradient.get("id")
            stops = gradient.findall("stop")
            if identifier and stops:
                self.style.gradients[identifier] = self.declared(stops[0], "stop-color") or "black"
        self.markers: dict[str, etree._Element] = {}
        for marker in root.iter("marker"):
            identifier = marker.get("id")
            if identifier and identifier not in self.markers:
                self.markers[identifier] = marker

    def convert(self) -> Drawing:
        root = self.root
        view_box = _numbers(root.get("viewBox")) if root.get("viewBox") else None
        if view_box is not None and len(view_box) != 4:
            raise unsupported("viewBox", root.get("viewBox") or "")
        width = self._size(root, "width", view_box[2] if view_box else None)
        height = self._size(root, "height", view_box[3] if view_box else None)
        view = Affine.identity()
        if view_box is not None and view_box[2] > 0 and view_box[3] > 0:
            min_x, min_y, box_width, box_height = view_box
            view = Affine.scale_by(width / box_width, height / box_height).then(
                Affine.translate(-min_x, -min_y)
            )
        paint = self.paint(_Paint.initial(), root)
        self.children(root, paint, view, None)
        return Drawing(width, height, tuple(self.items))

    def _size(self, root: etree._Element, name: str, fallback: float | None) -> float:
        """The root's width or height: its attribute, or the viewBox for none or a
        percentage (an SVG as wide as its container is as wide as its viewBox)."""
        value = root.get(name)
        if value is not None and not _PERCENT.match(value):
            return self.style.length(value)
        if fallback is None:
            raise SvgDrawingError(f"The diagram's SVG has no {name}.")
        return fallback

    # ------------------------------------------------------------------ cascade

    def declared(self, element: etree._Element, name: str) -> str | None:
        return self.cascade.value(element, name)

    def number(
        self, element: etree._Element, name: str, font_size: float = ROOT_FONT_SIZE
    ) -> float:
        value = element.get(name)
        return self.style.length(value, font_size) if value is not None else 0.0

    def paint(self, inherited: _Paint, element: etree._Element) -> _Paint:
        paint = inherited
        declared = self.declared
        size = declared(element, "font-size")
        if size is not None and size != "inherit":
            paint = replace(paint, font_size=self.style.length(size, inherited.font_size))
        color = declared(element, "color")
        if color is not None and color != "inherit":
            resolved = self.style.paint(color, inherited.color)
            paint = replace(paint, color=resolved if resolved is not None else inherited.color)
        opacity = _opacity(declared(element, "opacity"))
        fill_opacity = declared(element, "fill-opacity")
        if fill_opacity is not None:
            paint = replace(paint, fill_opacity=_opacity(fill_opacity))
        stroke_opacity = declared(element, "stroke-opacity")
        if stroke_opacity is not None:
            paint = replace(paint, stroke_opacity=_opacity(stroke_opacity))
        fill = declared(element, "fill")
        if fill is not None and fill != "inherit":
            paint = replace(paint, fill=self.style.paint(fill, paint.color))
        stroke = declared(element, "stroke")
        if stroke is not None and stroke != "inherit":
            paint = replace(paint, stroke=self.style.paint(stroke, paint.color))
        width = declared(element, "stroke-width")
        if width is not None and width != "inherit":
            paint = replace(paint, stroke_width=self.style.length(width, paint.font_size))
        dash = declared(element, "stroke-dasharray")
        if dash is not None and dash != "inherit":
            paint = replace(paint, dash=self._dash(dash, paint.font_size))
        join = declared(element, "stroke-linejoin")
        if join is not None and join != "inherit":
            paint = replace(paint, round_joins=join == "round")
        weight = declared(element, "font-weight")
        if weight is not None and weight != "inherit":
            paint = replace(paint, bold=_is_bold(weight))
        anchor = declared(element, "text-anchor")
        if anchor is not None and anchor != "inherit":
            paint = replace(paint, anchor=_anchor(anchor))
        rule = declared(element, "fill-rule")
        if rule is not None and rule != "inherit":
            paint = replace(paint, even_odd=rule == "evenodd")
        baseline = declared(element, "dominant-baseline") or declared(element, "alignment-baseline")
        if baseline is not None and baseline != "inherit":
            if baseline not in BASELINE_SHIFT:
                raise unsupported("dominant-baseline", baseline)
            paint = replace(paint, baseline=baseline)
        # Drawings have no transparency: a translucent colour is mixed with white instead.
        if opacity != 1:
            paint = replace(
                paint,
                fill_opacity=paint.fill_opacity * opacity,
                stroke_opacity=paint.stroke_opacity * opacity,
            )
        return paint

    def _dash(self, value: str, font_size: float) -> tuple[float, ...] | None:
        if value == "none":
            return None
        lengths = [self.style.length(v, font_size) for v in re.split(r"[\s,]+", value.strip()) if v]
        if len(lengths) % 2 == 1:
            lengths = lengths + lengths
        if not lengths or all(length == 0 for length in lengths[1::2]):
            return None  # no gaps: a solid line
        return tuple(lengths)

    def transform_of(self, element: etree._Element) -> Affine:
        """The element's own transform: the attribute, or the CSS property, about its
        ``transform-origin``."""
        value = self.declared(element, "transform")
        own = geometry.transform(value)
        origin = self.declared(element, "transform-origin")
        if origin is None or own == Affine.identity():
            return own
        parts = origin.split()
        if len(parts) != 2:
            raise unsupported("transform-origin", origin)
        ox, oy = (self.style.length(p) for p in parts)
        return Affine.translate(ox, oy).then(own).then(Affine.translate(-ox, -oy))

    # ------------------------------------------------------------------ elements

    def children(
        self, parent: etree._Element, inherited: _Paint, transform: Affine, room: float | None
    ) -> None:
        for element in parent:
            if not _is_element(element):
                continue  # comments and processing instructions
            name = element.tag
            if name.startswith("{"):
                raise unsupported_element(f"<{etree.QName(element).localname}>")
            if name in SKIPPED or self._hidden(element):
                continue
            for reference in ("clip-path", "mask"):
                value = self.declared(element, reference)
                if value is not None and value != "none":
                    raise unsupported_element(f"a {reference}")
            paint = self.paint(inherited, element)
            local = transform.then(self.transform_of(element))
            match name:
                case "g":
                    inner = self.room(element, local) if _is_label_group(element) else room
                    self.children(element, paint, local, inner)
                case "rect":
                    self._rect(element, paint, local)
                case "circle":
                    r = self.number(element, "r")
                    outline = geometry.ellipse(
                        self.number(element, "cx"), self.number(element, "cy"), r, r
                    )
                    self.shape(paint, local, outline, ShapeKind.ELLIPSE)
                case "ellipse":
                    outline = geometry.ellipse(
                        self.number(element, "cx"),
                        self.number(element, "cy"),
                        self.number(element, "rx"),
                        self.number(element, "ry"),
                    )
                    self.shape(paint, local, outline, ShapeKind.ELLIPSE)
                case "line":
                    outline: list[PathSegment] = [
                        MoveTo(self.number(element, "x1"), self.number(element, "y1")),
                        geometry.LineTo(self.number(element, "x2"), self.number(element, "y2")),
                    ]
                    self.marked(element, replace(paint, fill=None), local, outline)
                case "polyline":
                    self.marked(
                        element,
                        paint,
                        local,
                        geometry.points(element.get("points", ""), close=False),
                    )
                case "polygon":
                    self.marked(
                        element,
                        paint,
                        local,
                        geometry.points(element.get("points", ""), close=True),
                    )
                case "path":
                    self.marked(element, paint, local, geometry.path(element.get("d", "")))
                case "text":
                    self.text(element, paint, local, room)
                case _:
                    raise unsupported_element(f"<{name}>")

    def _hidden(self, element: etree._Element) -> bool:
        return self.declared(element, "display") == "none" or self.declared(
            element, "visibility"
        ) in ("hidden", "collapse")

    def _rect(self, element: etree._Element, paint: _Paint, transform: Affine) -> None:
        x, y = self.number(element, "x"), self.number(element, "y")
        w, h = self.number(element, "width"), self.number(element, "height")
        rx_value = self.declared(element, "rx")
        ry_value = self.declared(element, "ry")
        rx = self.style.length(rx_value) if rx_value not in (None, "auto") else None
        ry = self.style.length(ry_value) if ry_value not in (None, "auto") else None
        rx, ry = (rx if rx is not None else ry or 0.0), (ry if ry is not None else rx or 0.0)
        if w <= 0 or h <= 0:
            return
        if rx <= 0 or ry <= 0:
            kind = ShapeKind.RECTANGLE
        elif rx == ry:
            kind = ShapeKind.ROUNDED_RECTANGLE
        else:
            kind = ShapeKind.PATH
        self.shape(
            paint, transform, geometry.rectangle(x, y, w, h, rx, ry), kind, min(rx, min(w, h) / 2)
        )

    def marked(
        self, element: etree._Element, paint: _Paint, transform: Affine, outline: list[PathSegment]
    ) -> None:
        """A shape that may carry markers."""
        mid = self.declared(element, "marker-mid")
        if mid is not None and mid != "none":
            raise unsupported_element("marker-mid")
        self.shape(paint, transform, outline, ShapeKind.PATH)
        self.marker(element, "marker-start", outline, paint, transform)
        self.marker(element, "marker-end", outline, paint, transform)

    def shape(
        self,
        paint: _Paint,
        transform: Affine,
        outline: list[PathSegment],
        kind: ShapeKind,
        radius: float = 0,
    ) -> None:
        fill = paint.fill_color
        stroke = paint.stroke_color if paint.stroke_width > 0 else None
        if not outline or (fill is None and stroke is None):
            return
        aligned = transform.is_axis_aligned
        self.items.append(
            DrawingShape(
                DrawingPath(tuple(transform.apply_segment(s) for s in outline)),
                fill,
                stroke,
                0 if stroke is None else paint.stroke_width * transform.scale,
                dash=None
                if stroke is None or paint.dash is None
                else tuple(d * transform.scale for d in paint.dash),
                kind=kind if aligned else ShapeKind.PATH,
                corner_radius=radius * transform.scale
                if kind is ShapeKind.ROUNDED_RECTANGLE and aligned
                else 0,
                round_joins=paint.round_joins,
                even_odd=paint.even_odd and fill is not None,
            )
        )

    def marker(
        self,
        element: etree._Element,
        attribute: str,
        outline: list[PathSegment],
        paint: _Paint,
        transform: Affine,
    ) -> None:
        """The marker's content placed at the path's start or end, turned along the path for
        ``orient="auto"``; a marker ``viewBox`` is fitted into ``markerWidth`` ×
        ``markerHeight`` (``xMidYMid meet``)."""
        value = self.declared(element, attribute)
        if value is None or value == "none":
            return
        match = _URL.match(value)
        marker = self.markers.get(match.group(1)) if match else None
        if marker is None:
            raise unsupported_element(f"the {attribute} '{value}'")
        at_start = attribute == "marker-start"
        found = _start(outline) if at_start else _end(outline)
        if found is None:
            return
        (x, y), (dx, dy) = found
        direction = math.degrees(math.atan2(dy, dx))
        orient = marker.get("orient", "0")
        if orient == "auto":
            angle = direction
        elif orient == "auto-start-reverse":
            angle = direction + 180 if at_start else direction
        else:
            try:
                angle = float(orient.removesuffix("deg"))
            except ValueError as error:
                raise unsupported_element(f"the marker orient '{orient}'") from error
        units = 1.0 if marker.get("markerUnits") == "userSpaceOnUse" else paint.stroke_width
        content = Affine.identity()
        view_box = marker.get("viewBox")
        if view_box is not None:
            numbers = _numbers(view_box)
            if len(numbers) != 4 or numbers[2] <= 0 or numbers[3] <= 0:
                raise unsupported("marker viewBox", view_box)
            ratio = marker.get("preserveAspectRatio")
            if ratio not in (None, "xMidYMid meet", "xMidYMid"):
                raise unsupported_element(f"a marker with preserveAspectRatio '{ratio}'")
            min_x, min_y, box_width, box_height = numbers
            width = self.number(marker, "markerWidth") if marker.get("markerWidth") else 3.0
            height = self.number(marker, "markerHeight") if marker.get("markerHeight") else 3.0
            scale = min(width / box_width, height / box_height)
            content = (
                Affine.translate((width - box_width * scale) / 2, (height - box_height * scale) / 2)
                .then(Affine.scale_by(scale, scale))
                .then(Affine.translate(-min_x, -min_y))
            )
        ref_x, ref_y = content.apply(self.number(marker, "refX"), self.number(marker, "refY"))
        placed = (
            transform.then(Affine.translate(x, y))
            .then(Affine.rotate(angle))
            .then(Affine.scale_by(units, units))
            .then(Affine.translate(-ref_x, -ref_y))
            .then(content)
        )
        self.children(marker, self.paint(_Paint.initial(), marker), placed, None)

    def text(
        self, element: etree._Element, paint: _Paint, transform: Affine, room: float | None
    ) -> None:
        """Each line — the text, and every ``tspan`` positioned with ``x``, ``y`` or ``dy`` —
        becomes a ``DrawingText``; nested tspans with a weight become bold spans, a positioned
        tspan's size, colour, anchor and baseline are its line's. Whitespace collapses as SVG
        collapses it."""
        if not transform.is_axis_aligned:
            raise unsupported_element("rotated text")
        mono = "mono" in (element.get("class") or "").split()
        lines: list[tuple[float, float, list[DrawingSpan], _Paint]] = []
        x = self.number(element, "x", paint.font_size)
        y = self.number(element, "y", paint.font_size) + self.number(element, "dy", paint.font_size)
        spans: list[DrawingSpan] = []
        line_paint = paint

        def flush() -> None:
            nonlocal spans
            if spans:
                lines.append((x, y, spans, line_paint))
                spans = []

        def walk(container: etree._Element, container_paint: _Paint) -> None:
            nonlocal x, y, line_paint
            if container.text:
                spans.append(DrawingSpan(container.text, container_paint.bold))
            for node in container:
                if _is_element(node):
                    if node.tag != "tspan":
                        raise unsupported_element(
                            f"the element <{etree.QName(node).localname}> in text"
                        )
                    if self._hidden(node):
                        pass
                    else:
                        inner = self.paint(container_paint, node)
                        positioned = any(node.get(a) is not None for a in ("x", "y", "dy"))
                        if positioned:
                            flush()
                            size = inner.font_size
                            if node.get("x") is not None:
                                x = self.number(node, "x", size)
                            if node.get("y") is not None:
                                y = self.number(node, "y", size)
                            y += self.number(node, "dy", size)
                            line_paint = inner
                        walk(node, inner)
                        if positioned:
                            flush()
                            line_paint = paint
                if node.tail:
                    spans.append(DrawingSpan(node.tail, container_paint.bold))

        walk(element, paint)
        flush()
        for line_x, line_y, line_spans, painted in lines:
            color = painted.fill_color
            collapsed = _collapse(line_spans)
            if color is None or not collapsed:
                continue
            baseline = line_y + BASELINE_SHIFT[painted.baseline] * painted.font_size
            px, py = transform.apply(line_x, baseline)
            self.items.append(
                DrawingText(
                    px,
                    py,
                    tuple(collapsed),
                    painted.font_size * transform.scale,
                    color,
                    anchor=painted.anchor,
                    max_width=room,
                    mono=mono,
                )
            )

    def room(self, group: etree._Element, transform: Affine) -> float | None:
        """The width a node's or edge label's text has inside its shape: the first shape of
        the group, less padding."""
        shape = next((e for e in group if _is_element(e) and e.tag in SHAPES), None)
        if shape is None:
            return None
        width: float | None
        match shape.tag:
            case "rect":
                width = self.number(shape, "width") - 16
            case "circle":
                width = 2 * self.number(shape, "r") - 16
            case "ellipse":
                width = 2 * self.number(shape, "rx") - 16
            case "polygon":
                corners = geometry.points(shape.get("points", ""), close=False)
                bounds = DrawingPath(tuple(corners)).bounds
                # A diamond: its width at the height of one line of text.
                width = bounds.width * 0.7 if len(corners) == 4 else bounds.width - 24
            case "path":
                width = DrawingPath(tuple(geometry.path(shape.get("d", "")))).bounds.width - 16
            case _:
                width = None
        return width * transform.scale if width is not None and width > 0 else None


def _is_element(node: etree._Element) -> bool:
    """Whether ``node`` is an element, not a comment, processing instruction or entity."""
    return not isinstance(node, etree._Comment | etree._ProcessingInstruction | etree._Entity)


def unsupported_element(what: str) -> SvgDrawingError:
    return SvgDrawingError(f"The diagram's SVG has {what}, which cannot be drawn.")


def _is_label_group(group: etree._Element) -> bool:
    return any(c in LABEL_GROUP_CLASSES for c in (group.get("class") or "").split())


def _numbers(value: str | None) -> list[float]:
    try:
        return [float(n) for n in re.split(r"[\s,]+", (value or "").strip()) if n]
    except ValueError as error:
        raise unsupported("number list", value or "") from error


def _opacity(value: str | None) -> float:
    if value is None or value == "inherit":
        return 1.0
    try:
        number = float(value[:-1]) / 100 if value.endswith("%") else float(value)
    except ValueError as error:
        raise unsupported("opacity", value) from error
    return min(1.0, max(0.0, number))


def _is_bold(weight: str) -> bool:
    if weight in ("bold", "bolder"):
        return True
    if weight in ("normal", "lighter", ""):
        return False
    try:
        return int(weight) >= 600
    except ValueError as error:
        raise unsupported("font-weight", weight) from error


def _anchor(value: str) -> TextAnchor:
    match value:
        case "middle":
            return TextAnchor.MIDDLE
        case "end":
            return TextAnchor.END
        case "start":
            return TextAnchor.START
        case _:
            raise unsupported("text-anchor", value)


def _collapse(spans: list[DrawingSpan]) -> list[DrawingSpan]:
    """Whitespace runs become one space, the line is trimmed, and neighbouring spans of one
    weight are merged."""
    result: list[DrawingSpan] = []
    previous_space = True
    for span in spans:
        text: list[str] = []
        for character in span.text:
            space = character.isspace()
            if not (space and previous_space):
                text.append(" " if space else character)
            previous_space = space
        if not text:
            continue
        if result and result[-1].bold == span.bold:
            result[-1] = DrawingSpan(result[-1].text + "".join(text), span.bold)
        else:
            result.append(DrawingSpan("".join(text), span.bold))
    if result:
        result[-1] = DrawingSpan(result[-1].text.rstrip(), result[-1].bold)
        if not result[-1].text:
            result.pop()
    return result


def _segment_points(segment: PathSegment, subpath_start: Point) -> tuple[Point, ...]:
    return (subpath_start,) if isinstance(segment, ClosePath) else segment.points


def _start(outline: list[PathSegment]) -> tuple[Point, Point] | None:
    """The point and direction where a path starts."""
    if not outline or not isinstance(outline[0], MoveTo):
        return None
    start = outline[0]
    for segment in outline[1:]:
        for px, py in segment.points:
            if px != start.x or py != start.y:
                return (start.x, start.y), (px - start.x, py - start.y)
        if isinstance(segment, MoveTo):
            break
    return None


def _end(outline: list[PathSegment]) -> tuple[Point, Point] | None:
    """The point and direction where a path ends: along the last control point (or the
    segment's start) that differs from the end."""
    current: Point = (0.0, 0.0)
    subpath_start: Point = (0.0, 0.0)
    result: tuple[Point, Point] | None = None
    for segment in outline:
        points = _segment_points(segment, subpath_start)
        if isinstance(segment, MoveTo):
            current = subpath_start = points[0]
            continue
        end = points[-1]
        before: Iterator[Point] = reversed((current, *points[:-1]))
        start = next((p for p in before if p != end), end)
        if start != end:
            result = (end, (end[0] - start[0], end[1] - start[1]))
        current = end
    return result
