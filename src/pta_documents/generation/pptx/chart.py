"""Native PowerPoint charts from a ``ChartSpec``, placed in a chart placeholder (E04-S04, E06-S01).

The chart fills its layout's chart placeholder in the PTA chart style of
``generation/common/native_chart.py``: axis labels and legend 14 pt Segoe UI Light in the slide
text colour.
"""

from __future__ import annotations

from typing import Any, Final

from pta_documents.charts.spec import ChartSpec
from pta_documents.design import colors
from pta_documents.design import slides as design
from pta_documents.generation.common import native_chart
from pta_documents.generation.common.native_chart import chart_data, chart_type

STYLE: Final = native_chart.ChartStyle(design.BODY_FONT, 14, colors.TEXT_SLIDES)

__all__ = ["STYLE", "chart_data", "chart_type", "insert_chart"]


def insert_chart(placeholder: Any, spec: ChartSpec, show_title: bool) -> Any:
    """The chart in ``placeholder`` (a chart placeholder of the slide); its title (and unit) in
    the chart only with ``show_title`` — the PTA chart layouts have placeholders of their own
    for title, unit and source."""
    frame = placeholder.insert_chart(chart_type(spec), chart_data(spec))
    native_chart.apply_style(
        frame.chart,
        spec,
        STYLE,
        title=spec.title if show_title else None,
        unit=spec.unit if show_title else None,
    )
    return frame
