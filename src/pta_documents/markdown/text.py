r"""Helpers for writing Markdown text safely (port of DocLibs ``MarkdownText``).

The public interface for callers that write Markdown themselves; the DOCX and PPTX converters
use the same helpers. Import the module, not its names, which are too general on their own:

>>> from pta_documents.markdown import text as md
>>> md.normalize("# " + md.escape("Price_list *2026*") + "\n\n\n" + md.table([["a"], ["1"]]))
'# Price_list \\*2026\\*\n\n| a |\n| --- |\n| 1 |\n'
"""

from __future__ import annotations

import re
from collections.abc import Sequence

__all__ = [
    "cell",
    "code",
    "compact",
    "destination",
    "escape",
    "escape_line_start",
    "normalize",
    "table",
]


def _is_ascii_punctuation(c: str) -> bool:
    return "!" <= c <= "/" or ":" <= c <= "@" or "[" <= c <= "`" or "{" <= c <= "~"


def escape(text: str) -> str:
    r"""Escape only what would format inside a line, so that plain text stays readable.

    Guarded: ``*``, the backtick, ``[`` and ``~`` always; ``_`` only at a word edge
    (``customfield_10682`` stays); ``\`` at the end or before ASCII punctuation (``C:\path``
    stays); ``<`` before a letter, ``/``, ``!`` or ``?`` (a tag, comment or autolink; ``a < b``
    stays).

    Not guarded: block markers at the start of a line (``escape_line_start``), ``|`` (``cell``,
    ``table``), entities such as ``&amp;`` and the PTA extensions ``==mark==`` and
    ``:icon-name:``.

    >>> print(escape("*not bold* in customfield_10682, C:\\path and <b> but a < b"))
    \*not bold\* in customfield_10682, C:\path and \<b> but a < b
    """
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
    r"""Escape a line start that would begin a block: heading, quote, table, list, rule.

    Guarded: ``#``, ``>`` and ``|`` always; ``-``, ``+`` and ``=`` as a list marker (alone or
    before a space); ``-`` and ``=`` also as a line of only that character (rule or setext
    underline; ``+++`` stays); one to nine digits before ``.`` or ``)`` and a space or the end
    (an ordered list; ten digits are no list marker). Everything after the start is untouched,
    so ``escape`` goes first.

    >>> print(escape_line_start("# no heading"), escape_line_start("2026. was a year"))
    \# no heading 2026\. was a year
    >>> escape_line_start("end-to-end")
    'end-to-end'
    """
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
    """Inline code that survives backticks in ``content``.

    The fence is one backtick longer than the longest run in ``content``; a space pads content
    that starts or ends with a backtick. Empty content gives ``""``.

    >>> print(code("a"), code("a`b"), code("`x"))
    `a` ``a`b`` `` `x ``
    """
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
    """A link destination; wrapped in ``<>`` when it contains spaces, parentheses or ``<>``.

    Inside the brackets ``<`` and ``>`` become ``%3C`` and ``%3E``; nothing else is encoded.

    >>> print(destination("images/a.png"), destination("images/a b (1).png"))
    images/a.png <images/a b (1).png>
    """
    if not any(c in url for c in " ()<>"):
        return url
    return "<" + url.replace("<", "%3C").replace(">", "%3E") + ">"


def cell(markdown: str) -> str:
    r"""Markdown for a table cell: only ``|`` is escaped.

    ``markdown`` is already Markdown (``escape`` it first if it is plain text); line breaks are
    left as they are, ``table`` turns them into ``<br>``.

    >>> print(cell("Pear | green"))
    Pear \| green
    """
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
    r"""A pipe table whose first row is the header, followed by a blank line.

    Cells are Markdown and go through ``cell``; a line break in a cell (``\n``, ``\r\n`` or a
    hard break ``\`` / two spaces before it) becomes ``<br>``, a tab a space, and the cell is
    trimmed. Short rows are filled with empty cells up to the longest row. No rows give ``""``.

    >>> print(table([["Item", "Price"], ["Pear | green", "0.90\nper kg"], ["Short"]]), end="")
    | Item | Price |
    | --- | --- |
    | Pear \| green | 0.90<br>per kg |
    | Short |  |
    <BLANKLINE>
    """
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
    """Drop empty rows and columns; a cell of only whitespace counts as empty.

    Short rows count as empty in the missing columns and are filled with ``""``.

    >>> compact([["a", "", "b"], ["", "", ""], ["c", " ", "d"]])
    [['a', 'b'], ['c', 'd']]
    """
    kept = [r for r in rows if any(c.strip() for c in r)]
    if not kept:
        return []
    columns = max(len(r) for r in kept)
    keep = [c for c in range(columns) if any(c < len(r) and r[c].strip() for r in kept)]
    return [[r[c] if c < len(r) else "" for c in keep] for r in kept]


_LINE_BREAKS = re.compile(r"\r\n?")


def normalize(markdown: str) -> str:
    r"""Trim line ends, collapse blank lines, end with exactly one newline (or nothing).

    Line ends become ``\n``; trailing whitespace goes, so a hard break written as two spaces is
    lost: write hard breaks as ``\`` at the end of the line. Leading and trailing blank lines
    go; text of only whitespace gives ``""``.

    >>> normalize("\r\n\na  \r\n\r\n\r\nb\\\nc\n\n")
    'a\n\nb\\\nc\n'
    """
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
