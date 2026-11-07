"""What a chart shows, independent of how a generator draws it (port of DocLibs ``ChartSpec``)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pta_documents.design import colors


class ChartKind(StrEnum):
    """The kinds of chart."""

    BAR = "bar"
    """Vertical bars, clustered or stacked."""
    LINE = "line"
    """Lines with markers."""
    AREA = "area"
    """Filled areas, overlapping or stacked."""


@dataclass(frozen=True, slots=True)
class ChartSeries:
    """One series: its name (the column header) and a value per category (None where empty)."""

    name: str
    values: tuple[float | None, ...]


@dataclass(frozen=True, slots=True)
class ChartSpec:
    """A bar, line or area chart: categories along the horizontal axis, one series per column."""

    kind: ChartKind
    categories: tuple[str, ...]
    series: tuple[ChartSeries, ...]
    stacked: bool = False
    """Bars or areas on top of each other rather than side by side or overlapping."""
    title: str | None = None
    unit: str | None = None
    """The unit of the values, shown with the value axis (``k``, ``%``, ``EUR``)."""
    colors: tuple[str, ...] = colors.ACCENTS
    """The series colours (RGB hex without ``#``), in order; they repeat for more series."""
