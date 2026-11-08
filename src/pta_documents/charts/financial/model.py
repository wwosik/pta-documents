"""The six charts of a financial review, as data (port of DocLibs ``FinancialChart.cs``).

``DevelopmentChart``, ``GrowthByRowChart``, ``ActualVsReferenceChart``, ``GrowthTrendChart``,
``TwoYearChart`` and ``SummaryTable``. Figures are plain numbers; growth rates and shares are
fractions (``0.052`` is 5.2 %). The caller decides which months are actuals. Frozen dataclasses
holding tuples, so charts compare by content.
"""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final


@dataclass(frozen=True, slots=True, kw_only=True)
class FinancialChart:
    """What every financial chart has: a title, a period and a subtitle."""

    title: str = ""
    """The title, drawn bold at the top."""
    period: str | None = None
    """The period the chart is about, such as ``Juli 2026``; drawn after the title in
    brackets."""
    subtitle: str | None = None
    """The line under the title; None: the chart's own, empty: none."""


class DevelopmentPanel(StrEnum):
    """Which form the lower panel of a ``DevelopmentChart`` takes."""

    CUMULATIVE = "cumulative"
    """The year cumulated: the actuals as an area, previous year, reference and projection as
    lines."""
    GROWTH = "growth"
    """The cumulative growth rate against the previous year, with the flat reference rate."""


@dataclass(frozen=True, slots=True)
class DevelopmentMonth:
    """One month of a ``DevelopmentChart``: each figure for the month and cumulated to it."""

    label: str
    """The month as the axis names it, such as ``Jan``."""
    previous: float
    current: float | None
    """The current year's actual; None for a month without actuals."""
    projection: float | None
    previous_cumulative: float
    current_cumulative: float | None
    projection_cumulative: float | None
    reference: float
    """The previous year grown by the reference rate."""
    reference_cumulative: float
    growth: float | None = None
    """The cumulative growth rate (actual, then projected) that a growth panel draws."""


@dataclass(frozen=True, slots=True)
class EstimateMark:
    """An estimate: the month it lands on (an index), its label and its cumulative figure."""

    month: int
    label: str
    value: float


@dataclass(frozen=True, slots=True, kw_only=True)
class DevelopmentChart(FinancialChart):
    """A year month by month in two panels over the same month slots: per month above, cumulated
    or as a growth rate below. A dashed rule marks where the actuals end."""

    months: tuple[DevelopmentMonth, ...] = ()
    last_actual: int = 0
    """The index of the last month with actuals."""
    projection_compared_from: int | None = None
    """The first month whose actual bar also shows its projection, overlapping; None: none."""
    reference_rate: float = 0
    """The annual reference growth rate, named in the legend."""
    change_at_period: float = 0
    """The change against the previous year at the last actual month (subtitle)."""
    change_at_year_end: float | None = None
    """The projection's change against the previous year at year end (subtitle)."""
    estimates: tuple[EstimateMark, ...] = ()
    lower_panel: DevelopmentPanel = DevelopmentPanel.CUMULATIVE
    cumulative_line_width: float = 2
    hide_estimate_labels: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "months", tuple(self.months))
        object.__setattr__(self, "estimates", tuple(self.estimates))
        if self.cumulative_line_width <= 0:
            object.__setattr__(self, "cumulative_line_width", 2)


@dataclass(frozen=True, slots=True)
class GrowthRow:
    """One row of a ``GrowthByRowChart``."""

    label: str
    change: float
    reference: float
    emphasised: bool = False
    """The row to read: a stronger fill and a bold label."""


@dataclass(frozen=True, slots=True)
class GrowthFigures:
    """A change and the reference growth rate it is read against."""

    change: float
    reference: float


@dataclass(frozen=True, slots=True, kw_only=True)
class GrowthByRowChart(FinancialChart):
    """Growth per row as horizontal bars from zero: the change filled, the reference as an
    outline, two dashed lines for the overall figures and a table of the figures beside."""

    rows: tuple[GrowthRow, ...] = ()
    overall: GrowthFigures = GrowthFigures(0, 0)

    def __post_init__(self) -> None:
        object.__setattr__(self, "rows", tuple(self.rows))


class ReferenceDisplay(StrEnum):
    """Whether an ``ActualVsReferenceChart`` draws growth rates or values."""

    GROWTH = "growth"
    VALUE = "value"


@dataclass(frozen=True, slots=True)
class Measure:
    """One bar of a ``MeasureRow``."""

    series: str
    """The series it belongs to; measures of one series share a hue."""
    label: str
    year_to_date: bool
    """A year-to-date figure: drawn pale, with its reference as an outline."""
    current: float
    """The current figure (value display)."""
    change: float
    """The change against the previous year (growth display)."""
    reference: float
    """The reference growth rate (growth display)."""
    reference_value: float
    """The value the reference implies (value display)."""


@dataclass(frozen=True, slots=True)
class MeasureRow:
    """One row of an ``ActualVsReferenceChart``."""

    label: str
    measures: tuple[Measure, ...]
    aggregate: bool = False
    """The row adds up others: bold and flush left."""

    def __post_init__(self) -> None:
        object.__setattr__(self, "measures", tuple(self.measures))


@dataclass(frozen=True, slots=True, kw_only=True)
class ActualVsReferenceChart(FinancialChart):
    """Measures per row against their references: a band per row, a bar per measure, the
    reference as an outline over the year-to-date bars; a bar far beyond the others is clipped
    with an arrowhead."""

    rows: tuple[MeasureRow, ...] = ()
    display: ReferenceDisplay = ReferenceDisplay.GROWTH

    def __post_init__(self) -> None:
        object.__setattr__(self, "rows", tuple(self.rows))


@dataclass(frozen=True, slots=True)
class TrendMonth:
    """One month of a ``GrowthTrendChart``: the cumulative growth rate; None: none."""

    label: str
    change: float | None


@dataclass(frozen=True, slots=True, kw_only=True)
class GrowthTrendChart(FinancialChart):
    """One growth rate over the months: solid through the last actual, then dashed, against the
    flat reference rate."""

    months: tuple[TrendMonth, ...] = ()
    last_actual: int = 0
    reference: float = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "months", tuple(self.months))


@dataclass(frozen=True, slots=True)
class TwoYearSeries:
    """One category of a ``TwoYearChart``: one value per slot, None breaks the line."""

    label: str
    values: tuple[float | None, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", tuple(self.values))


@dataclass(frozen=True, slots=True, kw_only=True)
class TwoYearChart(FinancialChart):
    """Two years month by month, a line per category, a dashed rule at the year boundary; at
    most six categories, coloured by how high their lines run."""

    months: tuple[str, ...] = ()
    """The slot labels: the previous year's months, then the current year's."""
    previous_year: str = ""
    current_year: str = ""
    series: tuple[TwoYearSeries, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "months", tuple(self.months))
        object.__setattr__(self, "series", tuple(self.series))


@dataclass(frozen=True, slots=True)
class SummaryColumn:
    """One column of a ``SummaryTable``."""

    label: str
    total: bool = False
    """Totals the others: a darker header, a pale fill, bold figures and a gap after it."""
    rest: bool = False
    """Holds what no other column claimed: drawn only when it holds something."""


@dataclass(frozen=True, slots=True)
class SummaryCell:
    """One cell of a ``SummaryBlock``."""

    current: float
    previous: float
    change: float
    reference: float
    """The reference growth rate for this cell (amount blocks)."""
    _: KW_ONLY
    rate: float | None = None
    """The current share of the block's ``rate_of``; None: none."""
    previous_rate: float | None = None
    reference_rate: float | None = None


@dataclass(frozen=True, slots=True)
class SummaryBlock:
    """One metric's block: an amount block states the value, the change and its gap to the
    reference; a rate block (``rate_of`` set) the value, both shares and their distances."""

    metric: str
    reference: float
    cells: tuple[SummaryCell, ...]
    rate_of: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", tuple(self.cells))


@dataclass(frozen=True, slots=True, kw_only=True)
class SummaryTable(FinancialChart):
    """A table of figures per column in blocks of rows per metric; only the comparison rows are
    coloured, by verdict."""

    columns: tuple[SummaryColumn, ...] = ()
    blocks: tuple[SummaryBlock, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", tuple(self.columns))
        object.__setattr__(self, "blocks", tuple(self.blocks))


type AnyFinancialChart = (
    DevelopmentChart
    | GrowthByRowChart
    | ActualVsReferenceChart
    | GrowthTrendChart
    | TwoYearChart
    | SummaryTable
)

CHART_TYPES: Final = MappingProxyType[str, type[FinancialChart]](
    {
        "development": DevelopmentChart,
        "growth-by-row": GrowthByRowChart,
        "actual-vs-reference": ActualVsReferenceChart,
        "growth-trend": GrowthTrendChart,
        "two-year": TwoYearChart,
        "summary-table": SummaryTable,
    }
)
"""The ``type`` of each chart in a ``financial-chart`` block."""
