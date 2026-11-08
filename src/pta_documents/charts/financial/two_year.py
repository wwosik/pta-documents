"""A ``TwoYearChart`` (port of DocLibs ``TwoYearDrawing.cs``).

One panel, two years of month slots, one line per category. Colour is the only thing telling
the lines apart, so the legend is not optional, and nothing else on the plot has a hue.
"""

from __future__ import annotations

from typing import Final

from pta_documents.charts.financial import canvas as rules
from pta_documents.charts.financial.canvas import Canvas
from pta_documents.charts.financial.model import TwoYearChart, TwoYearSeries
from pta_documents.design.chart_colors import FinancialChartColors
from pta_documents.drawing.model import Drawing, TextAnchor

MAX_CATEGORIES: Final = 6
PADDING_LEFT: Final = 52.0
PADDING_RIGHT: Final = 16.0
"""Nothing is written past the plot: the legend identifies the lines."""
PLOT_HEIGHT: Final = 250.0
LEGEND_TOP: Final = 62.0
LEGEND_ROW: Final = 16.0
SWATCH: Final = 16.0


def draw(chart: TwoYearChart, canvas: Canvas) -> Drawing:
    colors = canvas.colors
    width = canvas.width
    slots = len(chart.months)
    if slots == 0:
        raise ValueError("A two-year chart needs at least one month.")
    for series in chart.series:
        if len(series.values) != slots:
            raise ValueError(
                f"The category '{series.label}' has {len(series.values)} values for {slots} months."
            )
    hues = colours(chart, colors)
    plot_width = width - PADDING_LEFT - PADDING_RIGHT
    right = PADDING_LEFT + plot_width
    slot = plot_width / slots

    def centre(index: int) -> float:
        return PADDING_LEFT + (index + 0.5) * slot

    subtitle = rules.fill(canvas.words.month_by_month, chart.previous_year, chart.current_year)
    canvas.heading(chart, subtitle)

    # The legend first: how many rows it takes decides where the plot starts.
    rows = 1
    x = 20.0
    for s, series in enumerate(chart.series):
        entry = SWATCH + 5 + rules.text_width(series.label, 10)
        if x > 20 and x + entry > width - 20:
            rows += 1
            x = 20
        y = LEGEND_TOP + (rows - 1) * LEGEND_ROW
        canvas.line(x, y, x + SWATCH, y, hues[s], 2.5, round_joins=True)
        canvas.text(x + SWATCH + 5, y + 3.5, series.label, 10, colors.text)
        x += entry + 14

    top = LEGEND_TOP + rows * LEGEND_ROW + 14
    bottom = top + PLOT_HEIGHT
    drawn = [v for series in chart.series for v in series.values if v is not None]
    scale = rules.axis(min(drawn) if drawn else 0, max(drawn) if drawn else 1)

    def y_of(v: float) -> float:
        return scale.y(v, top, PLOT_HEIGHT)

    canvas.gridlines(scale, y_of, PADDING_LEFT, right, canvas.value)

    # Where one year ends and the next begins: a rule, not a gap.
    half = slots // 2
    boundary = PADDING_LEFT + half * slot
    canvas.line(boundary, top, boundary, bottom, colors.gridline, 1.5, rules.BOUNDARY_DASH)

    # A run of consecutive months is one line; a single month between gaps is a dot.
    for s, series in enumerate(chart.series):
        run: list[tuple[int, float]] = []

        def flush(
            run: list[tuple[int, float]] = run, s: int = s, label: str = series.label
        ) -> None:
            if len(run) > 1:
                points = [(centre(i), y_of(v)) for i, v in run]
                canvas.polyline(points, hues[s], 1.6, round_joins=True)
            elif len(run) == 1:
                canvas.dot(centre(run[0][0]), y_of(run[0][1]), 1.8, hues[s])
            for index, v in run:
                text = f"{chart.months[index]} {label}: {canvas.value(v)}"
                canvas.hover_point(centre(index), y_of(v), text, hues[s])
            run.clear()

        for i, value in enumerate(series.values):
            if value is not None:
                run.append((i, value))
            else:
                flush()
        flush()

    # The month labels, and under them the year each half belongs to.
    for i, month in enumerate(chart.months):
        canvas.text(
            centre(i), bottom + 13, month, 8, colors.text, TextAnchor.MIDDLE, max_width=slot
        )
    canvas.text(
        PADDING_LEFT + half * slot / 2,
        bottom + 30,
        chart.previous_year,
        10,
        colors.muted,
        TextAnchor.MIDDLE,
        bold=True,
    )
    canvas.text(
        boundary + (slots - half) * slot / 2,
        bottom + 30,
        chart.current_year,
        10,
        colors.muted,
        TextAnchor.MIDDLE,
        bold=True,
    )
    return canvas.finish(bottom + 42)


def colours(chart: TwoYearChart, colors: FinancialChartColors) -> tuple[str, ...]:
    """The colour of each category: the category colours handed out by how high its line runs
    (the mean of its values), highest first. Raises ``ValueError`` beyond six categories."""
    if len(chart.series) > MAX_CATEGORIES:
        raise ValueError(
            f"A two-year chart draws at most {MAX_CATEGORIES} categories; this one has "
            f"{len(chart.series)}."
        )

    def height(series: TwoYearSeries) -> float:
        values = [v for v in series.values if v is not None]
        return sum(values) / len(values) if values else 0

    ranked = sorted(range(len(chart.series)), key=lambda i: (-height(chart.series[i]), i))
    hues = [""] * len(chart.series)
    for rank, index in enumerate(ranked):
        hues[index] = colors.categories[rank % len(colors.categories)]
    return tuple(hues)
