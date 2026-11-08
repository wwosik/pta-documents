"""Native Office charts from a ``ChartSpec`` in the PTA chart style (E06-S01).

Both generators write charts with python-pptx (PowerPoint through ``insert_chart``, Word through
the same chart XML in a part of its own, ``generation/docx/chart.py``), so the chart type, the
data and the style come from here (``ChartWriter.cs`` of DocLibs): series in the colours of the
spec, a gap of 60 % between bar groups, no tick marks, the category axis line 0.5 pt mid grey,
light grey gridlines, no value axis line, the legend at the bottom from two series on, gaps
staying gaps (areas count them as zero).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Final

from lxml import etree
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import (
    XL_CHART_TYPE,
    XL_LEGEND_POSITION,
    XL_MARKER_STYLE,
    XL_TICK_LABEL_POSITION,
    XL_TICK_MARK,
)
from pptx.util import Pt

from pta_documents.charts.drawing import AREA_SHARE
from pta_documents.charts.spec import ChartKind, ChartSpec
from pta_documents.design import colors

C: Final = "http://schemas.openxmlformats.org/drawingml/2006/chart"
A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"

GAP_WIDTH = 60
"""The gap between bar groups, in percent of a bar's width."""
LINE_PT = 0.5
"""The axis line and gridlines, in points."""
SERIES_LINE_PT = 2.25
MARKER_SIZE = 6


@dataclass(frozen=True, slots=True)
class ChartStyle:
    """The text of a chart: font, size and colour (RGB hex from ``design.colors``)."""

    font: str
    size_pt: float
    text: str


def chart_type(spec: ChartSpec) -> Any:
    """The Office chart type: clustered or stacked columns, lines with markers (they never
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


def series_color(spec: ChartSpec, index: int) -> str:
    """The colour of series ``index``: the spec's colours in turn; overlapping areas lighter,
    as in the drawing, so that the areas behind show."""
    color = spec.colors[index % len(spec.colors)]
    if spec.kind is ChartKind.AREA and not spec.stacked:
        return colors.tint(color, AREA_SHARE)
    return color


def apply_style(
    chart: Any, spec: ChartSpec, style: ChartStyle, title: str | None, unit: str | None
) -> None:
    """The PTA style on ``chart`` (a python-pptx ``Chart``); ``title`` in the chart (None:
    none), ``unit`` as the title of the value axis (None: none)."""
    _plain_chart_area(chart._chartSpace)
    font = chart.font
    font.name = style.font
    font.size = Pt(style.size_pt)
    font.color.rgb = RGBColor.from_string(style.text)

    chart.has_title = bool(title)
    if title:
        chart.chart_title.text_frame.text = title
        chart.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
    chart.has_legend = len(spec.series) > 1
    if chart.has_legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False

    plot = chart.plots[0]
    plot.vary_by_categories = False
    if spec.kind is ChartKind.BAR:
        plot.gap_width = GAP_WIDTH
        if spec.stacked:
            plot.overlap = 100

    category_axis = chart.category_axis
    category_axis.major_tick_mark = XL_TICK_MARK.NONE
    category_axis.minor_tick_mark = XL_TICK_MARK.NONE
    category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    _line(category_axis.format.line, colors.GREY_MID)
    category_axis.has_major_gridlines = False

    value_axis = chart.value_axis
    value_axis.major_tick_mark = XL_TICK_MARK.NONE
    value_axis.minor_tick_mark = XL_TICK_MARK.NONE
    value_axis.has_major_gridlines = True
    _line(value_axis.major_gridlines.format.line, colors.GREY_LIGHT)
    value_axis.format.line.fill.background()
    if spec.kind is not ChartKind.LINE:
        # Bars and areas start at zero (or below), so that their heights compare honestly.
        values = [v for series in spec.series for v in series.values if v is not None]
        value_axis.minimum_scale = min(0, math.floor(min(values, default=0)))
    value_axis.has_title = bool(unit)
    if unit:
        frame = value_axis.axis_title.text_frame
        frame.text = unit
        body_pr = frame._txBody.bodyPr
        body_pr.set("rot", "0")
        body_pr.set("vert", "horz")

    for n, series in enumerate(plot.series):
        color = RGBColor.from_string(series_color(spec, n))
        if spec.kind is ChartKind.LINE:
            series.format.line.color.rgb = color
            series.format.line.width = Pt(SERIES_LINE_PT)
            series.smooth = False
            series.marker.style = XL_MARKER_STYLE.CIRCLE
            series.marker.size = MARKER_SIZE
            series.marker.format.fill.solid()
            series.marker.format.fill.fore_color.rgb = color
            series.marker.format.line.fill.background()
        else:
            series.format.fill.solid()
            series.format.fill.fore_color.rgb = color
            series.format.line.fill.background()
            if spec.kind is ChartKind.BAR:
                series.invert_if_negative = False


def _line(line: Any, color: str) -> None:
    line.width = Pt(LINE_PT)
    line.fill.solid()
    line.fill.fore_color.rgb = RGBColor.from_string(color)


def _plain_chart_area(chart_space: Any) -> None:
    """Square corners and neither fill nor border around the chart: it sits on the page or
    slide like a drawing."""
    if chart_space.find(_c("roundedCorners")) is None:
        rounded = etree.Element(_c("roundedCorners"))
        rounded.set("val", "0")
        date = chart_space.find(_c("date1904"))
        if date is not None:
            date.addnext(rounded)
        else:
            chart_space.insert(0, rounded)
    if chart_space.find(_c("spPr")) is None:
        sp_pr = etree.fromstring(
            f'<c:spPr xmlns:c="{C}" xmlns:a="{A}"><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>'
        )
        chart_space.find(_c("chart")).addnext(sp_pr)


def _c(name: str) -> str:
    return f"{{{C}}}{name}"
