"""Risk matrices: the model of ``::: riskmatrix`` (E15-S02).

``::: riskmatrix`` holds one table: number, risk, probability (1–5), impact (1–5) and
optionally a measure, one row per risk. The 5 × 5 matrix colours a cell by the product of its
probability and impact: up to ``green`` green, up to ``yellow`` yellow-orange, above red
(``::: riskmatrix green=4 yellow=12`` are the defaults). ``read_risk_matrix`` reads it from the
tokens of the container; ``layout_syntax.check`` calls it first, so every generator rejects the
same mistakes with ``Line N: …``. Drawing it is ``drawing.riskmatrix``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from markdown_it.token import Token

from pta_documents.design.colors import StatusCategory
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.schedule import child_blocks, error_at, table_rows
from pta_documents.markdown.parser import container, line_of

SCALE: Final = 5
"""Probability and impact go from 1 to this."""
MAX_RISKS: Final = 15
MAX_NUMBER_LENGTH: Final = 3
"""A risk's number is drawn in a small circle: at most this many characters (``12``, ``R3``)."""
GREEN_KEY: Final = "green"
YELLOW_KEY: Final = "yellow"
DEFAULT_GREEN: Final = 4
DEFAULT_YELLOW: Final = 12


@dataclass(frozen=True)
class Thresholds:
    """Up to ``green`` a cell (probability × impact) is green, up to ``yellow`` yellow-orange,
    above red."""

    green: int = DEFAULT_GREEN
    yellow: int = DEFAULT_YELLOW

    def level(self, probability: int, impact: int) -> StatusCategory:
        """The signal of a cell: success (green), warning (yellow-orange) or danger (red)."""
        product = probability * impact
        if product <= self.green:
            return StatusCategory.SUCCESS
        if product <= self.yellow:
            return StatusCategory.WARNING
        return StatusCategory.DANGER


@dataclass(frozen=True)
class Risk:
    number: str
    """As written in the first column (``3``), drawn in the risk's circle."""
    name: str
    probability: int
    impact: int
    measure: str | None = None
    """The fifth column, if the table has one."""
    line: int | None = None


@dataclass(frozen=True)
class RiskMatrix:
    risks: tuple[Risk, ...]
    headings: tuple[str, ...]
    """The headings of the table: number, risk, probability, impact (the axes) and measure."""
    thresholds: Thresholds = Thresholds()

    @property
    def probability_heading(self) -> str:
        return self.headings[2]

    @property
    def impact_heading(self) -> str:
        return self.headings[3]

    @property
    def has_measures(self) -> bool:
        return len(self.headings) > 4

    def legend(self) -> tuple[tuple[str, ...], ...]:
        """The legend as rows of text, its headings first: number, risk and measure if any."""
        heads = (self.headings[0], self.headings[1]) + (
            (self.headings[4],) if self.has_measures else ()
        )
        rows = [
            (r.number, r.name) + ((r.measure or "",) if self.has_measures else ())
            for r in self.risks
        ]
        return (heads, *rows)

    def in_cell(self, probability: int, impact: int) -> tuple[Risk, ...]:
        return tuple(r for r in self.risks if (r.probability, r.impact) == (probability, impact))

    @property
    def alt(self) -> str:
        """The risks as one line, the alternative text of the drawing."""
        return "; ".join(
            f"{r.number} {r.name}: {self.probability_heading} {r.probability}, "
            f"{self.impact_heading} {r.impact}"
            for r in self.risks
        )


def thresholds_argument(arguments: str, format: DocumentFormat) -> Thresholds:
    """The thresholds ``::: riskmatrix green=4 yellow=12`` asks for (the defaults for what it
    leaves out); raises for any other argument or thresholds out of order."""
    values = {GREEN_KEY: DEFAULT_GREEN, YELLOW_KEY: DEFAULT_YELLOW}
    usage = (
        f"The container '::: riskmatrix' takes {GREEN_KEY}=… and {YELLOW_KEY}=…, whole numbers "
        f"from 1 to {SCALE * SCALE - 1} (such as '::: riskmatrix {GREEN_KEY}={DEFAULT_GREEN} "
        f"{YELLOW_KEY}={DEFAULT_YELLOW}'): a cell up to {GREEN_KEY} is green, up to "
        f"{YELLOW_KEY} yellow, above red"
    )
    seen: set[str] = set()
    for part in arguments.split():
        key, equals, value = part.partition("=")
        key = key.strip().lower()
        if (
            not equals
            or key not in values
            or key in seen
            or not (value.isascii() and value.isdigit())
            or not 1 <= int(value) < SCALE * SCALE
        ):
            raise DocumentConversionError(format, f"{usage}, not '{arguments}'.")
        seen.add(key)
        values[key] = int(value)
    if values[GREEN_KEY] >= values[YELLOW_KEY]:
        raise DocumentConversionError(
            format,
            f"{usage}; {GREEN_KEY}={values[GREEN_KEY]} is not below "
            f"{YELLOW_KEY}={values[YELLOW_KEY]}.",
        )
    return Thresholds(values[GREEN_KEY], values[YELLOW_KEY])


def read_risk_matrix(
    tokens: Sequence[Token], i: int, format: DocumentFormat, line_offset: int
) -> RiskMatrix:
    """The risk matrix of the ``::: riskmatrix`` at ``tokens[i]``: one table with the columns
    number, risk, probability, impact and optionally measure, 1 to 15 rows."""
    start_line = line_of(tokens[i], line_offset)
    try:
        thresholds = thresholds_argument(container(tokens[i])[1], format)
    except DocumentConversionError as error:
        raise error_at(format, start_line, error.reason) from None
    kids = child_blocks(tokens, i)
    if len(kids) != 1 or tokens[kids[0]].type != "table_open":
        raise error_at(
            format,
            start_line,
            "A '::: riskmatrix' holds one table with the columns Nr, Risiko, "
            "Wahrscheinlichkeit and Auswirkung (1 to 5), and optionally Maßnahme.",
        )
    table = table_rows(tokens, kids[0], line_offset)
    header, body = table[0], table[1:]
    columns = len(header[1])
    if columns not in (4, 5):
        raise error_at(
            format,
            header[0],
            "The table of a '::: riskmatrix' has 4 or 5 columns (Nr, Risiko, Wahrscheinlichkeit, "
            f"Auswirkung and optionally Maßnahme), not {columns}.",
        )
    if not 1 <= len(body) <= MAX_RISKS:
        raise error_at(
            format,
            start_line,
            f"A '::: riskmatrix' has 1 to {MAX_RISKS} risks, not {len(body)}; split it into "
            "two matrices, such as one per area.",
        )
    risks: list[Risk] = []
    seen: dict[str, str] = {}
    for line, cells in body:
        number, name = cells[0], cells[1]
        if not number:
            raise error_at(format, line, f"The risk '{name}' has no number in the first column.")
        if len(number) > MAX_NUMBER_LENGTH:
            raise error_at(
                format,
                line,
                f"The number of a risk is drawn in a small circle: {MAX_NUMBER_LENGTH} characters "
                f"at most, not '{number}'.",
            )
        if number in seen:
            raise error_at(
                format, line, f"The number {number} is the risk '{seen[number]}' already."
            )
        if not name:
            raise error_at(format, line, f"The risk {number} has no name.")
        seen[number] = name
        probability = _value(cells[2], header[1][2], number, line, format)
        impact = _value(cells[3], header[1][3], number, line, format)
        measure = (cells[4] or None) if columns == 5 else None
        risks.append(Risk(number, name, probability, impact, measure, line))
    return RiskMatrix(tuple(risks), tuple(header[1]), thresholds)


def _value(text: str, heading: str, number: str, line: int | None, format: DocumentFormat) -> int:
    if text.isascii() and text.isdigit() and 1 <= int(text) <= SCALE:
        return int(text)
    raise error_at(
        format,
        line,
        f"The {heading or 'value'} of risk {number} is a whole number from 1 to {SCALE}, "
        f"not '{text}'.",
    )
