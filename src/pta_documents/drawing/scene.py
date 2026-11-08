"""A scene (E09-S04) as a still ``Drawing``: the PDF's picture of a scene slide.

Port of vt-tools-libs ``SceneDrawing``: the grid at ``PIXELS_PER_UNIT`` pixels a unit (1600 ×
670), every step shown — the slide's ground with a thin frame, then the shapes in order. Rotation
is baked into the outlines; text is drawn unrotated on one line, shrunk to its box down to 70 %.
Opacity is mixed onto the ground (the PDF is PDF/A, without transparency), so a half-transparent
shape covers what lies below it; an invisible one (``opacity=0``) is left out. Images are no part of
a drawing: they come back with the index of the item they go before.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from pta_documents.design import colors
from pta_documents.drawing.model import (
    ClosePath,
    Drawing,
    DrawingItem,
    DrawingPath,
    DrawingShape,
    DrawingText,
    LineTo,
    MoveTo,
    PathSegment,
    TextAnchor,
)
from pta_documents.drawing.model import ShapeKind as DrawingShapeKind
from pta_documents.drawing.svg_geometry import Affine, ellipse, rectangle
from pta_documents.generation.common import scene_colors
from pta_documents.generation.common.scene import (
    COLUMNS,
    ROWS,
    UNIT_EMU,
    Scene,
    SceneShape,
    ShapeKind,
)

PIXELS_PER_UNIT: Final = 10.0
EMU_PER_POINT: Final = 12700
PIXELS_PER_POINT: Final = PIXELS_PER_UNIT * EMU_PER_POINT / UNIT_EMU
"""A point of the slide in pixels of the drawing: text sizes are points on the slide."""
BOX_LINE: Final = 2.0
"""The outline of boxes, in pixels."""
LINE_WIDTH: Final = 3.0
"""The width of lines and arrows, in pixels."""
CORNER_RADIUS: Final = 12.0
"""The corner radius of a ``round`` box, in pixels."""
TEXT_PADDING: Final = 8.0
"""The room between a box's edge and its text, in pixels."""
TEXT_BASELINE: Final = 0.35
"""The baseline below the middle of a box, in text sizes."""
FRAME_COLOR: Final = colors.GREY_MID
DARK_GROUND: Final = colors.DARK_BLUE
"""The ground of a ``.dark`` scene slide, as the dark PTA slides."""


@dataclass(frozen=True)
class PlacedImage:
    """An image of the scene, to be drawn before the item ``index`` of the drawing, in its box
    (pixels), turned ``rotation`` degrees clockwise about the centre."""

    index: int
    shape: SceneShape
    x: float
    y: float
    width: float
    height: float
    rotation: float


def draw(scene: Scene, dark: bool = False) -> tuple[Drawing, tuple[PlacedImage, ...]]:
    """The scene as a drawing of the whole grid, and its images."""
    ground = DARK_GROUND if dark else colors.WHITE
    width, height = COLUMNS * PIXELS_PER_UNIT, ROWS * PIXELS_PER_UNIT
    items: list[DrawingItem] = [
        DrawingShape(
            DrawingPath.rectangle(0, 0, width, height),
            ground,
            FRAME_COLOR,
            1,
            kind=DrawingShapeKind.RECTANGLE,
        )
    ]
    images: list[PlacedImage] = []
    for shape in scene.shapes:
        if shape.opacity == 0:
            continue  # invisible: mixed onto the ground it would cover what lies below
        x, y, w, h = (value * PIXELS_PER_UNIT for value in shape.box)
        if shape.kind is ShapeKind.IMAGE:
            images.append(PlacedImage(len(items), shape, x, y, w, h, shape.rotation))
            continue
        turn = _turn(x + w / 2, y + h / 2, shape.rotation)

        def color(role: str, shape: SceneShape = shape) -> str | None:
            value = scene_colors.hex_of(role)
            return colors.mix(value, shape.opacity, ground) if value is not None else None

        if shape.is_line:
            stroke = color(scene_colors.stroke(shape))
            if stroke is not None:
                items.extend(_rotated(item, turn) for item in line(shape, stroke))
            continue
        soft = scene_colors.is_soft(shape)
        fill_role = scene_colors.fill(shape)
        fill_hex = scene_colors.hex_of(fill_role)
        if soft and fill_hex is not None:
            fill = colors.mix(scene_colors.soft_fill(fill_hex), shape.opacity, ground)
        else:
            fill = color(fill_role)
        stroke = color(scene_colors.stroke(shape))
        if fill is not None or stroke is not None:
            items.append(
                DrawingShape(
                    DrawingPath(tuple(turn.apply_segment(s) for s in _outline(shape, x, y, w, h))),
                    fill,
                    stroke,
                    BOX_LINE if stroke is not None else 0,
                )
            )
        text_color = color(scene_colors.text(shape, soft, dark))
        if shape.text and text_color is not None:
            size = shape.size * PIXELS_PER_POINT
            is_text = shape.kind is ShapeKind.TEXT
            items.append(
                DrawingText.line(
                    x if is_text else x + w / 2,
                    y + h / 2 + size * TEXT_BASELINE,
                    shape.text,
                    size,
                    text_color,
                    bold=shape.bold,
                    anchor=TextAnchor.START if is_text else TextAnchor.MIDDLE,
                    max_width=max(w - (0 if is_text else 2 * TEXT_PADDING), 1),
                )
            )
    return Drawing(width, height, tuple(items)), tuple(images)


def line(shape: SceneShape, color: str) -> list[DrawingShape]:
    """A line or arrow, unrotated, in pixels: the line, and for an arrow a filled head at its
    end."""
    start = (shape.x * PIXELS_PER_UNIT, shape.y * PIXELS_PER_UNIT)
    end = ((shape.x + shape.width) * PIXELS_PER_UNIT, (shape.y + shape.height) * PIXELS_PER_UNIT)
    arrow = shape.kind is ShapeKind.ARROW
    length = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
    head = min(LINE_WIDTH * 4, length / 2) if arrow else 0
    ux, uy = ((end[0] - start[0]) / length, (end[1] - start[1]) / length) if length else (1, 0)
    stem = (end[0] - ux * head, end[1] - uy * head)
    result = [DrawingShape(DrawingPath((MoveTo(*start), LineTo(*stem))), None, color, LINE_WIDTH)]
    if arrow and length > 0:
        px, py = -uy * head * 0.6, ux * head * 0.6
        result.append(
            DrawingShape(
                DrawingPath(
                    (
                        MoveTo(*end),
                        LineTo(stem[0] + px, stem[1] + py),
                        LineTo(stem[0] - px, stem[1] - py),
                        ClosePath(),
                    )
                ),
                color,
                None,
                0,
            )
        )
    return result


def _outline(shape: SceneShape, x: float, y: float, w: float, h: float) -> list[PathSegment]:
    match shape.kind:
        case ShapeKind.ROUND:
            radius = min(CORNER_RADIUS, min(w, h) / 2)
            return list(rectangle(x, y, w, h, radius, radius))
        case ShapeKind.PILL:
            radius = min(w, h) / 2
            return list(rectangle(x, y, w, h, radius, radius))
        case ShapeKind.CIRCLE:
            return list(ellipse(x + w / 2, y + h / 2, w / 2, h / 2))
        case _:
            return list(DrawingPath.rectangle(x, y, w, h).segments)


def _turn(cx: float, cy: float, degrees: float) -> Affine:
    """Clockwise by ``degrees`` about the centre, as on screen, where y runs down."""
    if degrees == 0:
        return Affine.identity()
    return Affine.translate(cx, cy).then(Affine.rotate(degrees).then(Affine.translate(-cx, -cy)))


def _rotated(item: DrawingShape, turn: Affine) -> DrawingShape:
    path = DrawingPath(tuple(turn.apply_segment(s) for s in item.path.segments))
    return DrawingShape(path, item.fill, item.stroke, item.stroke_width)
