"""``[words]{.success}`` in running text: the words in the colour of a status category.

Port of DocLibs ``ColouredWords``. Found in the text of a paragraph's runs after Markdown has
been parsed (markdown-it leaves an unresolved ``[…]`` as text), never inside code and never
across a line break. Only that exact shape counts; any other brackets and braces stay text
(``[a] {.success}``, ``[a]{.success extra}``, ``[a](https://example.com){.x}``).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from typing import Final

from pta_documents.design.colors import StatusCategory
from pta_documents.errors import DocumentConversionError, DocumentFormat

MASK: Final = "\x01"
"""Stands for code and line breaks in the joined text, so that no span starts, ends or crosses
there."""

PATTERN: Final = re.compile(r"\[(?P<words>[^\[\]\x01]+)\]\{\.(?P<category>[A-Za-z]+)\}")
"""A span: ``[``, the words (no brackets, nothing masked), ``]{.``, the category, ``}``."""

VALID: Final = ", ".join("{." + c.value + "}" for c in StatusCategory)


def category(span: re.Match[str], format: DocumentFormat) -> StatusCategory:
    """The category a span found by ``PATTERN`` names; raises when it names none."""
    name = span.group("category").lower()
    for candidate in StatusCategory:
        if candidate.value == name:
            return candidate
    raise DocumentConversionError(format, f"'{span.group(0)}' names no colour. Valid: {VALID}.")


def masked(text: str, is_code: bool) -> str:
    """``text`` as it takes part in the search: code and line breaks masked."""
    return MASK * len(text) if is_code else text.replace("\n", MASK)


def apply[T](
    runs: Sequence[T],
    text: Callable[[T], str],
    is_code: Callable[[T], bool],
    with_text: Callable[[T, str], T],
    colour: Callable[[T, StatusCategory], T],
    format: DocumentFormat,
) -> list[T]:
    """``runs`` with every coloured span taken apart: brackets and braces dropped, the words in
    runs of their own made by ``colour``. Runs are left alone when there is no span.

    ``text`` gives a run's text (a line break as ``"\\n"``), ``is_code`` whether it is code (or
    anything else no span may cross), ``with_text`` a copy of a run with other text. Raises
    ``DocumentConversionError`` for a span that names no category.
    """
    whole = "".join(masked(text(run), is_code(run)) for run in runs)
    spans = list(PATTERN.finditer(whole))
    if not spans:
        return list(runs)

    categories: list[StatusCategory | None] = [None] * len(whole)
    dropped = [False] * len(whole)
    for span in spans:
        found = category(span, format)
        words_start, words_end = span.span("words")
        for i in range(span.start(), span.end()):
            if words_start <= i < words_end:
                categories[i] = found
            else:
                dropped[i] = True

    result: list[T] = []
    position = 0
    for run in runs:
        content = text(run)
        start = position
        position += len(content)
        if not content or is_code(run) or content == "\n":
            result.append(run)
            continue
        pieces: list[tuple[StatusCategory | None, list[str]]] = []
        for k in range(start, position):
            if dropped[k]:
                continue
            if not pieces or pieces[-1][0] != categories[k]:
                pieces.append((categories[k], []))
            pieces[-1][1].append(content[k - start])
        for found, characters in pieces:
            made = with_text(run, "".join(characters))
            result.append(colour(made, found) if found is not None else made)
    return result
