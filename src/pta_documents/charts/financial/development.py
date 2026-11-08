"""A ``DevelopmentChart`` (port of DocLibs ``DevelopmentDrawing.cs``).

Two panels over one row of month slots — bars per month above, the year cumulated (or its growth
rate) below. Both panels share the slot geometry, so a month reads straight down from a bar to
the line point below it; each keeps its own value axis.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Final

from pta_documents.charts.financial import canvas as rules
from pta_documents.charts.financial.canvas import Canvas, EndLabel, NumericAxis
from pta_documents.charts.financial.model import DevelopmentChart, DevelopmentPanel
from pta_documents.drawing.model import Drawing, DrawingHover, Point, TextAnchor

PADDING_LEFT: Final = 52.0
MIN_PADDING_RIGHT: Final = 68.0
"""At least this wide, and as wide as the longest end-of-year label."""
UPPER_HEIGHT: Final = 150.0
LOWER_HEIGHT: Final = UPPER_HEIGHT * 3 / 2
"""The lines panel is half again as tall: its lines run close together early in the year."""
UPPER_TOP: Final = 92.0
LOWER_TOP: Final = UPPER_TOP + UPPER_HEIGHT + 34


def draw(chart: DevelopmentChart, canvas: Canvas) -> Drawing:
    colors = canvas.colors
    labels = canvas.labels
    words = canvas.words
    months = chart.months
    if not months:
        raise ValueError("A development chart needs at least one month.")
    if not 0 <= chart.last_actual < len(months):
        raise ValueError(
            f"The last actual month is {chart.last_actual}, which is not a month of the chart "
            f"(0 to {len(months) - 1})."
        )
    series = colors.series
    current, previous = series[0], series[1 % len(series)]
    width = canvas.width
    growth = chart.lower_panel is DevelopmentPanel.GROWTH

    # A growth panel is a rate, and an estimate is a cumulative figure: it has no place there.
    estimates = [] if growth else [e for e in chart.estimates if 0 <= e.month < len(months)]
    last = len(months) - 1
    last_actual = chart.last_actual
    projected = any(m.projection is not None or m.projection_cumulative is not None for m in months)
    height = LOWER_TOP + LOWER_HEIGHT + 26
    padding_right = max(
        MIN_PADDING_RIGHT, max(rules.text_width(t, 9) for t in _end_label_texts(chart, canvas)) + 10
    )
    plot_width = width - PADDING_LEFT - padding_right
    plot_right = PADDING_LEFT + plot_width
    slot = plot_width / len(months)

    def centre(index: int) -> float:
        return PADDING_LEFT + (index + 0.5) * slot

    # Everything each panel draws, and nothing it does not: an undrawn figure must not pad an axis.
    monthly: list[float] = []
    cumulative: list[float] = []
    compared_from = chart.projection_compared_from
    for i, month in enumerate(months):
        monthly += [month.previous, month.reference]
        cumulative += [month.previous_cumulative, month.reference_cumulative]
        if month.current is not None:
            monthly.append(month.current)
        if month.projection is not None and (
            month.current is None or (compared_from is not None and i >= compared_from)
        ):
            monthly.append(month.projection)
        if month.current_cumulative is not None:
            cumulative.append(month.current_cumulative)
        if month.projection_cumulative is not None:
            cumulative.append(month.projection_cumulative)
    cumulative += [e.value for e in estimates]
    rates = [m.growth for m in months if m.growth is not None] + [chart.reference_rate]

    upper = rules.axis(min(monthly), max(monthly))
    lower = (
        rules.axis(min(rates), max(rates))
        if growth
        else rules.axis(min(cumulative), max(cumulative))
    )

    def upper_y(v: float) -> float:
        return upper.y(v, UPPER_TOP, UPPER_HEIGHT)

    def lower_y(v: float) -> float:
        return lower.y(v, LOWER_TOP, LOWER_HEIGHT)

    # The two answers that matter are stated rather than left to be measured off the lines.
    subtitle = (
        f"{labels.current} {words.versus} {labels.previous} "
        f"{canvas.signed_percent(chart.change_at_period)} {words.at} {months[last_actual].label}"
    )
    if chart.change_at_year_end is not None:
        subtitle += (
            f", {labels.projection} {words.versus} {labels.previous} "
            f"{canvas.signed_percent(chart.change_at_year_end)} {words.at} {months[last].label}."
        )
    else:
        subtitle += "."
    canvas.heading(chart, subtitle)

    legend_x = 20.0

    def legend(fill: str | None, stroke: str, dash: Sequence[float] | None, text: str) -> None:
        nonlocal legend_x
        canvas.rect(legend_x, 57, 10, 10, fill, stroke, 1, dash)
        canvas.text(legend_x + 14, 66, text, 10, colors.text)
        legend_x += 20 + rules.text_width(text, 10)

    legend(previous.strong, previous.stroke, None, labels.previous)
    legend(current.strong, current.stroke, None, labels.current)
    if projected:
        legend(current.pale, current.stroke, rules.PROJECTION_DASH, labels.projection)
    reference_rate = canvas.signed_percent(chart.reference_rate)
    legend(
        colors.reference_fill,
        colors.reference,
        None,
        f"{labels.reference} ({labels.previous} {reference_rate})",
    )
    if estimates:
        canvas.diamond(legend_x + 5, 62, 5, current.pale, current.stroke)
        canvas.text(legend_x + 14, 66, labels.estimate, 10, colors.text)

    def panel(
        caption: str,
        scale: NumericAxis,
        top: float,
        panel_height: float,
        format: Callable[[float], str],
    ) -> None:
        canvas.text(20, top - 10, caption, 10, colors.muted)
        canvas.gridlines(
            scale,
            lambda v: scale.y(v, top, panel_height),
            PADDING_LEFT,
            plot_right,
            format,
            caption,
        )

    panel(words.per_month, upper, UPPER_TOP, UPPER_HEIGHT, canvas.value)
    if growth:
        caption = rules.fill(words.cumulative_growth, labels.current, labels.previous)
        panel(caption, lower, LOWER_TOP, LOWER_HEIGHT, canvas.percent)
    else:
        panel(words.cumulative, lower, LOWER_TOP, LOWER_HEIGHT, canvas.value)

    # Where the actuals end, drawn once and crossing both panels.
    if last_actual < last:
        boundary = PADDING_LEFT + (last_actual + 1) * slot
        tooltip = rules.fill(words.actuals_end, months[last_actual].label)
        for top, panel_height in ((UPPER_TOP, UPPER_HEIGHT), (LOWER_TOP, LOWER_HEIGHT)):
            canvas.line(
                boundary,
                top,
                boundary,
                top + panel_height,
                colors.gridline,
                1.5,
                rules.BOUNDARY_DASH,
                DrawingHover(tooltip, boundary, top),
            )

    # Upper panel: two bars a month, the previous year beside the current one.
    group = slot * 0.66
    bar = (group - 2) / 2

    def segment(
        x: float,
        start: float,
        end: float,
        fill: str,
        stroke: str,
        dash: Sequence[float] | None,
        tooltip: str,
    ) -> None:
        y1, y2 = upper_y(start), upper_y(end)
        top = min(y1, y2)
        hover = DrawingHover(tooltip, x + bar / 2, top)
        canvas.rect(x, top, bar, max(abs(y1 - y2), 0.6), fill, stroke, 0.75, dash, hover)

    for i, month in enumerate(months):
        left = centre(i) - group / 2
        # The previous year with the growth the reference asks for stacked on it in grey.
        segment(
            left,
            0,
            month.previous,
            previous.strong,
            previous.stroke,
            None,
            f"{month.label} {labels.previous}: {canvas.value(month.previous)}",
        )
        segment(
            left,
            month.previous,
            month.reference,
            colors.reference_fill,
            colors.reference,
            None,
            f"{month.label} {labels.reference}: {canvas.value(month.reference)}",
        )
        x = left + bar + 2

        def projection_bar(v: float, x: float = x, label: str = month.label) -> None:
            text = f"{label} {labels.projection}: {canvas.value(v)}"
            segment(x, 0, v, current.pale, current.stroke, rules.PROJECTION_DASH, text)

        def actual_bar(v: float, x: float = x, label: str = month.label) -> None:
            text = f"{label} {labels.current}: {canvas.value(v)}"
            segment(x, 0, v, current.strong, current.stroke, None, text)

        if month.current is not None:
            actual = month.current
            # From the compared-from month on, the projection is drawn against its actual,
            # overlapping: the shorter bar goes in front.
            overlapping = (
                month.projection if compared_from is not None and i >= compared_from else None
            )
            if overlapping is not None and overlapping > actual:
                projection_bar(overlapping)
                actual_bar(actual)
            else:
                actual_bar(actual)
                if overlapping is not None:
                    projection_bar(overlapping)
        elif i > last_actual and month.projection is not None:
            projection_bar(month.projection)

    # The month labels, once, under the lower panel.
    for i, month in enumerate(months):
        canvas.text(
            centre(i),
            LOWER_TOP + LOWER_HEIGHT + 14,
            month.label,
            9,
            colors.text,
            TextAnchor.MIDDLE,
            max_width=slot,
        )

    bottom = LOWER_TOP + LOWER_HEIGHT + 4
    if growth:
        _growth_panel(chart, canvas, lower_y, centre, plot_right, bottom)
        return canvas.finish(height)

    # Lower panel, cumulative: every series rises out of the corner of the panel.
    origin = (PADDING_LEFT, lower_y(0))

    def line(points: Iterable[tuple[int, float]]) -> list[Point]:
        return [origin, *((centre(i), lower_y(v)) for i, v in points)]

    def hover_points(points: Iterable[tuple[int, float]], label: str, color: str) -> None:
        for index, v in points:
            text = f"{months[index].label} {label}: {canvas.value(v)}"
            canvas.hover_point(centre(index), lower_y(v), text, color)

    # What has happened is a shaded area, drawn first so the lines cross it.
    actuals = [(i, m.current_cumulative or 0.0) for i, m in enumerate(months[: last_actual + 1])]
    canvas.polygon([*line(actuals), (centre(actuals[-1][0]), lower_y(0))], current.strong, None, 0)
    hover_points(actuals, labels.current, current.stroke)

    line_width = chart.cumulative_line_width
    references = [(i, m.reference_cumulative) for i, m in enumerate(months)]
    canvas.polyline(line(references), colors.reference, line_width)
    hover_points(references, labels.reference, colors.reference)
    previous_year = [(i, m.previous_cumulative) for i, m in enumerate(months)]
    canvas.polyline(line(previous_year), previous.stroke, line_width)
    hover_points(previous_year, labels.previous, previous.stroke)

    projection = [
        (i, m.projection_cumulative)
        for i, m in enumerate(months)
        if m.projection_cumulative is not None
    ]
    if projection:
        canvas.polyline(line(projection), current.stroke, line_width, rules.PROJECTION_DASH)
        hover_points(projection, labels.projection, current.stroke)

    # An estimate: a diamond on its month, at its figure, with its own name and number.
    for estimate in estimates:
        x, y = centre(estimate.month), lower_y(estimate.value)
        text = f"{estimate.label} {canvas.value(estimate.value)}"
        hover = DrawingHover(f"{estimate.label}: {canvas.value(estimate.value)}", x, y)
        if not chart.hide_estimate_labels:
            # Below the diamond unless there is no room; on a patch of background.
            label_y = y - 9 if y + 15 > LOWER_TOP + LOWER_HEIGHT else y + 15
            patch = rules.text_width(text, 9) + 6
            canvas.rect(x - patch / 2, label_y - 10, patch, 15, colors.patch, None, 0)
            canvas.diamond(x, y, 4.5, current.pale, current.stroke, hover)
            canvas.text(x, label_y, text, 9, current.stroke, TextAnchor.MIDDLE)
        else:
            canvas.diamond(x, y, 4.5, current.pale, current.stroke, hover)

    # The year-end figures beside the ends of their lines.
    end = months[last]
    ends = [
        EndLabel(
            lower_y(end.previous_cumulative),
            f"{labels.previous} {canvas.value(end.previous_cumulative)}",
            previous.stroke,
        ),
        EndLabel(
            lower_y(end.reference_cumulative),
            f"{labels.reference} {canvas.value(end.reference_cumulative)}",
            colors.reference,
        ),
    ]
    if end.projection_cumulative is not None:
        value = end.projection_cumulative
        ends.append(
            EndLabel(lower_y(value), f"{labels.projection} {canvas.value(value)}", current.stroke)
        )
    elif last_actual == last and end.current_cumulative is not None:
        value = end.current_cumulative
        ends.append(
            EndLabel(lower_y(value), f"{labels.current} {canvas.value(value)}", current.stroke)
        )
    canvas.end_labels(ends, plot_right + 5, bottom)
    return canvas.finish(height)


def _end_label_texts(chart: DevelopmentChart, canvas: Canvas) -> list[str]:
    """Every end label the lower panel may write, for the room they need."""
    labels = canvas.labels
    last = chart.months[-1]
    if chart.lower_panel is DevelopmentPanel.GROWTH:
        texts = [f"{labels.reference} {canvas.percent(chart.reference_rate)}"]
        for m in chart.months:
            if m.growth is not None:
                texts.append(f"{labels.projection} {canvas.percent(m.growth)}")
                texts.append(f"{labels.current} {canvas.percent(m.growth)}")
        return texts
    texts = [
        f"{labels.previous} {canvas.value(last.previous_cumulative)}",
        f"{labels.reference} {canvas.value(last.reference_cumulative)}",
    ]
    if last.projection_cumulative is not None:
        texts.append(f"{labels.projection} {canvas.value(last.projection_cumulative)}")
    if last.current_cumulative is not None:
        texts.append(f"{labels.current} {canvas.value(last.current_cumulative)}")
    return texts


def _growth_panel(
    chart: DevelopmentChart,
    canvas: Canvas,
    y: Callable[[float], float],
    centre: Callable[[int], float],
    plot_right: float,
    bottom: float,
) -> None:
    """Lower panel, growth: solid through the last actual, dashed after it, the segments
    meeting; the flat reference rate solid."""
    colors = canvas.colors
    labels = canvas.labels
    words = canvas.words
    months = chart.months
    current = colors.series[0]
    reference_y = y(chart.reference_rate)
    canvas.line(
        PADDING_LEFT,
        reference_y,
        plot_right,
        reference_y,
        colors.reference,
        1.5,
        hover=DrawingHover(
            f"{labels.reference}: {canvas.percent(chart.reference_rate)}",
            (PADDING_LEFT + plot_right) / 2,
            reference_y,
        ),
    )

    def rate(i: int) -> float:
        value = months[i].growth
        assert value is not None
        return value

    def points(indices: Iterable[int]) -> list[Point]:
        return [(centre(i), y(rate(i))) for i in indices]

    actual = [i for i in range(chart.last_actual + 1) if months[i].growth is not None]
    canvas.polyline(points(actual), current.stroke, 1.5)
    for i in actual:
        text = (
            f"{months[i].label} {labels.current} {words.versus} {labels.previous}: "
            f"{canvas.percent(rate(i))}"
        )
        canvas.hover_point(centre(i), y(rate(i)), text, current.stroke)

    projection = [actual[-1]] if actual else []
    projection += [
        i for i in range(chart.last_actual + 1, len(months)) if months[i].growth is not None
    ]
    if len(projection) > 1:
        canvas.polyline(points(projection), current.stroke, 1.5, rules.PROJECTION_DASH)
        for i in projection[1:]:
            text = (
                f"{months[i].label} {labels.projection} {words.versus} {labels.previous}: "
                f"{canvas.percent(rate(i))}"
            )
            canvas.hover_point(centre(i), y(rate(i)), text, current.stroke)

    ends = [
        EndLabel(
            reference_y,
            f"{labels.reference} {canvas.percent(chart.reference_rate)}",
            colors.reference,
        )
    ]
    if actual:
        value = rate(actual[-1])
        ends.append(EndLabel(y(value), f"{labels.current} {canvas.percent(value)}", current.stroke))
    year_end = months[-1].growth
    if len(projection) > 1 and year_end is not None:
        ends.append(
            EndLabel(y(year_end), f"{labels.projection} {canvas.percent(year_end)}", current.stroke)
        )
    canvas.end_labels(ends, plot_right + 5, bottom)
