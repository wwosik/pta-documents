"""Scenes (E09-S04): named shapes at fixed places of a slide, which Morph moves.

Port of vt-tools-libs ``Scene.Parse`` and ``ShapeReader``. A ``::: scene`` holds one shape per
line, ``name: kind x,y wxh "text" key=value …``, optionally as a list item (``- ``), so that the
Markdown reads as a list elsewhere; blank lines and ``<!-- comments -->`` are skipped. The lines
are read as written (``markdown.parser.SOURCE_LINES``), not as Markdown.

PTA: the grid is ``COLUMNS`` × ``ROWS`` square units over the content area of ``Nur Titel``
(``design.slides.CONTENT_AREA``, 31.20 cm wide: a unit is 0.195 cm), from its top left corner;
a shape outside it is a mistake. A scene slide is a ``##`` section with one ``::: scene`` and
nothing else but ``::: notes`` (``check_place``). ``layout_syntax.check`` reads every scene, so
every generator rejects the same mistakes with ``Line N: …``; the generators read it again with
the document's images (``find_image``).
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Sequence
from dataclasses import KW_ONLY, dataclass, replace
from enum import StrEnum
from typing import Final

from markdown_it.token import Token

from pta_documents.design import slides as design
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import heading_attributes, scene_colors
from pta_documents.generation.common.schedule import error_at
from pta_documents.markdown import block_markers
from pta_documents.markdown.document import DocumentResource
from pta_documents.markdown.parser import CONTAINER_OPEN, SOURCE_LINES, container, line_of

SCENE: Final = "scene"
"""The container's name."""
COLUMNS: Final = 160
"""The grid across the content area (decision 2026-11-07: square units, 160 × 67)."""
ROWS: Final = 67
UNIT_EMU: Final = design.CONTENT_AREA.width // COLUMNS
"""A grid unit on the slide: 31.20 cm / 160 = 0.195 cm."""
DEFAULT_TEXT_PT: Final = 16.0
"""The text size without ``size=``, in points."""
MAX_TEXT_PT: Final = 400.0
ATTRIBUTES: Final = "fill, line, text, rotate, opacity, size, bold, solid, step, image"
"""The attributes, as they are written, for error messages."""
PLACE: Final = "A '::: scene' stands directly under a '##' heading, one per slide."
SLIDE: Final = (
    "A slide with a '::: scene' holds only its title, the scene and '::: notes'; put the rest "
    "on a slide of its own."
)

_CLOSING: Final = re.compile(r"^\s*:{3,}\s*$")
_COMMENT: Final = re.compile(r"^<!--.*-->$")
_SHAPE: Final = re.compile(r"^(?:[-*+]\s+)?(?P<name>[A-Za-z][\w-]*):\s+(?P<rest>.*)$")
_TOKEN: Final = re.compile(
    r'"(?P<text>[^"]*)"'
    r'|(?P<key>[A-Za-z][\w-]*)=(?:"(?P<quoted>[^"]*)"|(?P<value>\S+))'
    r"|(?P<word>\S+)"
)
_PAIR: Final = re.compile(r"^(?P<a>-?\d+(?:\.\d+)?)(?P<sep>[,x])(?P<b>-?\d+(?:\.\d+)?)$")
_STEP: Final = re.compile(r"^\d+$")
_NUMBER: Final = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")


class ShapeKind(StrEnum):
    """What a scene shape is, as it is written."""

    BOX = "box"
    ROUND = "round"
    """A box with rounded corners."""
    PILL = "pill"
    CIRCLE = "circle"
    TEXT = "text"
    """Text without a box, left-aligned."""
    LINE = "line"
    """From ``x,y`` to ``x+w,y+h``."""
    ARROW = "arrow"
    """A line with a head at its end."""
    IMAGE = "image"
    """``image=<path>`` fitted into the box; the text is its alternative text."""


KINDS: Final = ", ".join(kind.value for kind in ShapeKind)
"""The kinds, as they are written, for error messages."""
BOXES: Final = (ShapeKind.BOX, ShapeKind.ROUND, ShapeKind.PILL, ShapeKind.CIRCLE)
LINES: Final = (ShapeKind.LINE, ShapeKind.ARROW)


@dataclass(frozen=True)
class SceneShape:
    """A named shape in grid units. A line or arrow runs from (``x``, ``y``) to (``x`` +
    ``width``, ``y`` + ``height``), every other kind fills that box. Colours are as written (a
    role, ``#RRGGBB`` or ``none``, see ``scene_colors``); None takes the kind's default."""

    name: str
    kind: ShapeKind
    x: float
    y: float
    width: float
    height: float
    text: str = ""
    _: KW_ONLY
    line: int | None = None
    """The line of the Markdown it is written on, for messages."""
    fill: str | None = None
    stroke: str | None = None
    text_color: str | None = None
    rotation: float = 0.0
    """Clockwise, in degrees, about the centre."""
    opacity: float = 1.0
    """From 0 (invisible) to 1."""
    size: float = DEFAULT_TEXT_PT
    """The text size in points."""
    bold: bool = False
    solid: bool = False
    """A box filled in a colour stays solid instead of soft (``scene_colors.is_soft``)."""
    step: int = 0
    """The click it appears on; 0: with the slide."""
    image: str | None = None
    """The path of ``image=`` as written."""
    resource: DocumentResource | None = None
    """The picture of an image, when it was read with the document's images."""

    @property
    def is_line(self) -> bool:
        return self.kind in LINES

    @property
    def is_box(self) -> bool:
        return self.kind in BOXES

    @property
    def box(self) -> tuple[float, float, float, float]:
        """The box the shape takes, with a positive width and height; for lines, the box its
        two ends span."""
        return (
            min(self.x, self.x + self.width),
            min(self.y, self.y + self.height),
            abs(self.width),
            abs(self.height),
        )


@dataclass(frozen=True)
class Scene:
    shapes: tuple[SceneShape, ...]
    line: int | None = None
    """The line of ``::: scene``."""

    @property
    def steps(self) -> int:
        """The clicks the scene takes: its highest step."""
        return max((shape.step for shape in self.shapes), default=0)

    @property
    def texts(self) -> tuple[str, ...]:
        """The texts of its shapes but images, in order: what the scene says."""
        return tuple(s.text for s in self.shapes if s.text and s.kind is not ShapeKind.IMAGE)


type FindImage = Callable[[str], DocumentResource | None]


def read_scene(
    tokens: Sequence[Token],
    i: int,
    format: DocumentFormat,
    line_offset: int,
    find_image: FindImage | None = None,
) -> Scene:
    """The scene of the ``::: scene`` at ``tokens[i]``; ``find_image`` finds the pictures of
    images (None: they are not looked up, as in ``layout_syntax.check``)."""
    token = tokens[i]
    start = line_of(token, line_offset)
    lines = list(token.meta.get(SOURCE_LINES, ()))
    while lines and not lines[-1].strip():
        lines.pop()
    if lines and _CLOSING.match(lines[-1]):
        lines.pop()
    shapes: list[SceneShape] = []
    for n, raw in enumerate(lines, start=1):
        text = raw.strip()
        if not text or _COMMENT.match(text):
            continue
        line = start + n if start is not None else None
        shape = _ShapeReader(text, line, format, find_image).read()
        if any(other.name == shape.name for other in shapes):
            raise _error(format, line, text, f"the name '{shape.name}' is taken by another shape.")
        shapes.append(shape)
    if not shapes:
        raise error_at(format, start, "The '::: scene' holds no shapes.")
    return Scene(tuple(shapes), start)


def check_place(tokens: Sequence[Token], i: int, format: DocumentFormat, line_offset: int) -> None:
    """Raise unless the ``::: scene`` at ``tokens[i]`` stands directly under a ``##`` heading
    (no PTA slide kind, no layout but ``Nur Titel``) whose section holds nothing else but
    ``::: notes`` and HTML comments; a block marker on the scene is a mistake too."""
    token = tokens[i]
    line = line_of(token, line_offset)
    heading = _heading_before(tokens, i) if token.level == 0 else None
    if heading is None or tokens[heading].tag != "h2":
        raise error_at(format, line, PLACE)
    _, attributes = heading_attributes.split(tokens[heading + 1].content, format)
    if attributes is not None and (
        attributes.kind is not None
        or (attributes.layout is not None and attributes.layout != design.LAYOUTS.title_only)
    ):
        raise error_at(
            format,
            line_of(tokens[heading], line_offset),
            f"A scene slide goes on the layout '{design.LAYOUTS.title_only}'; its heading takes "
            '.dark, kicker="…" and uebergang="…", no PTA slide kind and no other layout.',
        )
    marker = token.meta.get(block_markers.MARKER)
    if isinstance(marker, block_markers.Marker):
        raise error_at(
            format,
            marker.line + 1 + line_offset,
            f"A scene is not built with '{marker.text}': give its shapes step=1, step=2 … to "
            "make them appear click by click.",
        )
    scenes = 0
    for other in tokens[heading + 3 : _section_end(tokens, heading)]:
        if other.level != 0 or other.nesting == -1:
            continue
        name = container(other)[0] if other.type == CONTAINER_OPEN else None
        if name == SCENE:
            scenes += 1
            if scenes > 1:
                raise error_at(format, line_of(other, line_offset), PLACE)
        elif name == "notes" or (
            other.type == "html_block" and _COMMENT.match(other.content.strip())
        ):
            continue
        else:
            raise error_at(format, line_of(other, line_offset), SLIDE)


def is_dark(tokens: Sequence[Token], i: int, format: DocumentFormat) -> bool:
    """Whether the slide of the ``::: scene`` at ``tokens[i]`` is ``.dark``."""
    heading = _heading_before(tokens, i)
    if heading is None:
        return False
    _, attributes = heading_attributes.split(tokens[heading + 1].content, format)
    return attributes is not None and attributes.dark


def outside(shape: SceneShape) -> bool:
    """Whether the shape's box reaches beyond the grid."""
    x, y, w, h = shape.box
    return x < 0 or y < 0 or x + w > COLUMNS or y + h > ROWS


def _heading_before(tokens: Sequence[Token], i: int) -> int | None:
    for j in range(i - 1, -1, -1):
        t = tokens[j]
        if t.type == "heading_open" and t.tag in ("h1", "h2") and t.level == 0:
            return j
    return None


def _section_end(tokens: Sequence[Token], heading: int) -> int:
    for j in range(heading + 3, len(tokens)):
        t = tokens[j]
        if t.type == "heading_open" and t.tag in ("h1", "h2") and t.level == 0:
            return j
    return len(tokens)


def _error(
    format: DocumentFormat, line: int | None, text: str, reason: str
) -> DocumentConversionError:
    return error_at(format, line, f"Scene shape '{text}': {reason}")


class _ShapeReader:
    """Reads one shape line, raising with its line on the first mistake."""

    def __init__(
        self, text: str, line: int | None, format: DocumentFormat, find_image: FindImage | None
    ) -> None:
        self.text = text
        self.line = line
        self.format = format
        self.find_image = find_image

    def error(self, reason: str) -> DocumentConversionError:
        return _error(self.format, self.line, self.text, reason)

    def read(self) -> SceneShape:
        match = _SHAPE.match(self.text)
        if match is None:
            raise self.error("expected 'name: kind x,y wxh \"text\" key=value …'.")
        tokens = list(_TOKEN.finditer(match.group("rest")))
        if len(tokens) < 3 or tokens[0].group("word") is None:
            raise self.error("expected a kind, a position x,y and a size wxh after the name.")
        kind_name = tokens[0].group("word")
        try:
            kind = ShapeKind(kind_name)
        except ValueError:
            raise self.error(f"unknown kind '{kind_name}'. Valid kinds: {KINDS}.") from None
        x, y = self.pair(tokens[1], ",", "a position x,y")
        width, height = self.pair(tokens[2], "x", "a size wxh")
        is_line = kind in LINES
        if not is_line and (width <= 0 or height <= 0):
            raise self.error(f"a {kind_name} needs a width and height above 0.")
        shape = SceneShape(match.group("name"), kind, x, y, width, height, line=self.line)
        seen: set[str] = set()
        has_text = False
        for token in tokens[3:]:
            if token.group("text") is not None:
                if has_text or is_line:
                    raise self.error(
                        f"a {kind_name} takes no text."
                        if is_line
                        else "a shape takes one text in quotes."
                    )
                shape = replace(shape, text=token.group("text"))
                has_text = True
                continue
            shape = self.attribute(shape, token, kind_name, seen)
        if kind is ShapeKind.IMAGE and shape.image is None:
            raise self.error("an image needs 'image=<path>'.")
        if outside(shape):
            bx, by, bw, bh = shape.box
            raise self.error(
                f"it reaches outside the grid of {COLUMNS} × {ROWS} units (the content area of "
                f"the slide): x from {bx:g} to {bx + bw:g}, y from {by:g} to {by + bh:g}. Keep x "
                f"within 0 to {COLUMNS} and y within 0 to {ROWS}."
            )
        return shape

    def attribute(
        self, shape: SceneShape, token: re.Match[str], kind_name: str, seen: set[str]
    ) -> SceneShape:
        key = token.group("key") or token.group("word")
        valued = token.group("key") is not None
        value = token.group("quoted") if token.group("quoted") is not None else token.group("value")
        if key in seen:
            raise self.error(f"'{key}' is given twice.")
        seen.add(key)
        if (shape.is_line and key in ("fill", "text", "size", "bold")) or (
            key == "solid" and not shape.is_box
        ):
            raise self.error(f"a {kind_name} takes no '{key}'.")
        match key, valued:
            case "bold", False:
                return replace(shape, bold=True)
            case "solid", False:
                return replace(shape, solid=True)
            case "fill", True:
                return replace(shape, fill=self.color(value))
            case "line", True:
                return replace(shape, stroke=self.color(value))
            case "text", True:
                return replace(shape, text_color=self.color(value))
            case "rotate", True:
                return replace(shape, rotation=self.number(key, value, -math.inf))
            case "opacity", True:
                return replace(shape, opacity=self.number(key, value, 0, 1))
            case "size", True:
                return replace(shape, size=self.number(key, value, 1, MAX_TEXT_PT))
            case "step", True:
                if not _STEP.match(value):
                    raise self.error(f"'step={value}' is not a whole number from 0.")
                return replace(shape, step=int(value))
            case "image", True if shape.kind is ShapeKind.IMAGE:
                return replace(shape, image=value, resource=self.resource(value))
            case "image", True:
                raise self.error("only an image takes 'image='.")
            case _:
                raise self.error(
                    f"unknown attribute '{token.group(0)}'. Valid attributes: {ATTRIBUTES}."
                )

    def resource(self, path: str) -> DocumentResource | None:
        if self.find_image is None:
            return None
        found = self.find_image(path)
        if found is None:
            raise self.error(f"the image '{path}' is not among the document's resources.")
        return found

    def pair(self, token: re.Match[str], separator: str, what: str) -> tuple[float, float]:
        match = _PAIR.match(token.group(0)) if token.group("word") is not None else None
        if match is None or match.group("sep") != separator:
            raise self.error(f"'{token.group(0)}' is not {what}.")
        return float(match.group("a")), float(match.group("b"))

    def color(self, value: str) -> str:
        if not scene_colors.is_valid(value):
            raise self.error(
                f"'{value}' is no colour. Valid colours: {scene_colors.VALID}, #RRGGBB or none."
            )
        return value

    def number(self, key: str, value: str, low: float, high: float = math.inf) -> float:
        number = float(value) if _NUMBER.match(value) else None
        if number is None or not low <= number <= high:
            what = " from 0 to 1" if high <= 1 else " above 0" if low > 0 else ""
            raise self.error(f"'{key}={value}' is not a number{what}.")
        return number
