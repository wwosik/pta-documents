"""Made-up figures for the six financial charts (port of DocLibs ``FinancialSamples.cs``): a
year of orders in millions, actuals through July."""

from __future__ import annotations

import math
from typing import Final

from pta_documents.charts.financial import (
    ActualVsReferenceChart,
    DevelopmentChart,
    DevelopmentMonth,
    DevelopmentPanel,
    EstimateMark,
    FinancialChartLabels,
    FinancialChartOptions,
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

MONTHS: Final = ("Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez")

OPTIONS: Final = FinancialChartOptions(scale=1_000_000, unit="Mio.")
"""German, as the PTA writes: DocLibs draws its samples in ``pl-PL`` with English labels."""

ENGLISH: Final = FinancialChartOptions(
    culture="en",
    scale=1_000_000,
    unit="m",
    labels=FinancialChartLabels(reference="Target", projection="Forecast"),
)

PREVIOUS_YEAR: Final = (14.2, 15.1, 17.8, 16.4, 17.0, 18.3, 16.9, 13.5, 17.7, 18.9, 19.4, 21.2)
CURRENT_YEAR: Final = (15.0, 15.9, 18.1, 17.9, 18.2, 19.6, 18.4)
FORECAST: Final = (14.8, 15.6, 18.0, 17.5, 18.6, 19.1, 18.0, 14.6, 19.0, 20.1, 20.5, 22.4)
TARGET_RATE: Final = 0.05


def m(millions: float) -> float:
    return millions * 1_000_000


def development(
    panel: DevelopmentPanel = DevelopmentPanel.CUMULATIVE, last_actual: int = 6
) -> DevelopmentChart:
    months: list[DevelopmentMonth] = []
    previous = current = forecast = target = 0.0
    for i in range(12):
        previous += PREVIOUS_YEAR[i]
        forecast += FORECAST[i]
        target += PREVIOUS_YEAR[i] * (1 + TARGET_RATE)
        actual = CURRENT_YEAR[i] if i <= last_actual and i < len(CURRENT_YEAR) else None
        if actual is not None:
            current += actual
        growth = (current / previous) - 1 if actual is not None else (forecast / previous) - 1
        months.append(
            DevelopmentMonth(
                MONTHS[i],
                m(PREVIOUS_YEAR[i]),
                None if actual is None else m(actual),
                m(FORECAST[i]),
                m(previous),
                None if actual is None else m(current),
                m(forecast),
                m(PREVIOUS_YEAR[i] * (1 + TARGET_RATE)),
                m(target),
                growth,
            )
        )
    return DevelopmentChart(
        title="Aufträge",
        period="Juli 2026",
        months=tuple(months),
        last_actual=last_actual,
        projection_compared_from=5,
        reference_rate=TARGET_RATE,
        change_at_period=months[last_actual].growth or 0,
        change_at_year_end=months[-1].growth,
        estimates=(EstimateMark(9, "Schätzung", m(166.0)),),
        lower_panel=panel,
    )


def growth_by_row() -> GrowthByRowChart:
    return GrowthByRowChart(
        title="Wachstum der Aufträge je Region",
        period="Juli 2026",
        rows=(
            GrowthRow("Nord", 0.081, 0.05),
            GrowthRow("Süd und die Inseln", 0.032, 0.05, emphasised=True),
            GrowthRow("Ost", -0.021, 0.04),
            GrowthRow("West", 0.124, 0.06),
            GrowthRow("Mitte und Ballungsräume", 0.049, 0.05),
        ),
        overall=GrowthFigures(0.052, 0.05),
    )


def _row(
    label: str,
    aggregate: bool,
    month: float,
    ytd: float,
    target: float,
    sales_month: float,
    sales_ytd: float,
    sales_target: float,
) -> MeasureRow:
    return MeasureRow(
        label,
        (
            Measure("orders", "Aufträge (Monat)", False, m(18.4), month, target, m(18.0)),
            Measure("orders", "Aufträge (lfd. J.)", True, m(122.5), ytd, target, m(121.8)),
            Measure("sales", "Umsatz (Monat)", False, m(16.2), sales_month, sales_target, m(16.0)),
            Measure("sales", "Umsatz (lfd. J.)", True, m(109.2), sales_ytd, sales_target, m(110.4)),
        ),
        aggregate,
    )


def actual_vs_reference(
    display: ReferenceDisplay = ReferenceDisplay.GROWTH,
) -> ActualVsReferenceChart:
    return ActualVsReferenceChart(
        title="Aufträge und Umsatz gegen Plan",
        period="Juli 2026",
        display=display,
        rows=(
            _row("Alle Regionen", True, 0.031, 0.052, 0.05, 0.044, 0.061, 0.06),
            _row("Nord", False, 0.12, 0.081, 0.05, 0.09, 0.07, 0.06),
            _row("Süd und die Inseln", False, -0.04, 0.032, 0.05, 2.4, 0.05, 0.06),
            _row("Ost", False, -0.08, -0.021, 0.04, -0.02, -0.01, 0.05),
        ),
    )


def growth_trend() -> GrowthTrendChart:
    return GrowthTrendChart(
        title="Wachstum der Aufträge",
        period="Juli 2026",
        last_actual=6,
        reference=TARGET_RATE,
        months=tuple(TrendMonth(month.label, month.growth) for month in development().months),
    )


NAMES: Final = (
    "Maschinen",
    "Ersatzteile",
    "Wartungsverträge",
    "Software",
    "Schulung",
    "Vermietung",
)
BASES: Final = (42, 18, 25, 9, 4, 12)


def two_year(categories: int = 5) -> TwoYearChart:
    series = tuple(
        TwoYearSeries(
            NAMES[c],
            tuple(
                None
                if i >= 19
                else m(BASES[c] * (1 + 0.12 * math.sin((i + c) * 0.7)) * (1.06 if i >= 12 else 1))
                for i in range(24)
            ),
        )
        for c in range(categories)
    )
    return TwoYearChart(
        title="Umsatz je Produktlinie",
        period="Juli 2026",
        months=MONTHS + MONTHS,
        previous_year="2025",
        current_year="2026",
        series=series,
    )


def _cell(current: float, previous: float, reference: float) -> SummaryCell:
    return SummaryCell(m(current), m(previous), (current / previous) - 1, reference)


def _rate(
    margin: float, previous_margin: float, sales: float, previous_sales: float
) -> SummaryCell:
    rate, previous_rate = margin / sales, previous_margin / previous_sales
    return SummaryCell(
        m(margin),
        m(previous_margin),
        0 if previous_margin == 0 else (margin / previous_margin) - 1,
        0,
        rate=rate if sales > 0.5 else None,
        previous_rate=previous_rate if previous_sales > 0.5 else None,
        reference_rate=previous_rate + 0.01 if previous_sales > 0.5 else None,
    )


def summary() -> SummaryTable:
    return SummaryTable(
        title="Übersicht",
        period="Juli 2026",
        columns=(
            SummaryColumn("Gesamt", total=True),
            SummaryColumn("Maschinen"),
            SummaryColumn("Teile"),
            SummaryColumn("Service"),
            SummaryColumn("Sonstige", rest=True),
        ),
        blocks=(
            SummaryBlock(
                "Aufträge",
                0.05,
                (
                    _cell(118.3, 112.5, 0.05),
                    _cell(64.2, 60.1, 0.05),
                    _cell(30.5, 31.0, 0.04),
                    _cell(23.4, 21.2, 0.06),
                    _cell(0.2, 0.2, 0.05),
                ),
            ),
            SummaryBlock(
                "Umsatz",
                0.04,
                (
                    _cell(109.2, 104.8, 0.04),
                    _cell(58.0, 55.9, 0.04),
                    _cell(29.1, 28.4, 0.03),
                    _cell(22.0, 20.4, 0.05),
                    _cell(0.1, 0.1, 0.04),
                ),
            ),
            SummaryBlock(
                "Marge",
                0.01,
                (
                    _rate(46.6, 44.9, 109.2, 104.8),
                    _rate(25.1, 24.7, 58.0, 55.9),
                    _rate(12.4, 12.0, 29.1, 28.4),
                    _rate(9.1, 8.2, 22.0, 20.4),
                    _rate(0.0, 0.0, 0.1, 0.1),
                ),
                rate_of="Umsatz",
            ),
        ),
    )
