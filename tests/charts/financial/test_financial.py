"""E06-S02: the six financial charts — snapshots, the rules they share, their edge cases (port of
DocLibs ``FinancialChartTests.cs`` without the brand and dark cases)."""

from __future__ import annotations

import itertools
import re
from dataclasses import replace
from pathlib import Path
from typing import Final

import pytest

from pta_documents.charts import financial
from pta_documents.charts.financial import (
    DevelopmentPanel,
    FinancialChart,
    FinancialChartOptions,
    GrowthFigures,
    ReferenceDisplay,
    SummaryCell,
    TrendMonth,
    TwoYearSeries,
)
from pta_documents.charts.financial import canvas as rules
from pta_documents.charts.financial.options import format_decimal
from pta_documents.design import colors
from pta_documents.design.chart_colors import FINANCIAL, SERIES
from pta_documents.drawing import (
    Drawing,
    DrawingHotspot,
    DrawingShape,
    DrawingText,
    ShapeKind,
    TextAnchor,
    estimate_width,
)
from tests.charts.financial import figures
from tests.expected import assert_matches_expected

SAMPLES: Final = Path(__file__).parent / "samples"
OPTIONS: Final = figures.OPTIONS


def charts() -> dict[str, FinancialChart]:
    return {
        "development": figures.development(),
        "development-growth": figures.development(DevelopmentPanel.GROWTH),
        "growth-by-row": figures.growth_by_row(),
        "actual-vs-reference": figures.actual_vs_reference(),
        "actual-vs-reference-value": figures.actual_vs_reference(ReferenceDisplay.VALUE),
        "growth-trend": figures.growth_trend(),
        "two-year": figures.two_year(),
        "summary-table": figures.summary(),
    }


NAMES: Final = tuple(charts())


def texts(drawing: Drawing) -> list[str]:
    return [item.text for item in drawing.items if isinstance(item, DrawingText)]


def shapes(drawing: Drawing) -> list[DrawingShape]:
    return [item for item in drawing.items if isinstance(item, DrawingShape)]


@pytest.mark.parametrize("name", NAMES)
def test_every_chart_matches_its_snapshot(name: str, review_dir: Path) -> None:
    svg = financial.to_svg(charts()[name], OPTIONS)
    (review_dir / "financial").mkdir(exist_ok=True)
    (review_dir / "financial" / f"{name}.svg").write_text(svg, encoding="utf-8")
    assert_matches_expected(SAMPLES / f"{name}.expected.svg", svg)


@pytest.mark.parametrize("name", NAMES)
def test_every_bar_point_and_line_has_hover_text_and_the_svg_has_no_script(name: str) -> None:
    drawing = financial.draw(charts()[name], OPTIONS)
    svg = financial.to_svg(charts()[name], OPTIONS)
    # Every filled bar (a rectangle with an outline) and every hotspot says what it is; legend
    # swatches are the small squares and need none.
    for shape in shapes(drawing):
        _, _, width, height = shape.path.bounds
        swatch = abs(width - height) < 0.01 and width <= 12.01
        if shape.kind is ShapeKind.RECTANGLE and shape.stroke is not None and height < 40:
            assert swatch or shape.hover is not None
    assert all(i.hover is not None for i in drawing.items if isinstance(i, DrawingHotspot))
    assert "<script" not in svg.lower()
    if name != "summary-table":
        assert '<g class="chart-hoverable">' in svg
        assert ".chart-hoverable:hover .chart-tooltip" in svg
    assert 'font-family="Segoe UI, Selawik, sans-serif"' in svg


@pytest.mark.parametrize("name", NAMES)
def test_every_colour_is_a_pta_colour_or_a_tint_of_one(name: str) -> None:
    svg = financial.to_svg(charts()[name], OPTIONS)
    pta = {*colors.ACCENTS, *colors.SIGNALS, colors.WHITE, colors.TEXT_WORD, colors.TEXT_SLIDES}
    tints = {
        colors.tint(c, share) for c in colors.ACCENTS for share in (0.08, 0.1, 0.18, 0.5, 0.65)
    }
    used = {c.upper() for c in re.findall(r"#([0-9A-Fa-f]{6})", svg)}
    assert used <= pta | tints


@pytest.mark.parametrize(
    ("low", "high", "step"),
    [
        (0, 0.0004, 0.02),  # six points of headroom: a rate panel keeps room for its end labels
        (-12, 140, 50),
        (3_000_000, 21_500_000, 5_000_000),
    ],
)
def test_the_axis_includes_zero_in_round_steps_padded_before_rounding(
    low: float, high: float, step: float
) -> None:
    scale = rules.axis(low, high)
    assert scale.min <= 0 and scale.max >= high
    assert scale.max > high, "a series ending on a round number gains a gridline above it"
    assert scale.step == pytest.approx(step)
    factor = scale.step / 10 ** int(f"{scale.step:e}".split("e")[1])
    assert round(factor, 6) in (1, 2, 2.5, 5)


def test_a_colour_means_a_series_a_bar_behind_its_reference_keeps_its_colour() -> None:
    drawing = financial.draw(figures.actual_vs_reference(), OPTIONS)
    bars = [s for s in shapes(drawing) if s.hover and "Aufträge (Monat)" in s.hover.text]
    assert len(bars) == 4  # ahead, behind, negative: all one fill
    assert {b.fill for b in bars} == {SERIES[0].fill}


def test_verdict_colours_go_on_figures_with_a_tolerance() -> None:
    chart = figures.growth_by_row()

    def colour(options: FinancialChartOptions, figure: str) -> str:
        drawing = financial.draw(chart, options)
        (text,) = [t for t in drawing.items if isinstance(t, DrawingText) and t.text == figure]
        return text.color

    assert colour(OPTIONS, "8,1 %") == FINANCIAL.ahead == colors.SIGNAL_GREEN
    assert colour(OPTIONS, "3,2 %") == FINANCIAL.behind == colors.SIGNAL_RED
    assert colour(OPTIONS, "4,9 %") == FINANCIAL.level  # 0.1 points under: level
    assert colour(replace(OPTIONS, tolerance=0.05), "8,1 %") == FINANCIAL.level
    assert all(s.fill != FINANCIAL.behind for s in shapes(financial.draw(chart, OPTIONS)))


def test_a_dash_means_projection() -> None:
    drawing = financial.draw(figures.development(), OPTIONS)
    dashed = [
        s
        for s in shapes(drawing)
        if s.kind is ShapeKind.RECTANGLE and s.dash is not None and s.hover is not None
    ]
    assert dashed
    assert all(s.hover is not None and "Prognose" in s.hover.text for s in dashed)
    plan = [s for s in shapes(drawing) if s.hover and "Plan" in s.hover.text]
    assert plan and all(s.dash is None for s in plan)


def test_numbers_follow_the_culture_scale_and_unit() -> None:
    german = texts(financial.draw(figures.development(), OPTIONS))
    english = texts(financial.draw(figures.development(), figures.ENGLISH))
    assert "Vorjahr 206,4 Mio." in german
    assert "Previous 206.4 m" in english
    assert any(t.startswith("Ist ggü. Vorjahr +6,4 % im Jul") for t in german)
    assert any(t.startswith("Current vs Previous +6.4% at Jul") for t in english)
    assert "Target (Previous +5.0%)" in english


def test_the_number_formats() -> None:
    assert format_decimal(1250.5, 1, False, german=True) == "1.250,5"
    assert format_decimal(1250.5, 1, False, german=False) == "1,250.5"
    assert format_decimal(5.0, 1, False, german=True) == "5"
    assert format_decimal(5.0, 1, True, german=True) == "5,0"
    assert format_decimal(-0.01, 1, True, german=True) == "0,0"
    assert format_decimal(0.25, 1, False, german=False) == "0.3"  # half away from zero
    canvas = rules.Canvas(OPTIONS)
    assert canvas.percent(0.052) == "5,2 %"
    assert canvas.signed_percent(0.05) == "+5,0 %"
    assert canvas.signed_points(-0.012) == "-1,2 Pp."
    english = rules.Canvas(figures.ENGLISH)
    assert (english.percent(0.052), english.signed_points(0.012)) == ("5.2%", "+1.2pp")


def test_end_labels_are_pushed_apart_and_stay_on_the_canvas() -> None:
    drawing = financial.draw(figures.development(), OPTIONS)
    ends = sorted(
        (
            t
            for t in drawing.items
            if isinstance(t, DrawingText)
            and t.x > drawing.width / 2
            and t.text.startswith(("Vorjahr ", "Plan ", "Prognose "))
        ),
        key=lambda t: t.baseline,
    )
    assert len(ends) == 3
    assert all(b.baseline - a.baseline >= 11 - 1e-9 for a, b in itertools.pairwise(ends))
    assert all(t.x + estimate_width(t.text, t.size) <= drawing.width for t in ends)


def test_without_a_projection_nothing_is_dashed_and_the_legend_has_no_entry() -> None:
    chart = figures.development()
    months = tuple(replace(m, projection=None, projection_cumulative=None) for m in chart.months)
    drawing = financial.draw(replace(chart, months=months, change_at_year_end=None), OPTIONS)
    assert all(s.dash != rules.PROJECTION_DASH for s in shapes(drawing))
    assert not any("Prognose" in t for t in texts(drawing))


def test_a_december_chart_has_no_boundary_rule() -> None:
    drawing = financial.draw(replace(figures.development(), last_actual=11), OPTIONS)
    assert not any(s.hover and s.hover.text.startswith("Ist-Werte bis") for s in shapes(drawing))


def test_all_values_negative_the_axis_runs_below_zero_and_tops_at_zero() -> None:
    months = tuple(TrendMonth(m, -0.02 - i * 0.01) for i, m in enumerate(figures.MONTHS))
    chart = replace(figures.growth_trend(), months=months, reference=-0.01)
    labels = texts(financial.draw(chart, OPTIONS))
    assert "0 %" in labels
    assert not any(t.startswith("+") for t in labels)


def test_a_bar_far_beyond_the_others_is_clipped_with_an_arrowhead() -> None:
    drawing = financial.draw(figures.actual_vs_reference(), OPTIONS)
    (clipped,) = [
        s for s in shapes(drawing) if s.hover and s.hover.text.endswith("240 % (abgeschnitten)")
    ]
    (label,) = [t for t in drawing.items if isinstance(t, DrawingText) and t.text == "240 %"]
    x, _, width, _ = clipped.path.bounds
    assert x + width <= drawing.width - 50
    assert label.anchor is TextAnchor.END  # turned inward
    arrowheads = [
        s for s in shapes(drawing) if len(s.path.segments) == 4 and s.fill == SERIES[1].stroke
    ]
    assert arrowheads  # three corners, closed


def test_an_empty_rest_column_is_left_out_and_a_small_one_states_its_value_alone() -> None:
    table = figures.summary()
    blocks = tuple(replace(b, cells=(*b.cells[:4], SummaryCell(0, 0, 0, 0))) for b in table.blocks)
    small = texts(financial.draw(table, OPTIONS))
    none = texts(financial.draw(replace(table, blocks=blocks), OPTIONS))
    assert "Sonstige" in small and "0,2" in small
    assert "Sonstige" not in none


def test_two_year_categories_are_coloured_by_height_six_at_most() -> None:
    chart = figures.two_year(6)
    hues = financial.category_colors(chart, OPTIONS)
    assert hues[0] == colors.ACCENTS[0]  # machines run highest
    assert hues[2] == colors.ACCENTS[1]  # then service contracts, listed third
    with pytest.raises(ValueError, match="at most 6 categories"):
        financial.draw(replace(chart, series=(*chart.series, chart.series[0])), OPTIONS)


def test_a_month_without_a_value_breaks_the_line_and_a_lone_value_is_a_dot() -> None:
    values = tuple(1_000_000.0 if i in (3, 10, 11) else None for i in range(24))
    chart = replace(figures.two_year(1), series=(TwoYearSeries("Allein", values),))
    found = [
        s
        for s in shapes(financial.draw(chart, OPTIONS))
        if colors.ACCENTS[0] in (s.stroke, s.fill) and s.path.bounds.y > 80  # not the legend
    ]
    assert len([s for s in found if s.kind is ShapeKind.ELLIPSE]) == 1  # month 3 alone
    lines = [s for s in found if s.kind is ShapeKind.PATH and len(s.path.segments) == 2]
    assert len(lines) == 1  # months 10-11


def test_a_label_near_an_edge_slides_back_inside_the_plot() -> None:
    chart = replace(figures.growth_by_row(), overall=GrowthFigures(0.124, 0.05))
    drawing = financial.draw(chart, OPTIONS)
    (label,) = [
        t
        for t in drawing.items
        if isinstance(t, DrawingText)
        and t.text.startswith("Gesamt Veränderung")
        and t.anchor is TextAnchor.MIDDLE
    ]
    assert (
        label.x + estimate_width(label.text, label.size) / 2 <= drawing.width - 8 - 12 - 76 + 0.01
    )


def test_the_chart_stands_on_a_white_surface_in_the_text_colour() -> None:
    drawing = financial.draw(figures.growth_trend(), OPTIONS)
    ground = drawing.items[0]
    assert isinstance(ground, DrawingShape) and ground.fill == colors.WHITE
    assert ground.path.bounds == (0, 0, drawing.width, drawing.height)
    title = next(t for t in drawing.items if isinstance(t, DrawingText))
    assert title.color == colors.TEXT_WORD and title.text == "Wachstum der Aufträge (Juli 2026)"


def test_mistakes_in_the_data_are_value_errors() -> None:
    with pytest.raises(ValueError, match="needs at least one month"):
        financial.draw(replace(figures.growth_trend(), months=()), OPTIONS)
    with pytest.raises(ValueError, match="last actual month is 12"):
        financial.draw(replace(figures.development(), last_actual=12), OPTIONS)
    with pytest.raises(ValueError, match="same measures"):
        chart = figures.actual_vs_reference()
        first = replace(chart.rows[0], measures=chart.rows[0].measures[:2])
        financial.draw(replace(chart, rows=(first, *chart.rows[1:])), OPTIONS)
    with pytest.raises(ValueError, match="has 4 cells for 5 columns"):
        table = figures.summary()
        block = replace(table.blocks[0], cells=table.blocks[0].cells[:4])
        financial.draw(replace(table, blocks=(block,)), OPTIONS)
    with pytest.raises(ValueError, match="not a culture"):
        FinancialChartOptions(culture="pl-PL")
