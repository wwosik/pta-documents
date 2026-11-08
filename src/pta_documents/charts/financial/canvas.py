"""What every financial chart draws with (port of DocLibs ``FinancialCanvas.cs``).

The items so far, the colours, the number formats and the rules all charts share: the
round-step axis, verdict colours, label wrapping and end labels pushed apart.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from typing import Final

from pta_documents.charts.financial.model import FinancialChart
from pta_documents.charts.financial.options import (
    FinancialChartLabels,
    FinancialChartOptions,
    FinancialChartWords,
    format_decimal,
)
from pta_documents.design.chart_colors import FinancialChartColors
from pta_documents.drawing.model import (
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
    Point,
    ShapeKind,
    TextAnchor,
)
from pta_documents.drawing.svg_output import estimate_width

PROJECTION_DASH: Final = (3.0, 2.0)
"""The dash that means "projection, not an actual" — and nothing else on these charts."""
REFERENCE_DASH: Final = (5.0, 4.0)
"""The dashed reference lines and the overall lines of the row charts."""
BOUNDARY_DASH: Final = (2.0, 3.0)
"""The rule where the actuals end, or where one year meets the next."""


@dataclass(frozen=True, slots=True)
class NumericAxis:
    """A value axis: where its ends sit, and the interval between its gridlines."""

    min: float
    max: float
    step: float

    def y(self, value: float, top: float, height: float) -> float:
        """The y of ``value`` on a panel from ``top``, ``height`` tall."""
        return top + height - ((value - self.min) / (self.max - self.min) * height)


def step(rough: float) -> float:
    """The nearest round number at or above ``rough``: 1, 2, 2.5 or 5 times a power of ten."""
    if rough <= 0 or not math.isfinite(rough):
        return 1
    magnitude = 10 ** math.floor(math.log10(rough))
    ratio = rough / magnitude
    if ratio <= 1:
        factor = 1.0
    elif ratio <= 2:
        factor = 2.0
    elif ratio <= 2.5:
        factor = 2.5
    elif ratio <= 5:
        factor = 5.0
    else:
        factor = 10.0
    return factor * magnitude


def axis(low: float, high: float, ticks: int = 5) -> NumericAxis:
    """An axis over ``low`` … ``high`` with a round step, always including zero, padded so the
    topmost tick label and the end labels have room. The padding goes on before the rounding,
    so a series ending exactly on a round number gains a gridline above it."""
    low = min(0.0, low)
    high = max(0.0, high)
    # At least 0.06: a growth-rate panel (fractions) keeps six points of headroom.
    padding = max(high - low, 1) * 0.06
    interval = step((high + padding - (low - padding if low < 0 else low)) / ticks)
    bottom = math.floor((low - padding) / interval) * interval if low < 0 else 0.0
    top = math.ceil((high + padding) / interval) * interval
    return NumericAxis(bottom, bottom + interval if top <= bottom else top, interval)


def wrap(text: str, width: int) -> list[str]:
    """A label wrapped by words at about ``width`` characters; a longer word stays whole."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = word if not current else f"{current} {word}"
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current or not lines:
        lines.append(current)
    return lines


def text_width(text: str, size: float) -> float:
    """Roughly how wide a label is: the SVG is written, not measured."""
    return estimate_width(text, size)


def fill(template: str, *values: object) -> str:
    """``template`` with its ``{0}``, ``{1}`` filled."""
    return template.format(*values)


def _rect(x: float, y: float, width: float, height: float) -> DrawingPath:
    return DrawingPath.rectangle(x, y, max(width, 0), max(height, 0))


def _circle(x: float, y: float, r: float) -> DrawingPath:
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


@dataclass(frozen=True, slots=True)
class EndLabel:
    y: float
    text: str
    color: str


class Canvas:
    """Collects the items of one chart; made anew for every chart."""

    def __init__(self, options: FinancialChartOptions) -> None:
        self.options = options
        self.colors: FinancialChartColors = options.colors
        self.width: float = options.width
        self.items: list[DrawingItem] = []

    @property
    def labels(self) -> FinancialChartLabels:
        return self.options.effective_labels

    @property
    def words(self) -> FinancialChartWords:
        return self.options.words

    def finish(self, height: float) -> Drawing:
        """The drawing, on the chart surface when there is one."""
        surface = self.colors.surface
        items: list[DrawingItem] = list(self.items)
        if surface is not None:
            ground = DrawingShape(
                _rect(0, 0, self.width, height), surface, None, 0, kind=ShapeKind.RECTANGLE
            )
            items.insert(0, ground)
        return Drawing(self.width, height, tuple(items))

    def add(self, item: DrawingItem) -> None:
        self.items.append(item)

    # ------------------------------------------------------------------ shapes

    def rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        fill: str | None,
        stroke: str | None,
        stroke_width: float,
        dash: Sequence[float] | None = None,
        hover: DrawingHover | None = None,
    ) -> None:
        self.items.append(
            DrawingShape(
                _rect(x, y, width, height),
                fill,
                stroke,
                stroke_width,
                dash=None if dash is None else tuple(dash),
                kind=ShapeKind.RECTANGLE,
                hover=hover,
            )
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: str,
        width: float,
        dash: Sequence[float] | None = None,
        hover: DrawingHover | None = None,
        round_joins: bool = False,
    ) -> None:
        path = DrawingPath((MoveTo(x1, y1), LineTo(x2, y2)))
        self.items.append(
            DrawingShape(
                path,
                None,
                stroke,
                width,
                dash=None if dash is None else tuple(dash),
                hover=hover,
                round_joins=round_joins,
            )
        )

    def polyline(
        self,
        points: Sequence[Point],
        stroke: str,
        width: float,
        dash: Sequence[float] | None = None,
        round_joins: bool = False,
    ) -> None:
        if len(points) < 2:
            return
        segments = (MoveTo(*points[0]), *(LineTo(x, y) for x, y in points[1:]))
        self.items.append(
            DrawingShape(
                DrawingPath(segments),
                None,
                stroke,
                width,
                dash=None if dash is None else tuple(dash),
                round_joins=round_joins,
            )
        )

    def polygon(
        self,
        points: Sequence[Point],
        fill: str | None,
        stroke: str | None,
        width: float,
        hover: DrawingHover | None = None,
    ) -> None:
        segments = (MoveTo(*points[0]), *(LineTo(x, y) for x, y in points[1:]), ClosePath())
        self.items.append(DrawingShape(DrawingPath(segments), fill, stroke, width, hover=hover))

    def dot(self, x: float, y: float, radius: float, fill: str) -> None:
        self.items.append(
            DrawingShape(_circle(x, y, radius), fill, None, 0, kind=ShapeKind.ELLIPSE)
        )

    def diamond(
        self,
        x: float,
        y: float,
        radius: float,
        fill: str,
        stroke: str,
        hover: DrawingHover | None = None,
    ) -> None:
        """The estimate's mark: the one shape that is neither a bar nor a line."""
        points = ((x, y - radius), (x + radius, y), (x, y + radius), (x - radius, y))
        self.polygon(points, fill, stroke, 1.25, hover)

    def text(
        self,
        x: float,
        baseline: float,
        text: str,
        size: float,
        color: str,
        anchor: TextAnchor = TextAnchor.START,
        bold: bool = False,
        max_width: float | None = None,
    ) -> None:
        self.items.append(
            DrawingText.line(
                x, baseline, text, size, color, bold=bold, anchor=anchor, max_width=max_width
            )
        )

    def spans(
        self,
        x: float,
        baseline: float,
        spans: Sequence[DrawingSpan],
        size: float,
        color: str,
        anchor: TextAnchor = TextAnchor.START,
    ) -> None:
        self.items.append(DrawingText(x, baseline, tuple(spans), size, color, anchor=anchor))

    def hover_point(self, x: float, y: float, text: str, color: str) -> None:
        """A point of a line: an invisible hit area with a dot in the line's colour shown while
        hovered."""
        self.items.append(DrawingHotspot(x, y, 10, dot=color, hover=DrawingHover(text, x, y)))

    def heading(
        self,
        chart: FinancialChart,
        subtitle: str,
        x: float = 20,
        subtitle_baseline: float = 44,
    ) -> None:
        """The title with the period in brackets, and the subtitle (the chart's own unless the
        caller set one)."""
        period = chart.period
        title = chart.title if not period or not period.strip() else f"{chart.title} ({period})"
        self.text(x, 26, title, 15, self.colors.text, bold=True, max_width=self.width - x - 10)
        line = chart.subtitle if chart.subtitle is not None else subtitle
        if line:
            self.text(
                x, subtitle_baseline, line, 10, self.colors.muted, max_width=self.width - x - 10
            )

    # ------------------------------------------------------------------ numbers

    def _percent(self, value: float, always: bool) -> str:
        number = format_decimal(value * 100, 1, always, self.options.german)
        return number + (" %" if self.options.german else "%")

    def percent(self, value: float) -> str:
        """A percentage as every chart writes one: one decimal when it has one."""
        return self._percent(value, always=False)

    def signed_percent(self, value: float) -> str:
        """A percentage read as a difference: always signed, always one decimal."""
        return ("+" if value > 0 else "") + self._percent(value, always=True)

    def rate(self, value: float) -> str:
        """A share as a level: one decimal always and no sign."""
        return self._percent(value, always=True)

    def signed_points(self, value: float) -> str:
        """A distance between two shares, in percentage points (``-1,2 Pp.``)."""
        number = format_decimal(value * 100, 1, True, self.options.german)
        return ("+" if value > 0 else "") + number + self.words.points

    @property
    def scale_factor(self) -> float:
        return self.options.scale if self.options.scale > 0 else 1

    def plain(self, value: float) -> str:
        """A value at the options' scale, without its unit."""
        return format_decimal(value / self.scale_factor, 1, False, self.options.german)

    def value(self, value: float) -> str:
        """A value at the options' scale, with its unit."""
        unit = self.options.unit
        return self.plain(value) + (f" {unit}" if unit else "")

    def table_value(self, value: float) -> str:
        """A value as a table writes it: one decimal always, so the column lines up."""
        return format_decimal(value / self.scale_factor, 1, True, self.options.german)

    def verdict(self, value: float, against: float) -> str:
        """A figure's colour: ahead of what it is measured against, level with it, or
        behind. Only figures carry it; a bar keeps its series colour."""
        difference = value - against
        if difference > self.options.tolerance:
            return self.colors.ahead
        if difference < -self.options.tolerance:
            return self.colors.behind
        return self.colors.level

    # ------------------------------------------------------------------ shared rules

    def gridlines(
        self,
        scale: NumericAxis,
        y: Callable[[float], float],
        left: float,
        right: float,
        format: Callable[[float], str],
        caption: str | None = None,
    ) -> None:
        """The gridlines and tick labels of a value axis; the one at zero in the axis
        colour."""
        ticks = round((scale.max - scale.min) / scale.step)
        for t in range(ticks + 1):
            value = scale.min + t * scale.step
            at = y(value)
            zero = abs(value) < scale.step / 1000
            text = format(value)
            hover = DrawingHover(
                text if caption is None else f"{caption}: {text}", (left + right) / 2, at
            )
            color = self.colors.axis if zero else self.colors.gridline
            self.line(left, at, right, at, color, 1, hover=hover)
            self.text(left - 6, at + 3, text, 9, self.colors.muted, TextAnchor.END)

    def end_labels(self, labels: list[EndLabel], x: float, bottom: float) -> None:
        """The figures at the ends of lines: pushed at least 11 px apart and kept above
        ``bottom``."""
        if not labels:
            return
        labels.sort(key=lambda label: label.y)
        for i in range(1, len(labels)):
            if labels[i].y - labels[i - 1].y < 11:
                labels[i] = replace(labels[i], y=labels[i - 1].y + 11)
        overflow = labels[-1].y - bottom
        for label in labels:
            y = label.y - overflow if overflow > 0 else label.y
            self.text(x, y + 3, label.text, 9, label.color)
