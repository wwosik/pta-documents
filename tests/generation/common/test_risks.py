"""E15-S02: the model of ``::: riskmatrix`` — risks, thresholds, legend, mistakes."""

from __future__ import annotations

from typing import Final

import pytest

from pta_documents.design.colors import StatusCategory
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import layout_syntax, risks
from pta_documents.markdown.parser import CONTAINER_OPEN, parse

DOCX: Final = DocumentFormat.DOCX
MATRIX: Final = """::: riskmatrix
| Nr | Risiko         | Wahrscheinlichkeit | Auswirkung | Maßnahme   |
| -- | -------------- | ------------------ | ---------- | ---------- |
| 1  | Ausfall        | 2                  | 4          | Vertretung |
| 2  | Daten          | 4                  | 4          | Prüfen     |
| R3 | Schnittstelle  | 4                  | 4          |            |
:::
"""


def read(markdown: str = MATRIX) -> risks.RiskMatrix:
    tokens = parse(markdown)
    first = next(n for n, t in enumerate(tokens) if t.type == CONTAINER_OPEN)
    return risks.read_risk_matrix(tokens, first, DOCX, 0)


def test_a_row_per_risk() -> None:
    matrix = read()
    assert [(r.number, r.probability, r.impact) for r in matrix.risks] == [
        ("1", 2, 4),
        ("2", 4, 4),
        ("R3", 4, 4),
    ]
    assert matrix.probability_heading == "Wahrscheinlichkeit"
    assert matrix.impact_heading == "Auswirkung"
    assert [r.number for r in matrix.in_cell(4, 4)] == ["2", "R3"]
    assert matrix.risks[2].measure is None


def test_the_legend_keeps_the_order_and_drops_the_axes() -> None:
    assert read().legend() == (
        ("Nr", "Risiko", "Maßnahme"),
        ("1", "Ausfall", "Vertretung"),
        ("2", "Daten", "Prüfen"),
        ("R3", "Schnittstelle", ""),
    )
    four = (
        "::: riskmatrix\n| Nr | Risiko | W | A |\n| - | - | - | - |\n| 1 | Ausfall | 2 | 4 |\n:::\n"
    )
    matrix = read(four)
    assert matrix.legend()[0] == ("Nr", "Risiko")


@pytest.mark.parametrize(
    ("probability", "impact", "level"),
    [
        (1, 1, StatusCategory.SUCCESS),
        (2, 2, StatusCategory.SUCCESS),
        (1, 4, StatusCategory.SUCCESS),
        (1, 5, StatusCategory.WARNING),
        (3, 4, StatusCategory.WARNING),
        (2, 5, StatusCategory.WARNING),
        (4, 4, StatusCategory.DANGER),
        (5, 5, StatusCategory.DANGER),
    ],
)
def test_the_default_thresholds(probability: int, impact: int, level: StatusCategory) -> None:
    assert risks.Thresholds().level(probability, impact) is level


def test_the_thresholds_can_be_set() -> None:
    matrix = read(MATRIX.replace("::: riskmatrix", "::: riskmatrix green=2 yellow=8"))
    assert matrix.thresholds == risks.Thresholds(2, 8)
    assert matrix.thresholds.level(1, 3) is StatusCategory.WARNING
    assert matrix.thresholds.level(3, 3) is StatusCategory.DANGER
    assert risks.thresholds_argument("yellow=15", DOCX) == risks.Thresholds(4, 15)


@pytest.mark.parametrize(
    ("markdown", "message"),
    [
        (
            MATRIX.replace("| 2                  | 4  ", "| 6                  | 4  "),
            "Line 4: The Wahrscheinlichkeit of risk 1 is a whole number from 1 to 5, not '6'",
        ),
        (
            MATRIX.replace("| 4          | Prüfen", "| hoch       | Prüfen"),
            "Line 5: The Auswirkung of risk 2",
        ),
        (
            MATRIX.replace("| 1  | Ausfall", "|    | Ausfall"),
            "Line 4: The risk 'Ausfall' has no number",
        ),
        (MATRIX.replace("| R3 |", "| 2  |"), "Line 6: The number 2 is the risk 'Daten' already."),
        (
            MATRIX.replace("| R3 |", "| R333 |"),
            "Line 6: The number of a risk is drawn in a small circle",
        ),
        (
            MATRIX.replace("| Ausfall        |", "|                |"),
            "Line 4: The risk 1 has no name.",
        ),
        (
            MATRIX.replace("::: riskmatrix", "::: riskmatrix green=12 yellow=4"),
            "Line 1: The container '::: riskmatrix' takes green=",
        ),
        (
            MATRIX.replace("::: riskmatrix", "::: riskmatrix rot=20"),
            "Line 1: The container '::: riskmatrix' takes",
        ),
        ("::: riskmatrix\nKein Text\n:::\n", "Line 1: A '::: riskmatrix' holds one table"),
        (
            "::: riskmatrix\n| Nr | Risiko | W |\n| - | - | - |\n| 1 | a | 2 |\n:::\n",
            "Line 2: The table of a '::: riskmatrix' has 4 or 5 columns",
        ),
        (
            "::: riskmatrix\n| Nr | R | W | A |\n| - | - | - | - |\n"
            + "".join(f"| {n} | r | 1 | 1 |\n" for n in range(16))
            + ":::\n",
            "Line 1: A '::: riskmatrix' has 1 to 15 risks, not 16",
        ),
    ],
)
def test_mistakes_name_their_line(markdown: str, message: str) -> None:
    with pytest.raises(DocumentConversionError) as error:
        layout_syntax.check(parse(markdown), DOCX)
    assert error.value.reason.startswith(message), error.value.reason
