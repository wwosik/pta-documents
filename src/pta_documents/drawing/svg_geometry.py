"""SVG geometry as path segments of the drawing model: path data, basic shapes and transforms.

Port of DocLibs ``SvgGeometry.cs`` (E06-S03). Arcs and quadratic curves become cubic Bézier
curves, so a ``Drawing`` only ever holds lines and cubics. Malformed or unknown input raises
``SvgDrawingError`` instead of being dropped.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Final

from pta_documents.drawing.model import (
    ClosePath,
    CubicTo,
    DrawingPath,
    LineTo,
    MoveTo,
    PathSegment,
    Point,
)

KAPPA: Final = 0.5522847498307936
"""The control-point distance of a cubic quarter circle, as a fraction of the radius."""

_TOKEN: Final = re.compile(r"[A-Za-z]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_TRANSFORM_ARGUMENTS: Final = re.compile(
    r"^[\s,]*(?:[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?(?:deg|px)?[\s,]*)*$"
)
"""Numbers, in CSS (the ``transform`` property) also with ``deg`` or ``px``."""
_TRANSFORM_CALL: Final = re.compile(r"(matrix|translate|scale|rotate)\s*\(([^)]*)\)")


class SvgDrawingError(ValueError):
    """An SVG has something the drawing model cannot draw, or is malformed."""


@dataclass(frozen=True, slots=True)
class Affine:
    """An affine transform, ``matrix(a b c d e f)`` in SVG's terms."""

    a: float
    b: float
    c: float
    d: float
    e: float
    f: float

    @staticmethod
    def identity() -> Affine:
        return Affine(1, 0, 0, 1, 0, 0)

    @staticmethod
    def translate(x: float, y: float) -> Affine:
        return Affine(1, 0, 0, 1, x, y)

    @staticmethod
    def rotate(degrees: float) -> Affine:
        radians = math.radians(degrees)
        sin, cos = math.sin(radians), math.cos(radians)
        return Affine(cos, sin, -sin, cos, 0, 0)

    @staticmethod
    def scale_by(x: float, y: float) -> Affine:
        return Affine(x, 0, 0, y, 0, 0)

    @property
    def is_axis_aligned(self) -> bool:
        """Whether it only moves and scales, so axis-aligned shapes stay axis-aligned."""
        return self.b == 0 and self.c == 0

    @property
    def scale(self) -> float:
        """How much it scales lengths, such as line widths."""
        return math.sqrt(abs(self.a * self.d - self.b * self.c))

    def then(self, inner: Affine) -> Affine:
        """``inner`` first, then this."""
        return Affine(
            self.a * inner.a + self.c * inner.b,
            self.b * inner.a + self.d * inner.b,
            self.a * inner.c + self.c * inner.d,
            self.b * inner.c + self.d * inner.d,
            self.a * inner.e + self.c * inner.f + self.e,
            self.b * inner.e + self.d * inner.f + self.f,
        )

    def apply(self, x: float, y: float) -> Point:
        return (self.a * x + self.c * y + self.e, self.b * x + self.d * y + self.f)

    def apply_segment(self, segment: PathSegment) -> PathSegment:
        match segment:
            case MoveTo(x, y):
                return MoveTo(*self.apply(x, y))
            case LineTo(x, y):
                return LineTo(*self.apply(x, y))
            case CubicTo(x1, y1, x2, y2, x, y):
                return CubicTo(*self.apply(x1, y1), *self.apply(x2, y2), *self.apply(x, y))
            case ClosePath():
                return segment


def _numbers(text: str) -> list[float]:
    return [float(token) for token in _TOKEN.findall(text) if not token[0].isalpha()]


def path(data: str) -> list[PathSegment]:
    """Parses path data: every command of SVG 1.1, relative ones too."""
    tokens = _TOKEN.findall(data)
    result: list[PathSegment] = []
    index = 0
    command = ""
    x = y = start_x = start_y = 0.0
    last_cubic: Point | None = None
    last_quad: Point | None = None

    def number() -> float:
        nonlocal index
        if index >= len(tokens) or tokens[index][0].isalpha():
            raise SvgDrawingError(
                f"The diagram's SVG has the path data '{data}', which is malformed."
            )
        index += 1
        return float(tokens[index - 1])

    while index < len(tokens):
        if tokens[index][0].isalpha():
            command = tokens[index]
            index += 1
        elif not command:
            raise SvgDrawingError(
                f"The diagram's SVG has the path data '{data}', which does not start with a "
                "command."
            )
        relative = command.islower()
        dx, dy = (x, y) if relative else (0.0, 0.0)
        is_cubic = is_quad = False
        match command.upper():
            case "M":
                x, y = number() + dx, number() + dy
                start_x, start_y = x, y
                result.append(MoveTo(x, y))
                command = "l" if relative else "L"  # further pairs are lines
            case "L":
                x, y = number() + dx, number() + dy
                result.append(LineTo(x, y))
            case "H":
                x = number() + dx
                result.append(LineTo(x, y))
            case "V":
                y = number() + dy
                result.append(LineTo(x, y))
            case "C":
                x1, y1, x2, y2 = number() + dx, number() + dy, number() + dx, number() + dy
                x, y = number() + dx, number() + dy
                result.append(CubicTo(x1, y1, x2, y2, x, y))
                last_cubic, is_cubic = (x2, y2), True
            case "S":
                x1, y1 = (2 * x - last_cubic[0], 2 * y - last_cubic[1]) if last_cubic else (x, y)
                x2, y2 = number() + dx, number() + dy
                x, y = number() + dx, number() + dy
                result.append(CubicTo(x1, y1, x2, y2, x, y))
                last_cubic, is_cubic = (x2, y2), True
            case "Q":
                qx, qy = number() + dx, number() + dy
                ex, ey = number() + dx, number() + dy
                result.append(_quadratic(x, y, qx, qy, ex, ey))
                x, y = ex, ey
                last_quad, is_quad = (qx, qy), True
            case "T":
                qx, qy = (2 * x - last_quad[0], 2 * y - last_quad[1]) if last_quad else (x, y)
                ex, ey = number() + dx, number() + dy
                result.append(_quadratic(x, y, qx, qy, ex, ey))
                x, y = ex, ey
                last_quad, is_quad = (qx, qy), True
            case "A":
                rx, ry, rotation = number(), number(), number()
                large, sweep = number() != 0, number() != 0
                ex, ey = number() + dx, number() + dy
                result.extend(_arc(x, y, rx, ry, rotation, large, sweep, ex, ey))
                x, y = ex, ey
            case "Z":
                result.append(ClosePath())
                x, y = start_x, start_y
            case _:
                raise SvgDrawingError(
                    f"The diagram's SVG has the path command '{command}', which cannot be drawn."
                )
        if not is_cubic:
            last_cubic = None
        if not is_quad:
            last_quad = None
    return result


def points(text: str, *, close: bool) -> list[PathSegment]:
    """The points of a ``polygon`` or ``polyline``."""
    numbers = _numbers(text)
    result: list[PathSegment] = [
        MoveTo(numbers[i], numbers[i + 1]) if i == 0 else LineTo(numbers[i], numbers[i + 1])
        for i in range(0, len(numbers) - 1, 2)
    ]
    if close and result:
        result.append(ClosePath())
    return result


def rectangle(
    x: float, y: float, width: float, height: float, rx: float, ry: float
) -> list[PathSegment]:
    """A rectangle, with elliptical corners when ``rx`` and ``ry`` are positive."""
    rx = min(rx, width / 2)
    ry = min(ry, height / 2)
    if rx <= 0 or ry <= 0:
        return list(DrawingPath.rectangle(x, y, width, height).segments)
    kx, ky = rx * KAPPA, ry * KAPPA
    right, bottom = x + width, y + height
    return [
        MoveTo(x + rx, y),
        LineTo(right - rx, y),
        CubicTo(right - rx + kx, y, right, y + ry - ky, right, y + ry),
        LineTo(right, bottom - ry),
        CubicTo(right, bottom - ry + ky, right - rx + kx, bottom, right - rx, bottom),
        LineTo(x + rx, bottom),
        CubicTo(x + rx - kx, bottom, x, bottom - ry + ky, x, bottom - ry),
        LineTo(x, y + ry),
        CubicTo(x, y + ry - ky, x + rx - kx, y, x + rx, y),
        ClosePath(),
    ]


def ellipse(cx: float, cy: float, rx: float, ry: float) -> list[PathSegment]:
    """An ellipse as four cubic quarter arcs, clockwise from the top."""
    kx, ky = rx * KAPPA, ry * KAPPA
    return [
        MoveTo(cx, cy - ry),
        CubicTo(cx + kx, cy - ry, cx + rx, cy - ky, cx + rx, cy),
        CubicTo(cx + rx, cy + ky, cx + kx, cy + ry, cx, cy + ry),
        CubicTo(cx - kx, cy + ry, cx - rx, cy + ky, cx - rx, cy),
        CubicTo(cx - rx, cy - ky, cx - kx, cy - ry, cx, cy - ry),
        ClosePath(),
    ]


def transform(value: str | None) -> Affine:
    """Parses a ``transform`` attribute or CSS property: ``matrix``, ``translate``, ``scale``,
    ``rotate``."""
    result = Affine.identity()
    if value is None or not value.strip():
        return result
    if _TRANSFORM_CALL.sub("", value).strip(" ,\t\r\n"):
        raise SvgDrawingError(
            f"The diagram's SVG has the transform '{value}', which cannot be drawn."
        )
    for match in _TRANSFORM_CALL.finditer(value):
        if not _TRANSFORM_ARGUMENTS.match(match.group(2)):
            raise SvgDrawingError(
                f"The diagram's SVG has the transform '{value}', which cannot be drawn."
            )
        n = _numbers(match.group(2))
        match (match.group(1), len(n)):
            case ("matrix", 6):
                step = Affine(*n)
            case ("translate", 1):
                step = Affine.translate(n[0], 0)
            case ("translate", 2):
                step = Affine.translate(n[0], n[1])
            case ("scale", 1):
                step = Affine.scale_by(n[0], n[0])
            case ("scale", 2):
                step = Affine.scale_by(n[0], n[1])
            case ("rotate", 1):
                step = Affine.rotate(n[0])
            case ("rotate", 3):
                step = (
                    Affine.translate(n[1], n[2])
                    .then(Affine.rotate(n[0]))
                    .then(Affine.translate(-n[1], -n[2]))
                )
            case _:
                raise SvgDrawingError(
                    f"The diagram's SVG has the transform '{value}', which cannot be drawn."
                )
        result = result.then(step)
    return result


def _quadratic(x0: float, y0: float, qx: float, qy: float, x: float, y: float) -> CubicTo:
    return CubicTo(
        x0 + 2 / 3 * (qx - x0),
        y0 + 2 / 3 * (qy - y0),
        x + 2 / 3 * (qx - x),
        y + 2 / 3 * (qy - y),
        x,
        y,
    )


def _arc(
    x1: float,
    y1: float,
    rx: float,
    ry: float,
    rotation: float,
    large: bool,
    sweep: bool,
    x2: float,
    y2: float,
) -> Sequence[PathSegment]:
    """SVG 1.1, appendix F.6.5 and F.6.6: endpoint to centre parameterization, then cubic
    pieces of at most 90°."""
    if (x1 == x2 and y1 == y2) or rx == 0 or ry == 0:
        return [] if x1 == x2 and y1 == y2 else [LineTo(x2, y2)]
    rx, ry = abs(rx), abs(ry)
    sin, cos = math.sin(math.radians(rotation)), math.cos(math.radians(rotation))
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p = cos * dx + sin * dy
    y1p = -sin * dx + cos * dy
    scale = x1p * x1p / (rx * rx) + y1p * y1p / (ry * ry)
    if scale > 1:
        rx *= math.sqrt(scale)
        ry *= math.sqrt(scale)
    numerator = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    denominator = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    factor = math.sqrt(max(0.0, numerator / denominator)) * (-1 if large == sweep else 1)
    cxp = factor * rx * y1p / ry
    cyp = -factor * ry * x1p / rx
    cx = cos * cxp - sin * cyp + (x1 + x2) / 2
    cy = sin * cxp + cos * cyp + (y1 + y2) / 2

    def angle(ux: float, uy: float, vx: float, vy: float) -> float:
        return math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)

    start = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    delta = angle((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and delta > 0:
        delta -= 2 * math.pi
    elif sweep and delta < 0:
        delta += 2 * math.pi
    pieces = math.ceil(abs(delta) / (math.pi / 2) - 1e-9)
    step = delta / pieces
    k = 4 / 3 * math.tan(step / 4)

    def point(t: float) -> Point:
        return (
            cx + rx * math.cos(t) * cos - ry * math.sin(t) * sin,
            cy + rx * math.cos(t) * sin + ry * math.sin(t) * cos,
        )

    def derivative(t: float) -> Point:
        return (
            -rx * math.sin(t) * cos - ry * math.cos(t) * sin,
            -rx * math.sin(t) * sin + ry * math.cos(t) * cos,
        )

    def curves() -> Iterator[PathSegment]:
        for i in range(pieces):
            t1, t2 = start + i * step, start + (i + 1) * step
            p1, d1, p2, d2 = point(t1), derivative(t1), point(t2), derivative(t2)
            end = (x2, y2) if i == pieces - 1 else p2
            yield CubicTo(
                p1[0] + k * d1[0],
                p1[1] + k * d1[1],
                p2[0] - k * d2[0],
                p2[1] - k * d2[1],
                end[0],
                end[1],
            )

    return list(curves())
