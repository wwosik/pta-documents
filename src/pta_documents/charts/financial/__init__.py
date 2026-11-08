"""The charts of a financial review (E06-S02), port of DocLibs ``DocumentGeneration.Charts``.

Development, growth by row, actual vs reference, growth trend, two years and a summary table —
from Python data (``model``) or a ``financial-chart`` block (``json_block``), drawn as a
``Drawing`` in the PTA colours (``design.chart_colors``): shapes in slides, an SVG with tooltips
that needs no script for web pages. The rules every chart follows: a colour means a series and
nothing else; verdict colours go on figures, never on bars; a dash means projection and only
projection; every value axis includes zero. Pure Python, part of the core.
"""

from __future__ import annotations

from pta_documents.charts.financial import (
    actual_vs_reference,
    development,
    growth_by_row,
    growth_trend,
    summary_table,
    two_year,
)
from pta_documents.charts.financial.canvas import Canvas
from pta_documents.charts.financial.json_block import FinancialChartError, parse, to_json
from pta_documents.charts.financial.model import (
    CHART_TYPES,
    ActualVsReferenceChart,
    AnyFinancialChart,
    DevelopmentChart,
    DevelopmentMonth,
    DevelopmentPanel,
    EstimateMark,
    FinancialChart,
    GrowthByRowChart,
    GrowthFigures,
    GrowthRow,
    GrowthTrendChart,
    Measure,
    MeasureRow,
    ReferenceDisplay,
    SummaryBlock,
    SummaryCell,
    SummaryColumn,
    SummaryTable,
    TrendMonth,
    TwoYearChart,
    TwoYearSeries,
)
from pta_documents.charts.financial.options import (
    CULTURES,
    ENGLISH_LABELS,
    GERMAN_LABELS,
    FinancialChartLabels,
    FinancialChartOptions,
)
from pta_documents.drawing.model import Drawing
from pta_documents.drawing.svg_output import SvgOptions
from pta_documents.drawing.svg_output import to_svg as drawing_to_svg


def draw(chart: FinancialChart, options: FinancialChartOptions | None = None) -> Drawing:
    """The chart as a drawing, ``options.width`` wide (a summary table sizes itself).

    Raises ``ValueError`` when the chart's data does not fit together, such as rows of
    different lengths.
    """
    canvas = Canvas(options or FinancialChartOptions())
    match chart:
        case DevelopmentChart():
            return development.draw(chart, canvas)
        case GrowthByRowChart():
            return growth_by_row.draw(chart, canvas)
        case ActualVsReferenceChart():
            return actual_vs_reference.draw(chart, canvas)
        case GrowthTrendChart():
            return growth_trend.draw(chart, canvas)
        case TwoYearChart():
            return two_year.draw(chart, canvas)
        case SummaryTable():
            return summary_table.draw(chart, canvas)
        case _:
            raise TypeError(f"{type(chart).__name__} is not a financial chart")


def to_svg(chart: FinancialChart, options: FinancialChartOptions | None = None) -> str:
    """The chart as a standalone SVG: a tooltip on every bar, point and line that needs no
    script, in ``Segoe UI, Selawik, sans-serif`` and the tooltip colours of the chart."""
    options = options or FinancialChartOptions()
    palette = options.colors
    svg = SvgOptions(tooltip_fill=palette.tooltip_fill, tooltip_text=palette.tooltip_text)
    return drawing_to_svg(draw(chart, options), svg)


def category_colors(
    chart: TwoYearChart, options: FinancialChartOptions | None = None
) -> tuple[str, ...]:
    """The colour each category of a two-year chart is drawn in, in the order of its series —
    for a legend or table elsewhere. Raises ``ValueError`` beyond six categories."""
    return two_year.colours(chart, (options or FinancialChartOptions()).colors)


__all__ = [
    "CHART_TYPES",
    "CULTURES",
    "ENGLISH_LABELS",
    "GERMAN_LABELS",
    "ActualVsReferenceChart",
    "AnyFinancialChart",
    "DevelopmentChart",
    "DevelopmentMonth",
    "DevelopmentPanel",
    "EstimateMark",
    "FinancialChart",
    "FinancialChartError",
    "FinancialChartLabels",
    "FinancialChartOptions",
    "GrowthByRowChart",
    "GrowthFigures",
    "GrowthRow",
    "GrowthTrendChart",
    "Measure",
    "MeasureRow",
    "ReferenceDisplay",
    "SummaryBlock",
    "SummaryCell",
    "SummaryColumn",
    "SummaryTable",
    "TrendMonth",
    "TwoYearChart",
    "TwoYearSeries",
    "category_colors",
    "draw",
    "parse",
    "to_json",
    "to_svg",
]
