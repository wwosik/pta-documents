"""Reads a ``chart`` code block (port of DocLibs ``ChartParser.cs``).

The block holds optional settings, one ``key: value`` per line (``type``, ``title``, ``unit``,
``source``, ``stacked``; a comment after `` #``), then a line ``---``, then the data as CSV: a
header row (the name of the category column, then one name per series) and a row per category.
Without settings, the block is the CSV alone. Cells are separated by ``,`` (numbers with a
decimal point, ``1250.5``) or by ``;`` (numbers with a decimal comma, ``1250,5``); the header
row decides. A cell in double quotes may hold the separator; an empty cell leaves a gap.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Final

from pta_documents.charts.spec import ChartKind, ChartSeries, ChartSpec

SETTINGS: Final = ("type", "title", "unit", "source", "stacked")
"""The settings of a block, in the order the authoring guide names them."""
SEPARATOR_LINE: Final = "---"

_NUMBER: Final = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")


class ChartBlockError(ValueError):
    """A mistake in a ``chart`` block; the message starts with ``Line N: `` where known."""


def parse(code: str, line: int | None = None) -> ChartSpec:
    """The chart ``code`` describes; ``line`` is the line of the opening fence (from 1), so
    that errors name the line of the mistake.

    Raises ``ChartBlockError`` when a setting or the data is malformed.
    """
    lines = code.replace("\r", "").split("\n")
    separator = next((n for n, text in enumerate(lines) if text.strip() == SEPARATOR_LINE), None)
    settings = lines[:separator] if separator is not None else []
    first_data = separator + 1 if separator is not None else 0

    def at(index: int | None) -> int | None:
        """The document line of the block's line ``index`` (0: the first line of the code)."""
        if line is None:
            return None
        return line + 1 + index if index is not None else line

    values = _settings(settings, at)
    kind = values.get("type", ChartKind.BAR)
    assert isinstance(kind, ChartKind)

    data = [(n, text) for n, text in enumerate(lines) if n >= first_data and text.strip()]
    if len(data) < 2:
        raise _error(
            at(None),
            "The data needs a header row and at least one row of values, as CSV below the line "
            "'---'.",
        )
    header_index, header_text = data[0]
    delimiter = ";" if ";" in _unquoted(header_text) else ","
    header = _cells(header_text, delimiter)
    if len(header) < 2:
        raise _error(
            at(header_index),
            "The header row names the category column and at least one series: "
            "'month, plan, actual'.",
        )
    categories: list[str] = []
    columns: list[list[float | None]] = [[] for _ in header[1:]]
    for row, (index, text) in enumerate(data[1:], start=2):
        cells = _cells(text, delimiter)
        if len(cells) > len(header):
            raise _error(
                at(index),
                f"Row {row} of the data has {len(cells)} values; the header names "
                f"{len(header)} columns.",
            )
        categories.append(cells[0])
        for n, column in enumerate(columns):
            cell = cells[n + 1] if n + 1 < len(cells) else ""
            column.append(_number(cell, delimiter, row, at(index)))
    stacked = values.get("stacked", False)
    assert isinstance(stacked, bool)
    return ChartSpec(
        kind,
        tuple(categories),
        tuple(
            ChartSeries(name, tuple(column))
            for name, column in zip(header[1:], columns, strict=True)
        ),
        # Lines never stack.
        stacked=stacked and kind is not ChartKind.LINE,
        title=_text(values.get("title")),
        unit=_text(values.get("unit")),
        source=_text(values.get("source")),
    )


def _settings(
    settings: list[str], at: Callable[[int | None], int | None]
) -> dict[str, ChartKind | bool | str]:
    values: dict[str, ChartKind | bool | str] = {}
    for index, raw in enumerate(settings):
        setting = _strip_comment(raw).strip()
        if not setting:
            continue
        key, colon, value = setting.partition(":")
        key, value = key.strip().lower(), value.strip()
        if not colon or not key:
            raise _error(
                at(index), f"'{setting}' is not a setting; write 'key: value' above the line '---'."
            )
        if key not in SETTINGS:
            raise _error(
                at(index), f"Unknown setting '{key}'. Valid settings: {', '.join(SETTINGS)}."
            )
        if key in values:
            raise _error(at(index), f"The setting '{key}' is given twice.")
        match key:
            case "type":
                try:
                    values[key] = ChartKind(value.lower())
                except ValueError:
                    raise _error(
                        at(index), f"The type '{value}' is not bar, line or area."
                    ) from None
            case "stacked":
                if value.lower() not in ("true", "false"):
                    raise _error(at(index), f"stacked is true or false, not '{value}'.")
                values[key] = value.lower() == "true"
            case _:
                values[key] = value
    return values


def _strip_comment(text: str) -> str:
    """A setting without its comment: `` # …``, or the whole line when it starts with ``#``."""
    if text.lstrip().startswith("#"):
        return ""
    hash_index = text.find(" #")
    return text[:hash_index] if hash_index >= 0 else text


def _unquoted(row: str) -> str:
    """``row`` without the parts in double quotes."""
    return re.sub(r'"[^"]*"?', "", row)


def _cells(row: str, delimiter: str) -> list[str]:
    """The cells of a CSV row, each trimmed; a cell in double quotes may hold the delimiter."""
    cells: list[str] = []
    cell: list[str] = []
    quoted = False
    for char in row:
        if char == '"':
            quoted = not quoted
        elif char == delimiter and not quoted:
            cells.append("".join(cell).strip())
            cell = []
        else:
            cell.append(char)
    cells.append("".join(cell).strip())
    return cells


def _number(cell: str, delimiter: str, row: int, line: int | None) -> float | None:
    if not cell:
        return None
    decimal = "," if delimiter == ";" else "."
    other = "." if decimal == "," else ","
    candidate = cell.replace(decimal, ".") if other not in cell else ""
    if _NUMBER.fullmatch(candidate):
        return float(candidate)
    point = "a decimal comma" if decimal == "," else "a decimal point"
    raise _error(
        line,
        f"'{cell}' in row {row} of the data is not a number; write numbers with {point} and no "
        "thousands separator.",
    )


def _text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _error(line: int | None, reason: str) -> ChartBlockError:
    where = f"Line {line}: " if line else ""
    return ChartBlockError(f"{where}The chart block cannot be drawn: {reason}")
