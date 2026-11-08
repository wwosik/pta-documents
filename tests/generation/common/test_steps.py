"""E15-S02: the model of ``::: steps`` — steps, the current one, mistakes."""

from __future__ import annotations

from typing import Final

import pytest

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import layout_syntax, steps
from pta_documents.markdown.parser import CONTAINER_OPEN, parse

DOCX: Final = DocumentFormat.DOCX
STEPS: Final = """::: steps
### Analyse
Interviews und Ist-Aufnahme
### Konzept
### Umsetzung {.current}
In Sprints
### Abnahme
:::
"""


def read(markdown: str = STEPS) -> steps.Steps:
    tokens = parse(markdown)
    first = next(n for n, t in enumerate(tokens) if t.type == CONTAINER_OPEN)
    return steps.read_steps(tokens, first, DOCX, 0)


def test_a_heading_per_step_with_its_text() -> None:
    read_steps = read()
    assert [s.title for s in read_steps.steps] == ["Analyse", "Konzept", "Umsetzung", "Abnahme"]
    assert [s.text for s in read_steps.steps] == [
        "Interviews und Ist-Aufnahme",
        "",
        "In Sprints",
        "",
    ]
    assert read_steps.current == 2
    assert [s.line for s in read_steps.steps] == [2, 4, 5, 7]
    assert read_steps.alt.startswith("1. Analyse: Interviews und Ist-Aufnahme; 2. Konzept; ")


def test_without_current_no_step_is_current() -> None:
    assert read(STEPS.replace(" {.current}", "")).current is None


def many(count: int) -> str:
    return "::: steps\n" + "".join(f"### Schritt {n}\n" for n in range(count)) + ":::\n"


@pytest.mark.parametrize(
    ("markdown", "message"),
    [
        (many(7), "Line 1: A '::: steps' has 3 to 6 steps, not 7; put the procedure on two"),
        (many(2), "Line 1: A '::: steps' has 3 to 6 steps, not 2"),
        (STEPS.replace("### Konzept", "### Konzept {.current}"), "Line 5: Only one step is"),
        (STEPS.replace("{.current}", "{.done}"), "Line 5: Unknown attribute '{.done}' of a step"),
        ("::: steps\nText davor\n\n### A\n### B\n### C\n:::\n", "Line 1: A '::: steps' holds"),
        ("::: steps\n### A\nEins\n\nZwei\n### B\n### C\n:::\n", "Line 5: A '::: steps' holds"),
        ("::: steps\n## A\n### B\n### C\n:::\n", "Line 1: A '::: steps' holds a '### heading'"),
        ("::: steps\n### {.current}\n### B\n### C\n:::\n", "Line 2: Every step"),
    ],
)
def test_mistakes_name_their_line(markdown: str, message: str) -> None:
    with pytest.raises(DocumentConversionError) as error:
        layout_syntax.check(parse(markdown), DOCX)
    assert error.value.reason.startswith(message), error.value.reason
