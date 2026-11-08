"""The colour roles of the financial charts (E06-S02), each mapped to a PTA colour.

Port of the chart roles of DocLibs ``ResolvedChartColors``. DocLibs derives them from a brand;
here every role names a value of ``design.colors`` — directly, or as a tint of one (decision
2026-11-07: shades between the PTA colours are computed with ``colors.tint``). There is no dark
variant: PTA content slides are light.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from pta_documents.design import colors


@dataclass(frozen=True, slots=True)
class SeriesColors:
    """The four shades of one series: from palest to the full colour."""

    fill: str
    """A filled bar (growth by row, the month bars of actual vs reference)."""
    pale: str
    """A projection bar or a year-to-date bar: the series, paler."""
    strong: str
    """An actual bar and the actual area of the cumulative panel."""
    stroke: str
    """Outlines, lines and the figures that name the series: the colour itself."""

    @staticmethod
    def of(color: str) -> SeriesColors:
        """The shades of ``color`` mixed with white, as DocLibs mixes them on a light ground."""
        return SeriesColors(
            colors.tint(color, 0.18), colors.tint(color, 0.08), colors.tint(color, 0.65), color
        )


SERIES: Final = (
    SeriesColors.of(colors.PTA_BLUE),
    SeriesColors.of(colors.DARK_BLUE),
    SeriesColors.of(colors.LIGHT_BLUE),
)
"""The series in order: the first is the current year, the second the previous one."""


@dataclass(frozen=True, slots=True)
class FinancialChartColors:
    """Every colour a financial chart draws with (RGB hex without ``#``)."""

    series: tuple[SeriesColors, ...] = SERIES
    categories: tuple[str, ...] = colors.ACCENTS
    """The lines of a two-year chart, handed out by how high each runs."""
    reference: str = colors.GREY_DARK
    """The reference (plan) as a line, an outline and its figures."""
    reference_fill: str = colors.GREY_LIGHT
    """The reference increment stacked on the previous year's bar."""
    axis: str = colors.GREY_MID
    """The zero line and the dividers of a summary table."""
    gridline: str = colors.GREY_LIGHT
    """Gridlines, table rules and the rule where the actuals end."""
    band: str = field(default_factory=lambda: colors.tint(colors.GREY_LIGHT, 0.5))
    """Behind every other row of an actual-vs-reference chart."""
    emphasis: str = field(default_factory=lambda: SERIES[0].strong)
    """The bar of the emphasised row of a growth-by-row chart: still the first series."""
    ahead: str = colors.SIGNAL_GREEN
    """A figure ahead of what it is measured against."""
    level: str = colors.GREY_DARK
    """A figure level with it, within the tolerance."""
    behind: str = colors.SIGNAL_RED
    """A figure behind it."""
    surface: str | None = colors.WHITE
    """The ground the chart is drawn on; None: transparent."""
    text: str = colors.TEXT_WORD
    muted: str = colors.GREY_DARK
    """Subtitles, axis captions and tick labels."""
    patch: str = colors.WHITE
    """What a label is written on where it crosses a line."""
    table_header: str = colors.PTA_BLUE
    total_header: str = colors.DARK_BLUE
    """The header of the total column of a summary table: darker than the others."""
    total_fill: str = field(default_factory=lambda: colors.tint(colors.PTA_BLUE, 0.10))
    """Behind the figures of the total column."""
    header_text: str = colors.WHITE
    tooltip_fill: str = colors.TEXT_SLIDES
    tooltip_text: str = colors.WHITE


FINANCIAL: Final = FinancialChartColors()
"""The colours of the financial charts in a Word document; slides take ``TEXT_SLIDES``."""
