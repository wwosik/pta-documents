"""Estimated text widths without font files (port of DocLibs ``TextMetrics``).

Widths are in EMU for a font size in points; the per-character factors approximate a sans
serif face like Segoe UI. They decide column widths and when slide text has to shrink.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

EMU_PER_POINT: Final = 12700
BOLD_FACTOR: Final = 1.08


@dataclass(frozen=True)
class TextRun:
    text: str = ""
    bold: bool = False
    is_break: bool = False
    """A line break between runs."""


BREAK: Final = TextRun(is_break=True)


def em(c: str) -> float:
    if c == " ":
        return 0.28
    if c in ".,:;'|!iljI()[]":
        return 0.3
    if c in "ftr":
        return 0.4
    if c in "mw":
        return 0.85
    if c in "MW%@":
        return 0.9
    if "0" <= c <= "9":
        return 0.6
    if "A" <= c <= "Z":
        return 0.68
    if "a" <= c <= "z":
        return 0.53
    if c.isupper():
        return 0.68
    if c.isalpha():
        return 0.55
    return 0.6


def width(text: str, size_pt: float, bold: bool = False) -> float:
    return sum(em(c) for c in text) * size_pt * EMU_PER_POINT * (BOLD_FACTOR if bold else 1.0)


def _words(runs: Sequence[TextRun], size_pt: float, bold: bool) -> list[list[float]]:
    """The widths of the words of each line; a word runs across runs until a space or break."""
    lines: list[list[float]] = [[]]
    word = 0.0

    def end_word() -> None:
        nonlocal word
        if word > 0:
            lines[-1].append(word)
            word = 0.0

    for run in runs:
        if run.is_break:
            end_word()
            lines.append([])
            continue
        factor = BOLD_FACTOR if (bold or run.bold) else 1.0
        for c in run.text:
            if c.isspace():
                end_word()
            else:
                word += em(c) * size_pt * EMU_PER_POINT * factor
    end_word()
    return lines


def longest_word(runs: Sequence[TextRun], size_pt: float, bold: bool = False) -> float:
    """The width of the longest word, which no line break can split."""
    return max((w for line in _words(runs, size_pt, bold) for w in line), default=0.0)


def lines(runs: Sequence[TextRun], size_pt: float, bold: bool, available: float) -> int:
    """How many lines the runs take in ``available`` EMU."""
    space = em(" ") * size_pt * EMU_PER_POINT
    count = 0
    for line in _words(runs, size_pt, bold):
        count += 1
        x = 0.0
        for word in line:
            needed = word if x == 0 else x + space + word
            if x > 0 and needed > available:
                count += 1
                x = word
            else:
                x = needed
            # A word wider than the line breaks inside, one more line per width it takes.
            while x > available > 0:
                count += 1
                x -= available
    return max(count, 1)


def segments(runs: Sequence[TextRun]) -> list[int]:
    """Character counts between line breaks."""
    result: list[int] = []
    length = 0
    for run in runs:
        if run.is_break:
            result.append(length)
            length = 0
        else:
            length += len(run.text)
    result.append(length)
    return result


def column_widths(
    cells: Sequence[Sequence[Sequence[TextRun]]],
    total: float,
    size_pt: float,
    insets: float,
    header: bool,
) -> list[int]:
    """Every column at least as wide as its longest word; the rest goes by longest text.

    ``cells`` are rows of cells of runs; the result sums to ``total``.
    """
    columns = max((len(r) for r in cells), default=0)
    if columns == 0:
        return []

    def cell(row: Sequence[Sequence[TextRun]], c: int) -> Sequence[TextRun]:
        return row[c] if c < len(row) else ()

    minimums = [
        max(longest_word(cell(row, c), size_pt, header and r == 0) for r, row in enumerate(cells))
        + insets
        for c in range(columns)
    ]
    spare = total - sum(minimums)
    if spare < 0:
        minimums = [m * total / sum(minimums) for m in minimums]
        spare = 0.0
    weights = [
        float(min(max(max(max(segments(cell(row, c)), default=0) for row in cells), 3), 60))
        for c in range(columns)
    ]
    widths = [int(minimums[c] + spare * weights[c] / sum(weights)) for c in range(columns)]
    widths[-1] = int(total) - sum(widths[:-1])
    return widths
