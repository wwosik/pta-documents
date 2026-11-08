"""Steps: the model of ``::: steps`` (E15-S02), a procedure drawn as a row of chevrons.

``::: steps`` holds a ``###`` heading per step, each with at most one paragraph below it (the
step's text); ``### Umsetzung {.current}`` marks the step the project is at. ``read_steps``
reads them from the tokens of the container; ``layout_syntax.check`` calls it first, so every
generator rejects the same mistakes with ``Line N: …``. Drawing them is ``drawing.steps``.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from markdown_it.token import Token

from pta_documents.errors import DocumentFormat
from pta_documents.generation.common.schedule import child_blocks, error_at, plain_text
from pta_documents.markdown.parser import line_of

MIN_STEPS: Final = 3
MAX_STEPS: Final = 6
CURRENT: Final = "current"
HEADING: Final = "h3"
_ATTRIBUTES: Final = re.compile(r"\s*\{\s*([^{}]*?)\s*\}\s*$")


@dataclass(frozen=True)
class Step:
    title: str
    text: str
    """The paragraph below the heading; empty without one."""
    current: bool = False
    """``{.current}`` at the end of the heading: the step the project is at."""
    line: int | None = None


@dataclass(frozen=True)
class Steps:
    steps: tuple[Step, ...]

    @property
    def current(self) -> int | None:
        """The index of the current step; None: no step is marked."""
        return next((n for n, step in enumerate(self.steps) if step.current), None)

    @property
    def alt(self) -> str:
        """The steps as one line, the alternative text of the drawing."""
        return "; ".join(
            f"{n}. {step.title}" + (f": {step.text}" if step.text else "")
            for n, step in enumerate(self.steps, start=1)
        )


def read_steps(tokens: Sequence[Token], i: int, format: DocumentFormat, line_offset: int) -> Steps:
    """The steps of the ``::: steps`` at ``tokens[i]``: 3 to 6 ``###`` headings, each with at
    most one paragraph below it, at most one of them ``{.current}``."""
    start_line = line_of(tokens[i], line_offset)
    shape = (
        "A '::: steps' holds a '### heading' per step, each with one paragraph below it at most: "
        "'### Analyse' and the next line 'Interviews und Ist-Aufnahme'."
    )
    steps: list[Step] = []
    for kid in child_blocks(tokens, i):
        token = tokens[kid]
        line = line_of(token, line_offset)
        if token.type == "heading_open" and token.tag == HEADING:
            steps.append(_heading(plain_text(tokens[kid + 1]).strip(), line, format))
        elif token.type == "paragraph_open" and steps and not steps[-1].text:
            text = plain_text(tokens[kid + 1]).strip()
            last = steps[-1]
            steps[-1] = Step(last.title, text, last.current, last.line)
        else:
            raise error_at(format, line if steps else start_line, shape)
    if len(steps) > MAX_STEPS:
        raise error_at(
            format,
            start_line,
            f"A '::: steps' has {MIN_STEPS} to {MAX_STEPS} steps, not {len(steps)}; put the "
            "procedure on two slides, each with its own '::: steps'.",
        )
    if len(steps) < MIN_STEPS:
        raise error_at(
            format,
            start_line,
            f"A '::: steps' has {MIN_STEPS} to {MAX_STEPS} steps, not {len(steps)}; write "
            "fewer steps as a list.",
        )
    current = [step for step in steps if step.current]
    if len(current) > 1:
        raise error_at(
            format,
            current[1].line,
            f"Only one step is {{.{CURRENT}}}: '{current[0].title}' already is.",
        )
    return Steps(tuple(steps))


def _heading(text: str, line: int | None, format: DocumentFormat) -> Step:
    current = False
    if match := _ATTRIBUTES.search(text):
        if match.group(1) != "." + CURRENT:
            raise error_at(
                format,
                line,
                f"Unknown attribute '{{{match.group(1)}}}' of a step. Valid: {{.{CURRENT}}}.",
            )
        current = True
        text = text[: match.start()].strip()
    if not text:
        raise error_at(format, line, "Every step of a '::: steps' has a title.")
    return Step(text, "", current, line)
