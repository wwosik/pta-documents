"""The PTA logos as SVG and PNG, converted from the EMF pictures of the templates.

``run.sh prepare-templates`` writes the files next to this module (package data) from
``source-templates/``; nothing is converted at run time:

==================== ================================================================ =========
Logo                 Source (found through the relationships)                         Colour
==================== ================================================================ =========
``logo-word``        Header picture of the Word portrait template (all four are       PTA blue
                     equal): word mark with corner brackets, without slogan
``logo-slides``      Logo of the slide layout ``Titelfolie mit Bild 01``, with the    white
                     slogan „Kundenorientierte IT-Lösungen seit 1969"
``logo-slides-plain`` Logo of the slide layout ``Abbschlussfolie``, without slogan      white
==================== ================================================================ =========

The SVGs contain only ``<path>`` elements with ``d`` (``M``/``L``/``C``/``Z``, absolute),
``fill`` and ``fill-rule``; ``shapes()`` reads that subset back and ``drawing()`` turns it into a
``Drawing`` (E02-S03), so other outputs (PDF) can draw the logo as vectors. The PNGs are
2000 px wide with a transparent background. The EMF colour of the Word logo (``026FB9``) is
written as PTA blue (decision 2026-11-07).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from enum import StrEnum
from importlib import resources
from typing import Final

from pta_documents.drawing import (
    ClosePath,
    CubicTo,
    Drawing,
    DrawingPath,
    DrawingShape,
    LineTo,
    MoveTo,
    PathSegment,
)

SVG_NS: Final = "http://www.w3.org/2000/svg"

PNG_WIDTH: Final = 2000
"""Width of the logo PNGs in pixels."""


class Logo(StrEnum):
    WORD = "word"
    """Blue word mark of the Word header, without slogan."""
    SLIDES = "slides"
    """White logo of the title slides, with slogan."""
    SLIDES_PLAIN = "slides-plain"
    """White logo of the closing slide, without slogan."""

    @property
    def stem(self) -> str:
        """The file name without suffix in the package (``logo-word`` …)."""
        return f"logo-{self.value}"


type Segment = tuple[str, tuple[float, ...]]
"""A path command ``M``, ``L``, ``C`` or ``Z`` with its absolute coordinates."""


@dataclass(frozen=True, slots=True)
class LogoShape:
    """One filled area of a logo, in the units of the SVG ``viewBox`` (origin top left)."""

    segments: tuple[Segment, ...]
    fill: str
    """``RRGGBB`` without ``#``, a value of ``design.colors``."""
    even_odd: bool


def read(name: str) -> bytes:
    """The bytes of a file in the logo folder."""
    return (resources.files(__name__) / name).read_bytes()


def svg(logo: Logo) -> bytes:
    return read(logo.stem + ".svg")


def png(logo: Logo) -> bytes:
    return read(logo.stem + ".png")


def size(logo: Logo) -> tuple[float, float]:
    """Width and height of the ``viewBox``."""
    return _view_box(_root(logo))


def aspect_ratio(logo: Logo) -> float:
    """Width divided by height."""
    width, height = size(logo)
    return width / height


def shapes(logo: Logo) -> tuple[LogoShape, ...]:
    """The filled paths of the SVG, in document order."""
    result: list[LogoShape] = []
    for element in _root(logo):
        if element.tag != f"{{{SVG_NS}}}path":
            raise ValueError(f"{logo.stem}.svg: unexpected element {element.tag}")
        fill = element.get("fill", "")
        if not re.fullmatch(r"#[0-9A-F]{6}", fill):
            raise ValueError(f"{logo.stem}.svg: unexpected fill {fill!r}")
        rule = element.get("fill-rule", "nonzero")
        if rule not in ("nonzero", "evenodd"):
            raise ValueError(f"{logo.stem}.svg: unexpected fill-rule {rule!r}")
        result.append(LogoShape(parse_path(element.get("d", "")), fill[1:], rule == "evenodd"))
    return tuple(result)


def drawing(logo: Logo, width: float | None = None) -> Drawing:
    """The logo as a ``Drawing``: one filled shape without stroke per path of the SVG.

    Without ``width`` the coordinates are the units of the ``viewBox``; with it the logo is
    scaled to that width in CSS pixels, the height in proportion.
    """
    view_width, view_height = size(logo)
    scale = 1.0 if width is None else width / view_width
    items = tuple(
        DrawingShape(
            DrawingPath(tuple(_segment(segment, scale) for segment in shape.segments)),
            shape.fill,
            None,
            0,
            even_odd=shape.even_odd,
        )
        for shape in shapes(logo)
    )
    return Drawing(view_width * scale, view_height * scale, items)


def _segment(segment: Segment, scale: float) -> PathSegment:
    command, numbers = segment
    x = tuple(n * scale for n in numbers)
    match command:
        case "M":
            return MoveTo(x[0], x[1])
        case "L":
            return LineTo(x[0], x[1])
        case "C":
            return CubicTo(x[0], x[1], x[2], x[3], x[4], x[5])
        case _:
            return ClosePath()


_ARITY: Final = {"M": 2, "L": 2, "C": 6, "Z": 0}
_TOKEN: Final = re.compile(r"([MLCZ])|(-?\d+(?:\.\d+)?)|(\s+)|(.)")


def parse_path(data: str) -> tuple[Segment, ...]:
    """Parses path data of the subset the logos use: absolute ``M``/``L``/``C``/``Z``."""
    segments: list[Segment] = []
    command: str | None = None
    numbers: list[float] = []

    def flush() -> None:
        if command is None:
            return
        arity = _ARITY[command]
        if len(numbers) != arity:
            raise ValueError(f"path command {command} needs {arity} numbers, got {numbers}")
        segments.append((command, tuple(numbers)))

    for match in _TOKEN.finditer(data):
        letter, number, _, other = match.groups()
        if other is not None:
            raise ValueError(f"unexpected character {other!r} in path data")
        if letter is not None:
            flush()
            command, numbers = letter, []
        elif number is not None:
            if command is None:
                raise ValueError("path data starts with a number")
            numbers.append(float(number))
    flush()
    return tuple(segments)


def _root(logo: Logo) -> ElementTree.Element:
    root = ElementTree.fromstring(svg(logo))
    if root.tag != f"{{{SVG_NS}}}svg":
        raise ValueError(f"{logo.stem}.svg is not an SVG")
    return root


def _view_box(root: ElementTree.Element) -> tuple[float, float]:
    x, y, width, height = (float(v) for v in root.get("viewBox", "").split())
    if x or y:
        raise ValueError("the logo viewBox must start at 0 0")
    return width, height
