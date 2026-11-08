"""How the financial charts are drawn: culture, scale, unit, labels, tolerances and colours.

Port of DocLibs ``FinancialChartOptions.cs``. Numbers are formatted here without a
``CultureInfo``: German (``de``, ``de-DE``; the default) writes ``5,2 %`` and ``1.250,5``,
English (``en``, ``en-US``, ``en-GB``) ``5.2%`` and ``1,250.5``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Final

from pta_documents.design.chart_colors import FINANCIAL, FinancialChartColors

CULTURES: Final = ("de", "de-DE", "en", "en-US", "en-GB")
"""The cultures a financial chart writes numbers in; the case does not matter."""
DEFAULT_CULTURE: Final = "de-DE"


def is_german(culture: str) -> bool:
    return culture.lower().split("-")[0] == "de"


def check_culture(culture: str) -> str:
    """``culture`` as ``CULTURES`` spells it; ``ValueError`` naming the valid ones otherwise."""
    for known in CULTURES:
        if known.lower() == culture.strip().lower():
            return known
    raise ValueError(
        f"'{culture}' is not a culture of the financial charts; valid: {', '.join(CULTURES)}."
    )


@dataclass(frozen=True, slots=True)
class FinancialChartLabels:
    """The words the charts print for their series; set them to the reader's terms."""

    previous: str = "Previous"
    current: str = "Current"
    reference: str = "Reference"
    projection: str = "Projection"
    estimate: str = "Estimate"
    change: str = "Change"
    overall: str = "Overall"
    value: str = "Value"

    @staticmethod
    def for_culture(culture: str) -> FinancialChartLabels:
        """German labels for ``de*``, else English."""
        return GERMAN_LABELS if is_german(culture) else ENGLISH_LABELS


ENGLISH_LABELS: Final = FinancialChartLabels()
GERMAN_LABELS: Final = FinancialChartLabels(
    previous="Vorjahr",
    current="Ist",
    reference="Plan",
    projection="Prognose",
    estimate="Schätzung",
    change="Veränderung",
    overall="Gesamt",
    value="Wert",
)
LABEL_NAMES: Final = (
    "previous",
    "current",
    "reference",
    "projection",
    "estimate",
    "change",
    "overall",
    "value",
)


@dataclass(frozen=True, slots=True)
class FinancialChartWords:
    """The fixed wording of the charts; ``{0}``, ``{1}`` are filled with ``str.format``."""

    versus: str
    at: str
    per_month: str
    cumulative: str
    cumulative_growth: str
    actuals_end: str
    filled_bar: str
    outline: str
    outline_implies: str
    in_unit: str
    against: str
    clipped: str
    month_by_month: str
    growth_trend: str
    year_to_date: str
    percent_of: str
    points: str
    """The unit of a distance between two shares, with its leading space if it has one."""

    @staticmethod
    def for_culture(culture: str) -> FinancialChartWords:
        return GERMAN_WORDS if is_german(culture) else ENGLISH_WORDS


ENGLISH_WORDS: Final = FinancialChartWords(
    "vs",
    "at",
    "Per month",
    "Cumulative",
    "Cumulative growth {0} vs {1}",
    "Actuals end after {0}",
    "Filled bar",
    "Outline",
    "what {0} implies",
    "in",
    "against",
    "clipped",
    "Month by month, {0} and {1}.",
    "Cumulative growth against {0} by month, against {1}.",
    "Year to date: change against {0}, and how far it is from {1}.",
    "{0} % of {1}",
    "pp",
)
GERMAN_WORDS: Final = FinancialChartWords(
    "ggü.",
    "im",
    "Pro Monat",
    "Kumuliert",
    "Kumuliertes Wachstum {0} ggü. {1}",
    "Ist-Werte bis {0}",
    "Gefüllter Balken",
    "Umriss",
    "was {0} ergibt",
    "in",
    "ggü.",
    "abgeschnitten",
    "Monat für Monat, {0} und {1}.",
    "Kumuliertes Wachstum ggü. {0} je Monat, gegen {1}.",
    "Seit Jahresbeginn: Veränderung ggü. {0} und Abstand zu {1}.",
    "{0} % von {1}",
    " Pp.",
)


@dataclass(frozen=True, slots=True)
class FinancialChartOptions:
    """How ``draw`` draws a chart."""

    culture: str = DEFAULT_CULTURE
    """The culture of numbers, captions and default labels: one of ``CULTURES``."""
    scale: float = 1
    """What values are divided by before they are written, such as 1 000 000 for millions."""
    unit: str = ""
    """The unit written after values, such as ``Mio. EUR``."""
    labels: FinancialChartLabels | None = None
    """The words for the series; None: those of the culture's language."""
    tolerance: float = 0.005
    """How far a figure may be from what it is measured against and still count as level, as
    a fraction (0.005: half a percentage point)."""
    rest_share: float = 0.005
    """The share of the total column below which a summary table's rest column states its
    value but no comparisons."""
    width: float = 560
    """The width of the charts in pixels (the summary table sizes itself)."""
    colors: FinancialChartColors = field(default=FINANCIAL)

    def __post_init__(self) -> None:
        object.__setattr__(self, "culture", check_culture(self.culture))

    @property
    def effective_labels(self) -> FinancialChartLabels:
        return self.labels or FinancialChartLabels.for_culture(self.culture)

    @property
    def words(self) -> FinancialChartWords:
        return FinancialChartWords.for_culture(self.culture)

    @property
    def german(self) -> bool:
        return is_german(self.culture)


def format_decimal(value: float, decimals: int, always: bool, german: bool) -> str:
    """``value`` rounded half away from zero to ``decimals``, thousands grouped; with
    ``always`` every decimal is written (``0.0``), else trailing zeros go (``0.#``). Never
    ``-0``."""
    quantum = Decimal(1).scaleb(-decimals)
    rounded = Decimal(repr(value)).quantize(quantum, rounding=ROUND_HALF_UP)
    if rounded == 0:
        rounded = abs(rounded)
    text = f"{rounded:,.{decimals}f}"
    if not always and "." in text:
        text = text.rstrip("0").rstrip(".")
    if text == "-0":
        text = "0"
    if german:
        text = text.translate(str.maketrans({",": ".", ".": ","}))
    return text
