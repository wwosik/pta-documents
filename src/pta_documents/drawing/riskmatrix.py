"""The risk matrix as a ``Drawing`` (E15-S02), the same for every format.

``draw`` lays out 5 × 5 cells, probability from left to right and impact from bottom to top,
each cell tinted in the signal colour of its product (``Thresholds.level``) and every risk a
dark blue circle with its number in white, several in a cell side by side. The axes carry their
numbers and the headings of the table with an arrow. Sizes are CSS pixels (a pixel is 0.75 pt);
colours come from ``design.colors`` — the signal colours only here (risks are a status).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

from pta_documents.design import colors
from pta_documents.drawing.model import (
    ClosePath,
    Drawing,
    DrawingHover,
    DrawingItem,
    DrawingPath,
    DrawingShape,
    DrawingText,
    LineTo,
    MoveTo,
    ShapeKind,
    TextAnchor,
)
from pta_documents.drawing.schedule import px
from pta_documents.drawing.svg_geometry import ellipse
from pta_documents.generation.common.risks import SCALE, RiskMatrix

CM: Final = 72 / 2.54
"""Points per centimetre."""


@dataclass(frozen=True)
class RiskMatrixStyle:
    """Sizes of a risk matrix in pixels (sizes of text in points)."""

    cell: float = px(1.6 * CM)
    """A cell: 1.6 cm square."""
    dot: float = px(0.6 * CM)
    """The circle of a risk: 0.6 cm."""
    number_pt: float = 10
    label_pt: float = 10
    tint: float = 0.35
    """The share of the signal colour in a cell (the rest is white)."""
    rule: float = 2
    """The white gap between two cells."""
    tick: float = 18
    """The band of the axis numbers, left of and below the cells."""
    band: float = 22
    """The band of an axis heading, above (impact) and below (probability) the cells."""
    arrow: float = 14
    """The length of an axis arrow."""
    arrow_line: float = 1.5
    spread: float = 3
    """The least room between two circles in a cell, as long as they fit."""


RISK_MATRIX: Final = RiskMatrixStyle()


def draw(
    matrix: RiskMatrix, *, dark: bool = False, style: RiskMatrixStyle = RISK_MATRIX
) -> Drawing:
    """The matrix in its natural size (cells of ``style.cell``); ``dark``: on a dark slide."""
    label_color = colors.WHITE if dark else colors.GREY_DARK
    left = style.tick
    top = style.band
    side = SCALE * style.cell
    items: list[DrawingItem] = []
    label = px(style.label_pt)
    for probability in range(1, SCALE + 1):
        for impact in range(1, SCALE + 1):
            x, y = _cell(probability, impact, left, top, style)
            level = matrix.thresholds.level(probability, impact)
            fill = colors.tint(colors.STATUS_COLORS[level], style.tint)
            inset = style.rule / 2
            items.append(
                DrawingShape(
                    DrawingPath.rectangle(
                        x + inset, y + inset, style.cell - style.rule, style.cell - style.rule
                    ),
                    fill,
                    None,
                    0,
                    kind=ShapeKind.RECTANGLE,
                )
            )
    for n in range(1, SCALE + 1):
        x, _ = _cell(n, 1, left, top, style)
        items.append(
            DrawingText.line(
                x + style.cell / 2,
                top + side + style.tick * 0.75,
                str(n),
                label,
                label_color,
                anchor=TextAnchor.MIDDLE,
            )
        )
        _, y = _cell(1, n, left, top, style)
        items.append(
            DrawingText.line(
                left / 2,
                y + style.cell / 2 + label * 0.35,
                str(n),
                label,
                label_color,
                anchor=TextAnchor.MIDDLE,
            )
        )
    # The impact upwards above the cells, the probability to the right below them.
    items.extend(
        _arrow(left / 2, style.band - 3, left / 2, style.band - 3 - style.arrow, label_color, style)
    )
    items.append(
        DrawingText.line(
            left + 2, style.band - 7, matrix.impact_heading, label, label_color, bold=True
        )
    )
    bottom = top + side + style.tick + style.band - 7
    end = left + side
    arrow_y = bottom - label * 0.3
    items.extend(_arrow(end - style.arrow, arrow_y, end, arrow_y, label_color, style))
    items.append(
        DrawingText.line(
            end - style.arrow - 4,
            bottom,
            matrix.probability_heading,
            label,
            label_color,
            bold=True,
            anchor=TextAnchor.END,
        )
    )
    items.extend(_dots(matrix, left, top, style))
    return Drawing(left + side, top + side + style.tick + style.band, tuple(items))


def _cell(
    probability: int, impact: int, left: float, top: float, style: RiskMatrixStyle
) -> tuple[float, float]:
    """The top left corner of a cell: probability to the right, impact upwards."""
    return left + (probability - 1) * style.cell, top + (SCALE - impact) * style.cell


def offsets(count: int, style: RiskMatrixStyle = RISK_MATRIX) -> list[tuple[float, float]]:
    """Where ``count`` circles sit in a cell, from its centre: on a grid of as many columns as
    rows, centred; closer together (overlapping) when they would not fit."""
    if count <= 1:
        return [(0.0, 0.0)] * count
    columns = math.ceil(math.sqrt(count))
    rows = math.ceil(count / columns)
    room = style.cell - style.rule - style.dot - 2 * style.spread
    pitch = min(style.dot + style.spread, room / (max(columns, rows) - 1))
    result: list[tuple[float, float]] = []
    for n in range(count):
        row, column = divmod(n, columns)
        in_row = min(columns, count - row * columns)
        result.append(((column - (in_row - 1) / 2) * pitch, (row - (rows - 1) / 2) * pitch))
    return result


def _dots(matrix: RiskMatrix, left: float, top: float, style: RiskMatrixStyle) -> list[DrawingItem]:
    items: list[DrawingItem] = []
    radius = style.dot / 2
    size = px(style.number_pt)
    for probability in range(1, SCALE + 1):
        for impact in range(1, SCALE + 1):
            here = matrix.in_cell(probability, impact)
            x, y = _cell(probability, impact, left, top, style)
            cx, cy = x + style.cell / 2, y + style.cell / 2
            for risk, (dx, dy) in zip(here, offsets(len(here), style), strict=True):
                hover = DrawingHover(f"{risk.number} {risk.name}", cx + dx, cy + dy - radius)
                items.append(
                    DrawingShape(
                        DrawingPath(tuple(ellipse(cx + dx, cy + dy, radius, radius))),
                        colors.DARK_BLUE,
                        colors.WHITE,
                        1,
                        kind=ShapeKind.ELLIPSE,
                        hover=hover,
                    )
                )
                items.append(
                    DrawingText.line(
                        cx + dx,
                        cy + dy + size * 0.35,
                        risk.number,
                        size,
                        colors.WHITE,
                        bold=True,
                        anchor=TextAnchor.MIDDLE,
                    )
                )
    return items


def _arrow(
    x1: float, y1: float, x2: float, y2: float, color: str, style: RiskMatrixStyle
) -> list[DrawingItem]:
    """A line from (``x1``, ``y1``) with a small head at (``x2``, ``y2``)."""
    length = math.hypot(x2 - x1, y2 - y1) or 1
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    head = 5.0
    base_x, base_y = x2 - ux * head, y2 - uy * head
    line = DrawingShape(
        DrawingPath((MoveTo(x1, y1), LineTo(base_x, base_y))),
        None,
        color,
        style.arrow_line,
    )
    tip = DrawingShape(
        DrawingPath(
            (
                MoveTo(x2, y2),
                LineTo(base_x - uy * head * 0.6, base_y + ux * head * 0.6),
                LineTo(base_x + uy * head * 0.6, base_y - ux * head * 0.6),
                ClosePath(),
            )
        ),
        color,
        None,
        0,
    )
    return [line, tip]
