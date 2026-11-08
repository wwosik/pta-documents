"""A native chart of the deck as the drawing of its data (``charts.drawing``), inline SVG.

PowerPoint draws the chart from its chart part; the HTML deck reads the same part back into a
``ChartSpec`` — kind, categories, series, title and unit — and draws it with the chart drawing
Word's and the PDF's fallbacks use, so the browser shows the same figures in the PTA style.
"""

from __future__ import annotations

from typing import Any, Final

from pptx.enum.chart import XL_CHART_TYPE

from pta_documents.charts.drawing import draw
from pta_documents.charts.spec import ChartKind, ChartSeries, ChartSpec
from pta_documents.design.variants import Language
from pta_documents.drawing.svg_output import to_svg

C: Final = "http://schemas.openxmlformats.org/drawingml/2006/chart"
_KINDS: Final = {
    XL_CHART_TYPE.COLUMN_CLUSTERED: (ChartKind.BAR, False),
    XL_CHART_TYPE.COLUMN_STACKED: (ChartKind.BAR, True),
    XL_CHART_TYPE.LINE_MARKERS: (ChartKind.LINE, False),
    XL_CHART_TYPE.LINE: (ChartKind.LINE, False),
    XL_CHART_TYPE.AREA: (ChartKind.AREA, False),
    XL_CHART_TYPE.AREA_STACKED: (ChartKind.AREA, True),
}


def spec_of(chart: Any) -> ChartSpec | None:
    """The ``ChartSpec`` of a python-pptx chart the generator wrote; None for other charts."""
    try:
        kind = _KINDS.get(chart.chart_type)
        if kind is None:
            return None
        plot = chart.plots[0]
        categories = tuple(str(c) for c in plot.categories)
        series = tuple(
            ChartSeries(
                str(s.name),
                tuple(float(v) if v is not None else None for v in s.values),
            )
            for s in plot.series
        )
        title = chart.chart_title.text_frame.text if chart.has_title else None
        axis = chart.value_axis
        unit = axis.axis_title.text_frame.text if axis.has_title else None
    except (AttributeError, IndexError, KeyError, ValueError):
        return None
    if not categories or not series:
        return None
    return ChartSpec(kind[0], categories, series, stacked=kind[1], title=title, unit=unit)


def chart_svg(part: Any, language: str) -> str | None:
    """The chart of the chart part ``part`` as SVG markup, scaled to its box by CSS."""
    chart = getattr(part, "chart", None)
    if chart is None:
        return None
    spec = spec_of(chart)
    if spec is None:
        return None
    lang = Language.EN if language.startswith("en") else Language.DE
    return to_svg(draw(spec, lang))
