"""A ``GrowthTrendChart`` (port of DocLibs ``GrowthTrendDrawing.cs``).

One panel, one line: the growth rate at every month against the flat annual reference rate. The
rate is a fraction, written as a percentage, so this panel has no scale or unit.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Final

from pta_documents.charts.financial import canvas as rules
from pta_documents.charts.financial.canvas import Canvas, EndLabel
from pta_documents.charts.financial.model import GrowthTrendChart
from pta_documents.drawing.model import Drawing, DrawingHover, Point, TextAnchor

PADDING_LEFT: Final = 52.0
MIN_PADDING_RIGHT: Final = 96.0
"""Room for the end labels: at least this, and as much as the longest needs."""
PLOT_HEIGHT: Final = 220.0
PLOT_TOP: Final = 74.0


def draw(chart: GrowthTrendChart, canvas: Canvas) -> Drawing:
    colors = canvas.colors
    labels = canvas.labels
    words = canvas.words
    months = chart.months
    if not months:
        raise ValueError("A growth-trend chart needs at least one month.")
    current = colors.series[0]
    width = canvas.width
    last_actual = min(max(chart.last_actual, -1), len(months) - 1)
    bottom = PLOT_TOP + PLOT_HEIGHT
    changes = [m.change for m in months if m.change is not None]
    end_texts = [
        text
        for rate in changes
        for text in (
            f"{labels.current} {canvas.percent(rate)}",
            f"{labels.projection} {canvas.percent(rate)}",
        )
    ] + [f"{labels.reference} {canvas.percent(chart.reference)}"]
    padding_right = max(MIN_PADDING_RIGHT, max(rules.text_width(t, 9) for t in end_texts) + 10)
    plot_width = width - PADDING_LEFT - padding_right
    right = PADDING_LEFT + plot_width
    slot = plot_width / len(months)

    def centre(index: int) -> float:
        return PADDING_LEFT + (index + 0.5) * slot

    drawn = [*changes, chart.reference]
    scale = rules.axis(min(drawn), max(drawn))

    def y(v: float) -> float:
        return scale.y(v, PLOT_TOP, PLOT_HEIGHT)

    def rate(i: int) -> float:
        value = months[i].change
        assert value is not None
        return value

    actual = [i for i in range(last_actual + 1) if months[i].change is not None]
    projection = [actual[-1]] if actual else []
    projection += [i for i in range(last_actual + 1, len(months)) if months[i].change is not None]

    canvas.heading(chart, rules.fill(words.growth_trend, labels.previous, labels.reference))

    legend_x = 20.0

    def legend(stroke: str, dash: Sequence[float] | None, text: str) -> None:
        nonlocal legend_x
        canvas.line(legend_x, 57, legend_x + 16, 57, stroke, 2.5, dash)
        canvas.text(legend_x + 21, 60.5, text, 10, colors.text)
        legend_x += 27 + rules.text_width(text, 10)

    legend(current.stroke, None, f"{labels.current} {words.versus} {labels.previous}")
    if len(projection) > 1:
        legend(current.stroke, rules.PROJECTION_DASH, labels.projection)
    legend(colors.reference, None, f"{labels.reference} ({canvas.signed_percent(chart.reference)})")

    canvas.gridlines(scale, y, PADDING_LEFT, right, canvas.percent)

    reference_y = y(chart.reference)
    canvas.line(
        PADDING_LEFT,
        reference_y,
        right,
        reference_y,
        colors.reference,
        1.5,
        hover=DrawingHover(
            f"{labels.reference}: {canvas.percent(chart.reference)}",
            PADDING_LEFT + plot_width / 2,
            reference_y,
        ),
    )

    def points(indices: Iterable[int]) -> list[Point]:
        return [(centre(i), y(rate(i))) for i in indices]

    canvas.polyline(points(actual), current.stroke, 1.5)
    for i in actual:
        text = (
            f"{months[i].label} {labels.current} {words.versus} {labels.previous}: "
            f"{canvas.percent(rate(i))}"
        )
        canvas.hover_point(centre(i), y(rate(i)), text, current.stroke)
    if len(projection) > 1:
        canvas.polyline(points(projection), current.stroke, 1.5, rules.PROJECTION_DASH)
        for i in projection[1:]:
            text = f"{months[i].label} {labels.projection}: {canvas.percent(rate(i))}"
            canvas.hover_point(centre(i), y(rate(i)), text, current.stroke)

    for i, month in enumerate(months):
        canvas.text(
            centre(i), bottom + 14, month.label, 9, colors.text, TextAnchor.MIDDLE, max_width=slot
        )

    ends: list[EndLabel] = []
    if actual:
        value = rate(actual[-1])
        ends.append(EndLabel(y(value), f"{labels.current} {canvas.percent(value)}", current.stroke))
    year_end = months[-1].change
    if len(projection) > 1 and year_end is not None:
        ends.append(
            EndLabel(y(year_end), f"{labels.projection} {canvas.percent(year_end)}", current.stroke)
        )
    ends.append(
        EndLabel(
            reference_y, f"{labels.reference} {canvas.percent(chart.reference)}", colors.reference
        )
    )
    canvas.end_labels(ends, right + 5, bottom + 4)
    return canvas.finish(bottom + 40)
