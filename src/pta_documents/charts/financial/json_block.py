"""Reads and writes ``financial-chart`` blocks (port of DocLibs ``FinancialChartJson.cs``).

A block is one JSON object: the chart's ``type`` (``CHART_TYPES``), its properties in camel case
as the dataclasses name them (``lastActual`` for ``last_actual``), and an optional ``options``
object (``culture``, ``scale``, ``unit``, ``labels``, ``tolerance``, ``restShare``, ``width``).
The keys stay English, because programs write these blocks. Unknown properties and wrong types
are errors naming the line, so a misspelt key is never silently ignored; comments (``//``,
``/* */``) and trailing commas are allowed, as in DocLibs.

The reader is a small JSON parser of its own: Python's ``json`` knows neither comments nor the
line of a value.
"""

from __future__ import annotations

import dataclasses
import math
import re
import types
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final, Union, get_args, get_origin, get_type_hints

from pta_documents.charts.financial.model import CHART_TYPES, FinancialChart
from pta_documents.charts.financial.options import (
    LABEL_NAMES,
    FinancialChartLabels,
    FinancialChartOptions,
    check_culture,
)

LANGUAGE: Final = "financial-chart"
OPTIONS: Final = "options"
OPTION_KEYS: Final = ("culture", "scale", "unit", "labels", "tolerance", "restShare", "width")


class FinancialChartError(ValueError):
    """A ``financial-chart`` block that cannot be drawn; the message starts with ``Line N: ``
    when the line is known."""


def error(line: int | None, reason: str) -> FinancialChartError:
    where = f"Line {line}: " if line else ""
    return FinancialChartError(f"{where}The financial-chart block cannot be drawn: {reason}")


# ---------------------------------------------------------------------- JSON with lines


@dataclass(frozen=True, slots=True)
class _Node:
    value: object
    """``str``, ``int``, ``float``, ``bool``, None, ``list[_Node]`` or ``dict[str, _Entry]``."""
    line: int
    """The line the value starts on, from 1."""


@dataclass(frozen=True, slots=True)
class _Entry:
    key_line: int
    node: _Node


class _JsonError(Exception):
    def __init__(self, line: int, reason: str) -> None:
        super().__init__(reason)
        self.line = line
        self.reason = reason


_NUMBER: Final = re.compile(r"-?(?:0|[1-9]\d*)(\.\d+)?([eE][+-]?\d+)?")
_ESCAPES: Final = {
    '"': '"',
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


class _Reader:
    def __init__(self, text: str) -> None:
        self.text = text
        self.at = 0

    def line(self, at: int | None = None) -> int:
        return self.text.count("\n", 0, self.at if at is None else at) + 1

    def fail(self, reason: str) -> _JsonError:
        return _JsonError(self.line(), reason)

    def skip(self) -> None:
        """Whitespace and comments."""
        text = self.text
        while self.at < len(text):
            c = text[self.at]
            if c in " \t\r\n﻿":
                self.at += 1
            elif text.startswith("//", self.at):
                end = text.find("\n", self.at)
                self.at = len(text) if end < 0 else end
            elif text.startswith("/*", self.at):
                end = text.find("*/", self.at + 2)
                if end < 0:
                    raise self.fail("a comment '/*' is not closed with '*/'")
                self.at = end + 2
            else:
                return

    def document(self) -> _Node:
        self.skip()
        node = self.value()
        self.skip()
        if self.at < len(self.text):
            raise self.fail(f"unexpected '{self.text[self.at]}' after the JSON value")
        return node

    def value(self) -> _Node:
        text = self.text
        if self.at >= len(text):
            raise self.fail("the JSON ends where a value is expected")
        line = self.line()
        c = text[self.at]
        if c == "{":
            return _Node(self.object(), line)
        if c == "[":
            return _Node(self.array(), line)
        if c == '"':
            return _Node(self.string(), line)
        for word, value in (("true", True), ("false", False), ("null", None)):
            if text.startswith(word, self.at):
                self.at += len(word)
                return _Node(value, line)
        match = _NUMBER.match(text, self.at)
        if match is None:
            raise self.fail(f"unexpected '{c}' where a value is expected")
        self.at = match.end()
        number: int | float = (
            float(match.group()) if match.group(1) or match.group(2) else int(match.group())
        )
        if isinstance(number, float) and not math.isfinite(number):
            raise self.fail(f"the number {match.group()} is too large")
        return _Node(number, line)

    def object(self) -> dict[str, _Entry]:
        self.at += 1
        entries: dict[str, _Entry] = {}
        while True:
            self.skip()
            if self.text.startswith("}", self.at):
                self.at += 1
                return entries
            if not self.text.startswith('"', self.at):
                raise self.fail("a property name in double quotes is expected")
            key_line = self.line()
            key = self.string()
            if key in entries:
                raise _JsonError(key_line, f"the property '{key}' appears twice")
            self.skip()
            if not self.text.startswith(":", self.at):
                raise self.fail(f"':' is expected after '{key}'")
            self.at += 1
            self.skip()
            entries[key] = _Entry(key_line, self.value())
            self.skip()
            if self.text.startswith(",", self.at):
                self.at += 1
            elif not self.text.startswith("}", self.at):
                raise self.fail("',' or '}' is expected")

    def array(self) -> list[_Node]:
        self.at += 1
        items: list[_Node] = []
        while True:
            self.skip()
            if self.text.startswith("]", self.at):
                self.at += 1
                return items
            items.append(self.value())
            self.skip()
            if self.text.startswith(",", self.at):
                self.at += 1
            elif not self.text.startswith("]", self.at):
                raise self.fail("',' or ']' is expected")

    def string(self) -> str:
        text = self.text
        self.at += 1
        parts: list[str] = []
        while True:
            if self.at >= len(text):
                raise self.fail("a string is not closed with '\"'")
            c = text[self.at]
            if c == '"':
                self.at += 1
                return "".join(parts)
            if c == "\n":
                raise self.fail("a string is not closed with '\"' on its line")
            if c == "\\":
                escape = text[self.at + 1 : self.at + 2]
                if escape == "u":
                    digits = text[self.at + 2 : self.at + 6]
                    if not re.fullmatch(r"[0-9A-Fa-f]{4}", digits):
                        raise self.fail("'\\u' needs four hex digits")
                    parts.append(chr(int(digits, 16)))
                    self.at += 6
                    continue
                if escape not in _ESCAPES:
                    raise self.fail(f"'\\{escape}' is not an escape of JSON")
                parts.append(_ESCAPES[escape])
                self.at += 2
                continue
            parts.append(c)
            self.at += 1


# ---------------------------------------------------------------------- schema


def camel(name: str) -> str:
    """``last_actual`` → ``lastActual``."""
    head, *rest = name.split("_")
    return head + "".join(part.capitalize() for part in rest)


def _describe(node: _Node) -> str:
    value = node.value
    if isinstance(value, dict):
        return "an object"
    if isinstance(value, list):
        return "a list"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f"the text '{value}'"
    return f"the number {value}"


class _Binder:
    """Turns JSON nodes into the dataclasses of ``model``, strictly."""

    def __init__(self, base_line: int | None) -> None:
        self.base_line = base_line

    def fail(self, line: int, reason: str) -> FinancialChartError:
        return error(None if self.base_line is None else self.base_line + line, reason)

    def bind(self, kind: Any, node: _Node, path: str) -> object:
        origin = get_origin(kind)
        if origin in (Union, types.UnionType):
            options = [k for k in get_args(kind) if k is not type(None)]
            if node.value is None:
                return None
            return self.bind(options[0], node, path)
        if origin is tuple:
            item = get_args(kind)[0]
            if not isinstance(node.value, list):
                raise self.fail(node.line, f"'{path}' must be a list, not {_describe(node)}.")
            items: list[_Node] = node.value
            return tuple(self.bind(item, child, f"{path}[{i}]") for i, child in enumerate(items))
        if kind is bool:
            if not isinstance(node.value, bool):
                raise self.fail(
                    node.line, f"'{path}' must be true or false, not {_describe(node)}."
                )
            return node.value
        if kind is int:
            if isinstance(node.value, bool) or not isinstance(node.value, int):
                raise self.fail(
                    node.line, f"'{path}' must be a whole number, not {_describe(node)}."
                )
            return node.value
        if kind is float:
            if isinstance(node.value, bool) or not isinstance(node.value, int | float):
                raise self.fail(node.line, f"'{path}' must be a number, not {_describe(node)}.")
            return float(node.value)
        if kind is str:
            if not isinstance(node.value, str):
                raise self.fail(node.line, f"'{path}' must be a text, not {_describe(node)}.")
            return node.value
        if isinstance(kind, type) and issubclass(kind, StrEnum):
            members: list[StrEnum] = list(kind)
            valid = ", ".join(m.value for m in members)
            if isinstance(node.value, str):
                for member in members:
                    if member.value == node.value.lower():
                        return member
            raise self.fail(node.line, f"'{path}' must be one of {valid}, not {_describe(node)}.")
        if isinstance(kind, type) and dataclasses.is_dataclass(kind):
            return self.record(kind, node, path)
        raise TypeError(f"no JSON binding for {kind!r}")

    def record(self, kind: type[Any], node: _Node, path: str, skip: tuple[str, ...] = ()) -> object:
        if not isinstance(node.value, dict):
            raise self.fail(node.line, f"'{path}' must be an object, not {_describe(node)}.")
        entries: dict[str, _Entry] = node.value
        hints = get_type_hints(kind)
        fields = [f for f in dataclasses.fields(kind) if f.init]
        by_key = {camel(f.name): f for f in fields}
        prefix = f"{path}." if path else ""
        for key, entry in entries.items():
            if key not in by_key and key not in skip:
                valid = ", ".join(by_key)
                raise self.fail(
                    entry.key_line, f"unknown property '{prefix}{key}'; valid there: {valid}."
                )
        values: dict[str, object] = {}
        for key, field in by_key.items():
            entry = entries.get(key)
            if entry is None:
                no_default = field.default is dataclasses.MISSING
                if no_default and field.default_factory is dataclasses.MISSING:
                    raise self.fail(node.line, f"'{prefix}{key}' is missing.")
                continue
            values[field.name] = self.bind(hints[field.name], entry.node, prefix + key)
        return kind(**values)


def parse(
    code: str, line: int | None = None, culture: str | None = None
) -> tuple[FinancialChart, FinancialChartOptions]:
    """The chart and options of a block; ``line`` is the line of the opening fence (the block's
    first line is the next), ``culture`` the default culture (the document language).

    Raises ``FinancialChartError`` (a ``ValueError``) naming the line of the mistake.
    """
    try:
        root = _Reader(code).document()
    except _JsonError as failure:
        where = None if line is None else line + failure.line
        raise error(where, f"the block is not valid JSON: {failure.reason}.") from None
    binder = _Binder(line)
    if not isinstance(root.value, dict):
        raise binder.fail(root.line, "the block is not a JSON object.")
    entries: dict[str, _Entry] = root.value
    valid_types = ", ".join(CHART_TYPES)
    type_entry = entries.get("type")
    if type_entry is None or not isinstance(type_entry.node.value, str):
        raise binder.fail(root.line, f'the block needs a "type": {valid_types}.')
    chart_type = type_entry.node.value
    kind = CHART_TYPES.get(chart_type)
    if kind is None:
        raise binder.fail(
            type_entry.key_line, f"'{chart_type}' is not a type; valid: {valid_types}."
        )
    chart = binder.record(kind, root, "", skip=("type", OPTIONS))
    assert isinstance(chart, FinancialChart)
    options = FinancialChartOptions(culture=culture or FinancialChartOptions().culture)
    settings = entries.get(OPTIONS)
    if settings is not None:
        options = _options(binder, settings, options)
    return chart, options


def _options(
    binder: _Binder, entry: _Entry, defaults: FinancialChartOptions
) -> FinancialChartOptions:
    node = entry.node
    if not isinstance(node.value, dict):
        raise binder.fail(node.line, f"'options' must be an object, not {_describe(node)}.")
    entries: dict[str, _Entry] = node.value
    for key, item in entries.items():
        if key not in OPTION_KEYS:
            raise binder.fail(
                item.key_line,
                f"unknown property 'options.{key}'; valid there: {', '.join(OPTION_KEYS)}.",
            )

    def number(key: str, default: float, positive: bool) -> float:
        item = entries.get(key)
        if item is None:
            return default
        value = binder.bind(float, item.node, f"options.{key}")
        assert isinstance(value, float)
        if value < 0 or (positive and value <= 0):
            bound = "greater than 0" if positive else "0 or more"
            raise binder.fail(item.node.line, f"'options.{key}' must be {bound}, not {value:g}.")
        return value

    def text(key: str, default: str) -> str:
        item = entries.get(key)
        if item is None:
            return default
        value = binder.bind(str, item.node, f"options.{key}")
        assert isinstance(value, str)
        return value

    culture = text("culture", defaults.culture)
    try:
        culture = check_culture(culture)
    except ValueError as failure:
        item = entries["culture"]
        raise binder.fail(item.node.line, str(failure)) from None
    labels: FinancialChartLabels | None = None
    labels_entry = entries.get("labels")
    if labels_entry is not None:
        labels = _labels(binder, labels_entry.node, FinancialChartLabels.for_culture(culture))
    return FinancialChartOptions(
        culture=culture,
        scale=number("scale", defaults.scale, positive=True),
        unit=text("unit", defaults.unit),
        labels=labels,
        tolerance=number("tolerance", defaults.tolerance, positive=False),
        rest_share=number("restShare", defaults.rest_share, positive=False),
        width=number("width", defaults.width, positive=True),
        colors=defaults.colors,
    )


def _labels(binder: _Binder, node: _Node, defaults: FinancialChartLabels) -> FinancialChartLabels:
    """The labels given, on top of those of the culture's language."""
    if not isinstance(node.value, dict):
        raise binder.fail(node.line, f"'options.labels' must be an object, not {_describe(node)}.")
    entries: dict[str, _Entry] = node.value
    given: dict[str, str] = {}
    for key, item in entries.items():
        if key not in LABEL_NAMES:
            raise binder.fail(
                item.key_line, f"unknown label '{key}'; valid labels: {', '.join(LABEL_NAMES)}."
            )
        value = binder.bind(str, item.node, f"options.labels.{key}")
        assert isinstance(value, str)
        given[key] = value
    return dataclasses.replace(defaults, **given)


# ---------------------------------------------------------------------- writing


def to_json(chart: FinancialChart, options: FinancialChartOptions | None = None) -> str:
    """``chart`` (and ``options``, colours aside) as the JSON of a ``financial-chart`` block,
    which ``parse`` reads back to the same chart."""
    import json

    names = {kind: name for name, kind in CHART_TYPES.items()}
    if type(chart) not in names:
        raise TypeError(f"{type(chart).__name__} is not a financial chart")
    data: dict[str, object] = {"type": names[type(chart)]}
    record = _plain(chart)
    assert isinstance(record, dict)
    data.update(record)
    if options is not None:
        settings: dict[str, object] = {
            "culture": options.culture,
            "scale": options.scale,
            "unit": options.unit,
            "tolerance": options.tolerance,
            "restShare": options.rest_share,
            "width": options.width,
        }
        if options.labels is not None:
            settings["labels"] = _plain(options.labels)
        data[OPTIONS] = settings
    return json.dumps(data, ensure_ascii=False, indent=2)


def _plain(value: object) -> object:
    if isinstance(value, StrEnum):
        return value.value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            camel(f.name): _plain(getattr(value, f.name))
            for f in dataclasses.fields(value)
            if f.init
        }
    if isinstance(value, tuple):
        items: tuple[object, ...] = value
        return [_plain(item) for item in items]
    return value
