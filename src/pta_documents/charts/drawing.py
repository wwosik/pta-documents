"""A chart as a vector ``Drawing`` (port of DocLibs ``ChartDrawing.cs``).

For outputs that draw rather than write native charts (PDF, SVG): the title on top, the unit
above the value axis, the value axis on the left with gridlines at round steps, the categories
below, the legend at the bottom. Colours come from ``design.colors`` only: the series in the
colours of the spec (the PTA accents), text in the text colour of the format, gridlines light
grey, the zero line mid grey.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final, NamedTuple

from pta_documents.charts.spec import ChartKind, ChartSpec
from pta_documents.design import colors
from pta_documents.design.variants import Language
from pta_documents.drawing.model import (
    ClosePath,
    CubicTo,
    Drawing,
    DrawingItem,
    DrawingPath,
    DrawingShape,
    DrawingText,
    LineTo,
    MoveTo,
    PathSegment,
    ShapeKind,
    TextAnchor,
)

WIDTH: Final = 640.0
HEIGHT: Final = 380.0
"""The size of the drawing in CSS pixels; Word places native charts in the same proportions."""
LABEL_SIZE: Final = 11.0
TITLE_SIZE: Final = 15.0
GRID_WIDTH: Final = 0.5
AXIS_WIDTH: Final = 0.5 / 0.75
"""The zero line: 0.5 pt (PTA axis line) in pixels."""
AREA_SHARE: Final = 0.55
"""How much of its colour an overlapping area keeps, so the areas behind it show."""
STEPS: Final = (1.0, 2.0, 2.5, 5.0, 10.0)


@dataclass(frozen=True, slots=True)
class ChartColors:
    """The colours of a chart's text and lines (the series colours are the spec's)."""

    text: str = colors.TEXT_WORD
    grid: str = colors.GREY_LIGHT
    axis: str = colors.GREY_MID


class Scale(NamedTuple):
    """The value axis: from ``low`` to ``high`` in steps of ``step``."""

    low: float
    high: float
    step: float


def scale(chart: ChartSpec) -> Scale:
    """From 0 (or the lowest value, if below) to the highest value (the highest sum, when
    stacked), in about six round steps."""
    present = [v for series in chart.series for v in series.values if v is not None]
    if chart.stacked:
        tops = [
            sum(max(series.values[i] or 0, 0) for series in chart.series)
            for i in range(len(chart.categories))
        ]
    else:
        tops = present
    lowest = min(0.0, min(present, default=0.0))
    highest = max(0.0, max(tops, default=0.0))
    if highest - lowest <= 0:
        highest = lowest + 1
    rough = (highest - lowest) / 6
    magnitude = 10 ** math.floor(math.log10(rough))
    step = next(f * magnitude for f in STEPS if f * magnitude >= rough)
    return Scale(math.floor(lowest / step) * step, math.ceil(highest / step) * step, step)


def format_number(value: float, language: Language) -> str:
    """``value`` as the chart writes it: thousands grouped, up to six decimals; German
    ``1.250,5``, English ``1,250.5``."""
    rounded = round(value, 6)
    if rounded == 0:
        rounded = 0.0  # no "-0"
    text = f"{rounded:,.6f}".rstrip("0").rstrip(".")
    if language is Language.DE:
        text = text.translate(str.maketrans({",": ".", ".": ","}))
    return text


class _Plot(NamedTuple):
    left: float
    top: float
    right: float
    bottom: float


def draw(
    chart: ChartSpec,
    language: Language = Language.DE,
    palette: ChartColors | None = None,
) -> Drawing:
    """``chart`` as a drawing of ``WIDTH`` × ``HEIGHT`` pixels; numbers in ``language``."""
    palette = palette or ChartColors()
    items: list[DrawingItem] = []
    top = 12.0
    if chart.title:
        items.append(
            DrawingText.line(
                WIDTH / 2,
                top + TITLE_SIZE,
                chart.title,
                TITLE_SIZE,
                palette.text,
                bold=True,
                anchor=TextAnchor.MIDDLE,
                max_width=WIDTH - 20,
            )
        )
        top += TITLE_SIZE + 14
    if chart.unit:
        items.append(DrawingText.line(8, top + LABEL_SIZE, chart.unit, LABEL_SIZE, palette.text))
        top += LABEL_SIZE + 8
    legend_top = HEIGHT - 22 - LABEL_SIZE - 8 if chart.source else HEIGHT - 22
    low, high, step = scale(chart)
    plot = _Plot(56.0, top + 6, WIDTH - 12, legend_top - 26)

    def y(value: float) -> float:
        return plot.bottom - (value - low) / (high - low) * (plot.bottom - plot.top)

    steps = round((high - low) / step)
    for n in range(steps + 1):
        value = low + n * step
        at = y(value)
        zero = abs(value) < step / 2
        items.append(
            DrawingShape(
                _line(plot.left, at, plot.right, at),
                None,
                palette.axis if zero else palette.grid,
                AXIS_WIDTH if zero else GRID_WIDTH,
            )
        )
        items.append(
            DrawingText.line(
                plot.left - 6,
                at + LABEL_SIZE * 0.35,
                format_number(value, language),
                LABEL_SIZE,
                palette.text,
                anchor=TextAnchor.END,
            )
        )

    count = max(len(chart.categories), 1)
    group = (plot.right - plot.left) / count

    def centre(i: int) -> float:
        return plot.left + group * (i + 0.5)

    for i, category in enumerate(chart.categories):
        items.append(
            DrawingText.line(
                centre(i),
                plot.bottom + 6 + LABEL_SIZE,
                category,
                LABEL_SIZE,
                palette.text,
                anchor=TextAnchor.MIDDLE,
                max_width=group - 2,
            )
        )

    def colour(series: int) -> str:
        return chart.colors[series % len(chart.colors)]

    match chart.kind if chart.categories else None:
        case None:
            pass
        case ChartKind.BAR:
            _bars(chart, items, colour, y, centre, group)
        case ChartKind.LINE:
            _lines(chart, items, colour, y, centre)
        case ChartKind.AREA:
            _areas(chart, items, colour, y, centre)
    _legend(chart, items, colour, legend_top, palette.text)
    if chart.source:
        items.append(
            DrawingText.line(
                8, HEIGHT - 8, chart.source, LABEL_SIZE, palette.text, max_width=WIDTH - 16
            )
        )
    return Drawing(WIDTH, HEIGHT, tuple(items))


type _Colour = Callable[[int], str]
type _Y = Callable[[float], float]
type _Centre = Callable[[int], float]


def _bars(
    chart: ChartSpec,
    items: list[DrawingItem],
    colour: _Colour,
    y: _Y,
    centre: _Centre,
    group: float,
) -> None:
    width = group * 0.7
    for i in range(len(chart.categories)):
        below = 0.0
        for s, series in enumerate(chart.series):
            value = series.values[i]
            if value is None:
                continue
            if chart.stacked:
                start, end = below, below + max(value, 0)
                items.append(
                    _bar(centre(i) - width / 2, y(end), width, y(start) - y(end), colour(s))
                )
                below = end
            else:
                bar = width / len(chart.series)
                x = centre(i) - width / 2 + s * bar
                upper, lower = y(max(value, 0)), y(min(value, 0))
                items.append(_bar(x + 0.5, upper, bar - 1, lower - upper, colour(s)))


def _lines(
    chart: ChartSpec, items: list[DrawingItem], colour: _Colour, y: _Y, centre: _Centre
) -> None:
    """A line per series, broken at gaps, with a dot per value."""
    for s, series in enumerate(chart.series):
        points = [
            (centre(i), y(value)) if value is not None else None
            for i, value in enumerate(series.values)
        ]
        segments: list[PathSegment] = []
        pen = False
        for point in points:
            if point is None:
                pen = False
                continue
            segments.append(LineTo(*point) if pen else MoveTo(*point))
            pen = True
        items.append(
            DrawingShape(DrawingPath(tuple(segments)), None, colour(s), 2.5, round_joins=True)
        )
        for point in points:
            if point is not None:
                items.append(
                    DrawingShape(_circle(*point, 3.5), colour(s), None, 0, kind=ShapeKind.ELLIPSE)
                )


def _areas(
    chart: ChartSpec, items: list[DrawingItem], colour: _Colour, y: _Y, centre: _Centre
) -> None:
    """Stacked areas sit on each other; overlapping ones are lighter, each with its line on
    top. A gap counts as zero."""
    count = len(chart.categories)
    floor = [0.0] * count
    for s, series in enumerate(chart.series):
        values = [v or 0.0 for v in series.values]
        tops = [floor[i] + max(v, 0) for i, v in enumerate(values)] if chart.stacked else values
        bases = floor if chart.stacked else [0.0] * count
        segments: list[PathSegment] = [MoveTo(centre(0), y(bases[0]))]
        segments += [LineTo(centre(i), y(tops[i])) for i in range(count)]
        segments += [LineTo(centre(i), y(bases[i])) for i in reversed(range(count))]
        segments.append(ClosePath())
        fill = colour(s) if chart.stacked else colors.tint(colour(s), AREA_SHARE)
        items.append(DrawingShape(DrawingPath(tuple(segments)), fill, None, 0))
        outline: list[PathSegment] = [MoveTo(centre(0), y(tops[0]))]
        outline += [LineTo(centre(i), y(tops[i])) for i in range(1, count)]
        items.append(
            DrawingShape(DrawingPath(tuple(outline)), None, colour(s), 2, round_joins=True)
        )
        if chart.stacked:
            floor = tops


def _legend(
    chart: ChartSpec, items: list[DrawingItem], colour: _Colour, top: float, text: str
) -> None:
    widths = [14 + len(series.name) * LABEL_SIZE * 0.55 + 18 for series in chart.series]
    x = (WIDTH - sum(widths)) / 2
    for s, series in enumerate(chart.series):
        items.append(
            DrawingShape(
                DrawingPath.rectangle(x, top + 4, 10, 10),
                colour(s),
                None,
                0,
                kind=ShapeKind.RECTANGLE,
            )
        )
        items.append(
            DrawingText.line(x + 14, top + 4 + LABEL_SIZE - 1, series.name, LABEL_SIZE, text)
        )
        x += widths[s]


def _bar(x: float, y: float, width: float, height: float, colour: str) -> DrawingShape:
    return DrawingShape(
        DrawingPath.rectangle(x, y, max(width, 0), max(height, 0)),
        colour,
        None,
        0,
        kind=ShapeKind.RECTANGLE,
    )


def _line(x1: float, y1: float, x2: float, y2: float) -> DrawingPath:
    return DrawingPath((MoveTo(x1, y1), LineTo(x2, y2)))


def _circle(x: float, y: float, r: float) -> DrawingPath:
    """A circle as four cubic curves, for outputs that draw the path rather than an ellipse."""
    k = r * 0.5523
    return DrawingPath(
        (
            MoveTo(x + r, y),
            CubicTo(x + r, y + k, x + k, y + r, x, y + r),
            CubicTo(x - k, y + r, x - r, y + k, x - r, y),
            CubicTo(x - r, y - k, x - k, y - r, x, y - r),
            CubicTo(x + k, y - r, x + r, y - k, x + r, y),
            ClosePath(),
        )
    )
