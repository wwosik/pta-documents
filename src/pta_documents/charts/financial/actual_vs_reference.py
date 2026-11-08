"""An ``ActualVsReferenceChart`` (port of DocLibs ``ActualVsReferenceDrawing.cs``).

One band per row, one bar per measure, all diverging around a shared zero line. Measures of one
series share a hue, the month solid and the year to date pale; a bar behind its reference keeps
the colour of one ahead of it.
"""

from __future__ import annotations

from typing import Final

from pta_documents.charts.financial import canvas as rules
from pta_documents.charts.financial.canvas import Canvas
from pta_documents.charts.financial.model import ActualVsReferenceChart, Measure, ReferenceDisplay
from pta_documents.charts.financial.options import format_decimal
from pta_documents.design.chart_colors import SeriesColors
from pta_documents.drawing.model import Drawing, DrawingHover, DrawingSpan, TextAnchor

PADDING_BOTTOM: Final = 22.0
PADDING_LEFT: Final = 132.0
PADDING_RIGHT: Final = 52.0
BAR_HEIGHT: Final = 11.0
BAR_GAP: Final = 2.0
BAND_PADDING: Final = 14.0
LEGEND_Y: Final = 68.0
PADDING_TOP: Final = 92.0


def draw(chart: ActualVsReferenceChart, canvas: Canvas) -> Drawing:
    colors = canvas.colors
    labels = canvas.labels
    words = canvas.words
    rows = chart.rows
    width = canvas.width
    if not rows or not rows[0].measures:
        raise ValueError(
            "An actual-vs-reference chart needs at least one row with at least one measure."
        )
    measure_count = len(rows[0].measures)
    if any(len(row.measures) != measure_count for row in rows):
        raise ValueError(
            "Every row of an actual-vs-reference chart needs the same measures; the first has "
            f"{measure_count}."
        )

    value_display = chart.display is ReferenceDisplay.VALUE
    unit = canvas.options.unit

    def actual_of(m: Measure) -> float:
        return m.current / canvas.scale_factor if value_display else m.change

    def reference_of(m: Measure) -> float:
        return m.reference_value / canvas.scale_factor if value_display else m.reference

    def format(v: float) -> str:
        if not value_display:
            return canvas.percent(v)
        number = format_decimal(v, 1, False, canvas.options.german)
        return number + (f" {unit}" if unit else "")

    band_height = measure_count * (BAR_HEIGHT + BAR_GAP) + BAND_PADDING
    plot_height = len(rows) * band_height
    height = PADDING_TOP + plot_height + PADDING_BOTTOM
    plot_width = width - PADDING_LEFT - PADDING_RIGHT

    # The bars carrying a reference set the scale together with those references.
    measures = [m for row in rows for m in row.measures]
    anchors = [v for m in measures if m.year_to_date for v in (actual_of(m), reference_of(m))]
    if not anchors:
        anchors = [actual_of(m) for m in measures]
    high = max(0.0, max(anchors))
    low = min(0.0, min(anchors))

    # A bar without a reference may widen the axis by at most half of what the others need;
    # past that it is clipped at the plot edge and says so.
    spread = max(high - low, 0.0001)
    allowed_high, allowed_low = high + spread * 0.5, low - spread * 0.5
    loose = [actual_of(m) for m in measures if not m.year_to_date]
    high = max(high, max((v for v in loose if v <= allowed_high), default=high))
    low = min(low, min((v for v in loose if v >= allowed_low), default=low))

    # Padded so the value labels at the ends of the longest bars still have room.
    span = 1 if high - low <= 0 else high - low
    high += span * 0.08
    low -= span * 0.08
    span = high - low

    def x_of(v: float) -> float:
        return PADDING_LEFT + (v - low) / span * plot_width

    plot_right = PADDING_LEFT + plot_width

    def clamp_x(v: float) -> float:
        return min(max(x_of(v), PADDING_LEFT), plot_right)

    zero_x = x_of(0)

    # Series appear in the order of the first row, and each keeps its colour.
    order = list(dict.fromkeys(m.series for m in rows[0].measures))

    def series_of(name: str) -> SeriesColors:
        index = order.index(name) if name in order else 0
        return colors.series[index % len(colors.series)]

    def fill_of(m: Measure) -> str:
        shades = series_of(m.series)
        return shades.pale if m.year_to_date else shades.fill

    if value_display:
        in_unit = f", {words.in_unit} {unit}" if unit else ""
        implies = rules.fill(words.outline_implies, labels.reference)
        subtitle = f"{words.filled_bar}: {labels.current}{in_unit}. {words.outline}: {implies}."
    else:
        subtitle = (
            f"{words.filled_bar}: {labels.change} {words.against} {labels.previous}. "
            f"{words.outline}: {labels.reference}."
        )
    canvas.heading(chart, subtitle, subtitle_baseline=43)

    # One swatch per measure, in the order of the bars in a band, then the reference outline.
    legend_x = 20.0
    for m in rows[0].measures:
        canvas.rect(legend_x, LEGEND_Y - 9, 10, 10, fill_of(m), series_of(m.series).stroke, 1)
        canvas.text(legend_x + 14, LEGEND_Y, m.label, 10, colors.text)
        legend_x += 24 + rules.text_width(m.label, 10)
    canvas.rect(legend_x, LEGEND_Y - 9, 10, 10, None, colors.reference, 1.5)
    canvas.text(legend_x + 14, LEGEND_Y, labels.reference, 10, colors.text)

    for r, row in enumerate(rows):
        band_top = PADDING_TOP + r * band_height
        if r % 2 == 1:
            canvas.rect(14, band_top, width - 28, band_height, colors.band, None, 0)

        # Aggregate rows bold and flush left; the others right-aligned, which reads as an indent.
        label_x = 14 if row.aggregate else PADDING_LEFT - 10
        anchor = TextAnchor.START if row.aggregate else TextAnchor.END
        lines = rules.wrap(row.label, 16)
        first = band_top + band_height / 2 - len(lines) * 6.0 + 4
        for n, text in enumerate(lines):
            canvas.text(label_x, first + n * 12, text, 11, colors.text, anchor, row.aggregate)

        # The exact references under the label: one figure per series, in its colour.
        references: list[DrawingSpan] = [DrawingSpan(labels.reference + ": ")]
        for i, name in enumerate(order):
            m = next(
                (m for m in row.measures if m.series == name and m.year_to_date),
                next(m for m in row.measures if m.series == name),
            )
            if i > 0:
                references.append(DrawingSpan(" · "))
            references.append(
                DrawingSpan(canvas.percent(m.reference), color=series_of(m.series).stroke)
            )
        canvas.spans(label_x, first + len(lines) * 12, references, 9, colors.muted, anchor)

        for i, m in enumerate(row.measures):
            actual = actual_of(m)
            top = band_top + BAND_PADDING / 2 + i * (BAR_HEIGHT + BAR_GAP)
            actual_x = clamp_x(actual)
            clipped = abs(actual_x - x_of(actual)) > 0.5
            stroke = series_of(m.series).stroke
            text = format(actual)
            left, right = min(actual_x, zero_x), max(actual_x, zero_x)
            note = f" ({words.clipped})" if clipped else ""
            canvas.rect(
                left,
                top,
                max(right - left, 0.5),
                BAR_HEIGHT,
                fill_of(m),
                stroke,
                0.75,
                hover=DrawingHover(
                    f"{row.label} — {m.label}: {text}{note}", (left + right) / 2, top
                ),
            )

            # A clipped bar ends in an arrowhead pointing off the plot.
            if clipped:
                tip = actual_x + (6 if actual >= 0 else -6)
                canvas.polygon(
                    (
                        (actual_x, top + 0.5),
                        (tip, top + BAR_HEIGHT / 2),
                        (actual_x, top + BAR_HEIGHT - 0.5),
                    ),
                    stroke,
                    None,
                    0,
                )

            # The reference as an outline, only on the year-to-date bar; the label goes on
            # whichever bar reaches further.
            outer = actual_x
            if m.year_to_date:
                reference_x = x_of(reference_of(m))
                rl, rr = min(reference_x, zero_x), max(reference_x, zero_x)
                canvas.rect(
                    rl,
                    top,
                    max(rr - rl, 0.5),
                    BAR_HEIGHT,
                    None,
                    colors.reference,
                    1.5,
                    hover=DrawingHover(
                        f"{row.label} — {m.label} {labels.reference}: {format(reference_of(m))}",
                        (rl + rr) / 2,
                        top,
                    ),
                )
                outer = (
                    actual_x if abs(actual_x - zero_x) >= abs(reference_x - zero_x) else reference_x
                )

            # A clipped bar's label turns inward and states the real figure.
            positive = actual >= 0
            if clipped:
                label_at = actual_x + (-5 if positive else 5)
            else:
                label_at = outer + (5 if positive else -5)
            anchor = TextAnchor.END if clipped == positive else TextAnchor.START
            canvas.text(label_at, top + BAR_HEIGHT - 2, text, 9, colors.text, anchor)

    canvas.line(zero_x, PADDING_TOP, zero_x, PADDING_TOP + plot_height, colors.axis, 1)
    return canvas.finish(height)
