"""Charts from ``chart`` code blocks (E06-S01): data types, parser and drawing.

The renderer is ``pta_documents.charts.renderer.ChartRenderer`` (not imported here: it depends on
``generation.common.renderers``, which imports ``charts.spec``).
"""

from pta_documents.charts.drawing import ChartColors, Scale, draw, format_number, scale
from pta_documents.charts.parser import ChartBlockError, parse
from pta_documents.charts.spec import ChartKind, ChartSeries, ChartSpec

__all__ = [
    "ChartBlockError",
    "ChartColors",
    "ChartKind",
    "ChartSeries",
    "ChartSpec",
    "Scale",
    "draw",
    "format_number",
    "parse",
    "scale",
]
