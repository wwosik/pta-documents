"""The outline of a DrawingML shape as SVG path data, in CSS pixels of its box.

The preset geometries the PTA template and the PPTX generator use are drawn as PowerPoint draws
them (``rect``, ``roundRect``, ``ellipse``, ``line``, ``pie``, ``chevron``, ``homePlate``,
``wedgeRectCallout``, ``triangle``); any other preset falls back to its box. Custom geometry
(``a:custGeom``) is read path by path, with numeric points as the template writes them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

from pta_documents.generation.html.ooxml import Element, a, integer, local, number

FULL_CIRCLE: Final = 21600000
"""60 000ths of a degree in a circle."""


@dataclass(frozen=True)
class Outline:
    """One path of a shape: its data, and whether it is filled and stroked."""

    data: str
    filled: bool = True
    stroked: bool = True
    closed: bool = True
    """Ends in ``Z``: a line has no arrow heads then."""


def outlines(sp_pr: Element | None, width: float, height: float) -> list[Outline]:
    """The paths of the geometry in ``sp_pr`` (``p:spPr``) for a box of ``width`` × ``height``;
    a box without geometry is a rectangle."""
    geometry = sp_pr.find(a("custGeom")) if sp_pr is not None else None
    if geometry is not None:
        return custom(geometry, width, height)
    preset_geometry = sp_pr.find(a("prstGeom")) if sp_pr is not None else None
    name = preset_geometry.get("prst", "rect") if preset_geometry is not None else "rect"
    adjust = _adjustments(preset_geometry)
    return [preset(name, adjust, width, height)]


def is_line(sp_pr: Element | None) -> bool:
    geometry = sp_pr.find(a("prstGeom")) if sp_pr is not None else None
    return geometry is not None and geometry.get("prst") in ("line", "straightConnector1")


def preset_name(sp_pr: Element | None) -> str:
    geometry = sp_pr.find(a("prstGeom")) if sp_pr is not None else None
    if geometry is not None:
        return geometry.get("prst", "rect")
    return "custom" if sp_pr is not None and sp_pr.find(a("custGeom")) is not None else "rect"


def _adjustments(geometry: Element | None) -> dict[str, float]:
    result: dict[str, float] = {}
    if geometry is None:
        return result
    for guide in geometry.iterfind(f"{a('avLst')}/{a('gd')}"):
        formula = guide.get("fmla", "").split()
        if len(formula) == 2 and formula[0] == "val":
            try:
                result[guide.get("name", "")] = float(formula[1])
            except ValueError:
                continue
    return result


def _points(points: list[tuple[float, float]]) -> str:
    return "M" + " L".join(f"{number(x)} {number(y)}" for x, y in points) + " Z"


def preset(name: str, adjust: dict[str, float], w: float, h: float) -> Outline:
    short = min(w, h)
    if name in ("line", "straightConnector1"):
        return Outline(f"M0 0 L{number(w)} {number(h)}", filled=False, closed=False)
    if name == "ellipse":
        rx, ry = w / 2, h / 2
        return Outline(
            f"M0 {number(ry)} A{number(rx)} {number(ry)} 0 1 1 {number(w)} {number(ry)} "
            f"A{number(rx)} {number(ry)} 0 1 1 0 {number(ry)} Z"
        )
    if name == "roundRect":
        radius = short * adjust.get("adj", 16667) / 100000
        rr = number(radius)
        return Outline(
            f"M{rr} 0 H{number(w - radius)} A{rr} {rr} 0 0 1 {number(w)} {rr} "
            f"V{number(h - radius)} A{rr} {rr} 0 0 1 {number(w - radius)} {number(h)} "
            f"H{rr} A{rr} {rr} 0 0 1 0 {number(h - radius)} V{rr} A{rr} {rr} 0 0 1 {rr} 0 Z"
        )
    if name == "pie":
        return _pie(adjust.get("adj1", 0), adjust.get("adj2", 16200000), w, h)
    if name == "chevron":
        point = short * adjust.get("adj", 50000) / 100000
        return Outline(
            _points([(0, 0), (w - point, 0), (w, h / 2), (w - point, h), (0, h), (point, h / 2)])
        )
    if name == "homePlate":
        point = short * adjust.get("adj", 50000) / 100000
        return Outline(_points([(0, 0), (w - point, 0), (w, h / 2), (w - point, h), (0, h)]))
    if name == "triangle":
        apex = w * adjust.get("adj", 50000) / 100000
        return Outline(_points([(apex, 0), (w, h), (0, h)]))
    if name == "wedgeRectCallout":
        return _callout(adjust.get("adj1", -20833), adjust.get("adj2", 62500), w, h)
    return Outline(_points([(0, 0), (w, 0), (w, h), (0, h)]))


def _pie(start: float, end: float, w: float, h: float) -> Outline:
    rx, ry = w / 2, h / 2
    first = math.radians(start / 60000)
    sweep = (end - start) % FULL_CIRCLE
    last = first + math.radians(sweep / 60000)
    x1, y1 = rx + rx * math.cos(first), ry + ry * math.sin(first)
    x2, y2 = rx + rx * math.cos(last), ry + ry * math.sin(last)
    large = 1 if sweep > FULL_CIRCLE / 2 else 0
    return Outline(
        f"M{number(rx)} {number(ry)} L{number(x1)} {number(y1)} "
        f"A{number(rx)} {number(ry)} 0 {large} 1 {number(x2)} {number(y2)} Z"
    )


def _callout(dx: float, dy: float, w: float, h: float) -> Outline:
    """A rectangle with a wedge to the tip (``dx``, ``dy`` in 100 000ths from the centre): the
    wedge leaves the side nearest the tip, between a sixth and a third of that side."""
    tip_x, tip_y = w / 2 + w * dx / 100000, h / 2 + h * dy / 100000
    tip = (tip_x, tip_y)
    left = tip_x < w / 2
    top = tip_y < h / 2
    if tip_y > h or tip_y < 0:
        x1, x2 = (w / 6, w / 3) if left else (w * 2 / 3, w * 5 / 6)
        if top:
            points = [(0, 0), (x1, 0), tip, (x2, 0), (w, 0), (w, h), (0, h)]
        else:
            points = [(0, 0), (w, 0), (w, h), (x2, h), tip, (x1, h), (0, h)]
    else:
        y1, y2 = (h / 6, h / 3) if top else (h * 2 / 3, h * 5 / 6)
        if left:
            points = [(0, 0), (w, 0), (w, h), (0, h), (0, y2), tip, (0, y1)]
        else:
            points = [(0, 0), (w, 0), (w, y1), tip, (w, y2), (w, h), (0, h)]
    return Outline(_points(points))


def custom(geometry: Element, w: float, h: float) -> list[Outline]:
    result: list[Outline] = []
    for path in geometry.iterfind(f"{a('pathLst')}/{a('path')}"):
        path_w = integer(path, "w") or 0
        path_h = integer(path, "h") or 0
        sx = w / path_w if path_w else 1.0
        sy = h / path_h if path_h else 1.0
        data: list[str] = []
        x = y = 0.0
        closed = False
        for command in path:
            kind = local(command)
            points = [
                (integer(pt, "x") * sx, integer(pt, "y") * sy) for pt in command.iter(a("pt"))
            ]
            if kind == "moveTo" and points:
                x, y = points[0]
                data.append(f"M{number(x)} {number(y)}")
            elif kind == "lnTo" and points:
                x, y = points[0]
                data.append(f"L{number(x)} {number(y)}")
            elif kind == "cubicBezTo" and len(points) == 3:
                data.append("C" + " ".join(f"{number(px)} {number(py)}" for px, py in points))
                x, y = points[2]
            elif kind == "quadBezTo" and len(points) == 2:
                data.append("Q" + " ".join(f"{number(px)} {number(py)}" for px, py in points))
                x, y = points[1]
            elif kind == "arcTo":
                x, y, text = _arc(command, x, y, sx, sy)
                data.append(text)
            elif kind == "close":
                data.append("Z")
                closed = True
        if data:
            result.append(
                Outline(
                    " ".join(data),
                    filled=path.get("fill", "norm") != "none",
                    stroked=path.get("stroke", "1") not in ("0", "false"),
                    closed=closed,
                )
            )
    return result


def _arc(command: Element, x: float, y: float, sx: float, sy: float) -> tuple[float, float, str]:
    """``a:arcTo`` from (``x``, ``y``): the point of the ellipse at ``stAng`` is the current
    point; the arc runs ``swAng`` (clockwise for positive angles)."""
    rx, ry = integer(command, "wR") * sx, integer(command, "hR") * sy
    start = math.radians(integer(command, "stAng") / 60000)
    sweep = integer(command, "swAng") / 60000
    cx, cy = x - rx * math.cos(start), y - ry * math.sin(start)
    end = start + math.radians(sweep)
    x2, y2 = cx + rx * math.cos(end), cy + ry * math.sin(end)
    large = 1 if abs(sweep) > 180 else 0
    clockwise = 1 if sweep > 0 else 0
    text = (
        f"A{number(rx)} {number(ry)} 0 {large} {clockwise} {number(x2)} {number(y2)}"
        if rx and ry
        else f"L{number(x2)} {number(y2)}"
    )
    return x2, y2, text
