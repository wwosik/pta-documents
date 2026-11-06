"""Helpers for writing Markdown text safely (port of DocLibs ``MarkdownText``)."""

from __future__ import annotations

import re
from collections.abc import Sequence


def _is_ascii_punctuation(c: str) -> bool:
    return "!" <= c <= "/" or ":" <= c <= "@" or "[" <= c <= "`" or "{" <= c <= "~"


def escape(text: str) -> str:
    """Escape only what would format: ``*``, `` ` ``, ``[``, ``~``, ``_`` at word edges, tags."""
    result: list[str] = []
    for index, current in enumerate(text):
        before = text[index - 1] if index > 0 else " "
        after = text[index + 1] if index + 1 < len(text) else " "
        if current == "\\":
            guard = index + 1 >= len(text) or _is_ascii_punctuation(after)
        elif current in "`*[~":
            guard = True
        elif current == "_":
            guard = not before.isalnum() or not after.isalnum()
        elif current == "<":
            guard = after.isalpha() or after in "/!?"
        else:
            guard = False
        if guard:
            result.append("\\")
        result.append(current)
    return "".join(result)


def escape_line_start(line: str) -> str:
    """Escape a line start that would begin a block: heading, quote, table, list, rule."""
    if not line:
        return line
    first = line[0]
    if first in "#>|":
        return "\\" + line
    if first in "-+=":
        marker = len(line) == 1 or line[1] == " "
        underline = first != "+" and all(c == first for c in line)
        return "\\" + line if marker or underline else line
    digits = 0
    while digits < len(line) and digits < 9 and line[digits].isascii() and line[digits].isdigit():
        digits += 1
    if (
        digits > 0
        and digits < len(line)
        and line[digits] in ".)"
        and (digits + 1 == len(line) or line[digits + 1] == " ")
    ):
        return line[:digits] + "\\" + line[digits:]
    return line


def code(content: str) -> str:
    """Inline code that survives backticks in ``content``."""
    if not content:
        return ""
    longest = run = 0
    for c in content:
        run = run + 1 if c == "`" else 0
        longest = max(longest, run)
    fence = "`" * (longest + 1)
    pad = " " if content.startswith("`") or content.endswith("`") else ""
    return fence + pad + content + pad + fence


def destination(url: str) -> str:
    """A link destination; wrapped in ``<>`` when it contains spaces, parentheses or ``<>``."""
    if not any(c in url for c in " ()<>"):
        return url
    return "<" + url.replace("<", "%3C").replace(">", "%3E") + ">"


def cell(markdown: str) -> str:
    return markdown.replace("|", "\\|")


def _table_cell(value: str) -> str:
    return (
        cell(value)
        .replace("\\\n", "<br>")
        .replace("  \n", "<br>")
        .replace("\r\n", "<br>")
        .replace("\n", "<br>")
        .replace("\t", " ")
        .strip()
    )


def table(rows: Sequence[Sequence[str]]) -> str:
    """A pipe table whose first row is the header, followed by a blank line."""
    columns = max((len(r) for r in rows), default=0)
    if columns == 0:
        return ""
    lines: list[str] = []
    for r, row in enumerate(rows):
        cells = [_table_cell(row[c]) if c < len(row) else "" for c in range(columns)]
        lines.append("|" + "".join(f" {c} |" for c in cells))
        if r == 0:
            lines.append("|" + " --- |" * columns)
    return "\n".join(lines) + "\n\n"


def compact(rows: Sequence[Sequence[str]]) -> list[list[str]]:
    """Drop empty rows and columns."""
    kept = [r for r in rows if any(c.strip() for c in r)]
    if not kept:
        return []
    columns = max(len(r) for r in kept)
    keep = [c for c in range(columns) if any(c < len(r) and r[c].strip() for r in kept)]
    return [[r[c] if c < len(r) else "" for c in keep] for r in kept]


_LINE_BREAKS = re.compile(r"\r\n?")


def normalize(markdown: str) -> str:
    """Trim line ends, collapse blank lines, end with exactly one newline (or nothing)."""
    lines: list[str] = []
    blank_run = 0
    for raw in _LINE_BREAKS.sub("\n", markdown).split("\n"):
        line = raw.rstrip()
        if not line:
            blank_run += 1
            if blank_run > 1:
                continue
        else:
            blank_run = 0
        lines.append(line)
    result = "\n".join(lines).strip("\n")
    return result + "\n" if result else ""
