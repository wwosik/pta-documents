"""A ``GrowthByRowChart`` (port of DocLibs ``GrowthByRowDrawing.cs``).

Horizontal bars diverging from zero. The change is the only measure, so it takes series 1; the
reference bar and both overall lines are neutral, never a series colour.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

from pta_documents.charts.financial import canvas as rules
from pta_documents.charts.financial.canvas import Canvas
from pta_documents.charts.financial.model import GrowthByRowChart, GrowthRow
from pta_documents.drawing.model import Drawing, DrawingHover, TextAnchor

PADDING_BOTTOM: Final = 20.0
PADDING_LEFT: Final = 122.0
PADDING_RIGHT: Final = 8.0
ROW_HEIGHT: Final = 34.0
BAR_HEIGHT: Final = 17.0
LEGEND_Y: Final = 50.0
COLUMN_WIDTH: Final = 38.0
"""The figures live in columns right of the plot, not beside the bars."""
COLUMN_GAP: Final = 12.0
PADDING_TOP: Final = 100.0
COLUMN_HEADER_Y: Final = PADDING_TOP - 32


def draw(chart: GrowthByRowChart, canvas: Canvas) -> Drawing:
    colors = canvas.colors
    labels = canvas.labels
    series = colors.series[0]
    rows = chart.rows
    width = canvas.width

    # What happened, and what was meant to happen; the first carries the verdict.
    columns: list[tuple[str, Callable[[GrowthRow], str], Callable[[GrowthRow], str]]] = [
        (
            labels.change,
            lambda row: canvas.percent(row.change),
            lambda row: canvas.verdict(row.change, row.reference),
        ),
        (labels.reference, lambda row: canvas.percent(row.reference), lambda _: colors.reference),
    ]

    plot_height = max(1, len(rows)) * ROW_HEIGHT
    height = PADDING_TOP + plot_height + PADDING_BOTTOM
    plot_width = width - PADDING_LEFT - PADDING_RIGHT - COLUMN_GAP - len(columns) * COLUMN_WIDTH
    columns_left = PADDING_LEFT + plot_width + COLUMN_GAP

    def column_right(column: int) -> float:
        return columns_left + (column + 1) * COLUMN_WIDTH - 4

    high = 1.0 if not rows else max(0.0001, max(max(abs(r.change), abs(r.reference)) for r in rows))
    low = 0.0 if not rows else min(0.0, min(min(r.change, r.reference) for r in rows))
    overall = chart.overall
    high = max(high, abs(overall.change), abs(overall.reference))
    low = min(low, overall.change, overall.reference)
    span = 1 if high - low <= 0 else high - low

    def x_of(v: float) -> float:
        return PADDING_LEFT + (v - low) / span * plot_width

    zero_x = x_of(0)
    canvas.heading(chart, "")

    legend_x = 20.0

    def legend(swatch: Callable[[float], None], text: str) -> None:
        nonlocal legend_x
        swatch(legend_x)
        canvas.text(legend_x + 17, LEGEND_Y, text, 11, colors.text)
        legend_x += 30 + rules.text_width(text, 11)

    legend(
        lambda x: canvas.rect(x, LEGEND_Y - 10, 12, 12, series.fill, series.stroke, 0.75),
        labels.change,
    )
    legend(
        lambda x: canvas.rect(x, LEGEND_Y - 10, 12, 12, None, colors.reference, 2),
        labels.reference,
    )
    legend(
        lambda x: canvas.line(
            x, LEGEND_Y - 4, x + 12, LEGEND_Y - 4, colors.reference, 1.5, rules.REFERENCE_DASH
        ),
        f"{labels.overall} {labels.reference}",
    )
    legend(
        lambda x: canvas.line(
            x, LEGEND_Y - 4, x + 12, LEGEND_Y - 4, series.stroke, 1.5, rules.REFERENCE_DASH
        ),
        f"{labels.overall} {labels.change}",
    )

    canvas.line(zero_x, PADDING_TOP, zero_x, PADDING_TOP + plot_height, colors.axis, 1)
    for c, (header, _, _) in enumerate(columns):
        canvas.text(column_right(c), COLUMN_HEADER_Y, header, 9, colors.muted, TextAnchor.END)

    for i, row in enumerate(rows):
        centre = PADDING_TOP + ROW_HEIGHT * i + ROW_HEIGHT / 2
        top = centre - BAR_HEIGHT / 2
        change_x, reference_x = x_of(row.change), x_of(row.reference)
        change_left = min(change_x, zero_x)
        change_width = max(abs(change_x - zero_x), 0.5)
        reference_left = min(reference_x, zero_x)
        reference_width = max(abs(reference_x - zero_x), 0.5)

        # The emphasised row takes the emphasis fill: still series 1, one row picked out.
        tooltip = f"{row.label} {labels.change}: {canvas.percent(row.change)}"
        canvas.rect(
            change_left,
            top,
            change_width,
            BAR_HEIGHT,
            colors.emphasis if row.emphasised else series.fill,
            series.stroke,
            0.75,
            hover=DrawingHover(tooltip, change_left + change_width / 2, top),
        )
        canvas.rect(
            reference_left,
            top,
            reference_width,
            BAR_HEIGHT,
            None,
            colors.reference,
            2,
            hover=DrawingHover(
                f"{row.label} {labels.reference}: {canvas.percent(row.reference)}",
                reference_left + reference_width / 2,
                top,
            ),
        )

        lines = rules.wrap(row.label, 17)
        first = centre + 4 - (len(lines) - 1) * 6.5
        for n, text in enumerate(lines):
            canvas.text(
                PADDING_LEFT - 8,
                first + n * 13,
                text,
                11,
                colors.text,
                TextAnchor.END,
                row.emphasised,
            )
        for c, (_, value, color) in enumerate(columns):
            canvas.text(column_right(c), centre + 3.5, value(row), 10, color(row), TextAnchor.END)

    # The overall labels stay on their dashed lines, sliding back inside the plot near an edge.
    def label_x(line_x: float, text: str) -> float:
        half = rules.text_width(text, 10) / 2
        lowest = PADDING_LEFT + half
        return min(max(line_x, lowest), max(lowest, PADDING_LEFT + plot_width - half))

    overall_reference_x = x_of(overall.reference)
    reference_label = f"{labels.overall} {labels.reference} {canvas.percent(overall.reference)}"
    canvas.line(
        overall_reference_x,
        PADDING_TOP,
        overall_reference_x,
        PADDING_TOP + plot_height,
        colors.reference,
        1.5,
        rules.REFERENCE_DASH,
        DrawingHover(reference_label, overall_reference_x, PADDING_TOP),
    )
    canvas.text(
        label_x(overall_reference_x, reference_label),
        PADDING_TOP - 6,
        reference_label,
        10,
        colors.reference,
        TextAnchor.MIDDLE,
    )

    overall_change_x = x_of(overall.change)
    change_label = f"{labels.overall} {labels.change} {canvas.percent(overall.change)}"
    canvas.line(
        overall_change_x,
        PADDING_TOP,
        overall_change_x,
        PADDING_TOP + plot_height,
        series.stroke,
        1.5,
        rules.REFERENCE_DASH,
        DrawingHover(change_label, overall_change_x, PADDING_TOP + 14),
    )
    canvas.text(
        label_x(overall_change_x, change_label),
        PADDING_TOP - 20,
        change_label,
        10,
        series.stroke,
        TextAnchor.MIDDLE,
    )
    return canvas.finish(height)
