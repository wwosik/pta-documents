"""Native PowerPoint charts from a ``ChartSpec``, placed in a chart placeholder (E04-S04).

The placement is E04-S04's: the chart fills its layout's chart placeholder, in the series
colours of the spec. The PTA chart style (gap width, axis fonts and lines, ``ChartWriter.cs``)
follows with E06-S01, which also provides the ``chart`` renderer.
"""

from __future__ import annotations

from typing import Any

from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION

from pta_documents.charts.spec import ChartKind, ChartSpec


def chart_type(spec: ChartSpec) -> Any:
    """The PowerPoint chart type: clustered or stacked columns, lines with markers (they never
    stack), overlapping or stacked areas."""
    match spec.kind:
        case ChartKind.BAR:
            return XL_CHART_TYPE.COLUMN_STACKED if spec.stacked else XL_CHART_TYPE.COLUMN_CLUSTERED
        case ChartKind.LINE:
            return XL_CHART_TYPE.LINE_MARKERS
        case ChartKind.AREA:
            return XL_CHART_TYPE.AREA_STACKED if spec.stacked else XL_CHART_TYPE.AREA


def chart_data(spec: ChartSpec) -> CategoryChartData:
    """The categories and series; an empty cell (None) stays a gap."""
    data = CategoryChartData()
    data.categories = list(spec.categories)
    for series in spec.series:
        data.add_series(series.name, series.values)
    return data


def insert_chart(placeholder: Any, spec: ChartSpec, show_title: bool) -> Any:
    """The chart in ``placeholder`` (a chart placeholder of the slide); its title in the chart
    only with ``show_title`` (the PTA chart layouts have a placeholder of their own for it)."""
    frame = placeholder.insert_chart(chart_type(spec), chart_data(spec))
    chart = frame.chart
    chart.has_title = bool(show_title and spec.title)
    if chart.has_title:
        chart.chart_title.text_frame.text = spec.title or ""
    chart.has_legend = len(spec.series) > 1
    if chart.has_legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
    for n, series in enumerate(chart.plots[0].series):
        color = RGBColor.from_string(spec.colors[n % len(spec.colors)])
        if spec.kind is ChartKind.LINE:
            series.format.line.color.rgb = color
            series.marker.format.fill.solid()
            series.marker.format.fill.fore_color.rgb = color
        else:
            series.format.fill.solid()
            series.format.fill.fore_color.rgb = color
    return frame
