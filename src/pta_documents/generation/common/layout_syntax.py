"""The names of the slide-layout Markdown that every generator checks alike.

Port of DocLibs ``LayoutSyntax``: ``:::`` containers and alert kinds. Decks draw them (E04-S03);
Word and PDF show their content plainly (E03-S03, E05-S04), but all of them reject the same
mistakes with the same message — ``check`` runs before anything is written.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from markdown_it.token import Token

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import coloured_words, heading_attributes
from pta_documents.markdown.parser import ALERT, CONTAINER_OPEN, child_lines, container, line_of

CARDS: Final = "cards"
ROWS: Final = "rows"
PANEL: Final = "panel"
STATEMENT: Final = "statement"
COLUMNS: Final = "columns"

CONTAINER_NAMES: Final = (CARDS, ROWS, PANEL, STATEMENT, COLUMNS)
CONTAINERS: Final = ", ".join(CONTAINER_NAMES)
"""The containers, for error messages."""

ALERT_KINDS: Final = ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION")
ALERTS: Final = ", ".join(ALERT_KINDS)
"""The alerts, for error messages."""

_IMPORTANT: Final = ("IMPORTANT", "WARNING", "CAUTION")

STATUS: Final = "status"
"""The key in a text token's ``meta`` of the ``StatusCategory`` of coloured words (see
``coloured``)."""


def check_container(name: str, arguments: str, format: DocumentFormat) -> None:
    """Raise for an unknown container or arguments it does not take: ``panel`` takes ``dark``,
    ``columns`` a ratio of two or three widths (``1:2``), the others none."""
    if name not in CONTAINER_NAMES:
        raise DocumentConversionError(
            format, f"Unknown container '::: {name}'. Valid containers: {CONTAINERS}."
        )
    if name == COLUMNS:
        if arguments and column_widths(arguments) is None:
            raise DocumentConversionError(
                format,
                f"The container '::: columns {arguments}' takes the widths of its columns as a "
                "ratio of two or three whole numbers, such as 1:2.",
            )
        return
    if arguments and not (name == PANEL and arguments == "dark"):
        but = " but dark" if name == PANEL else ""
        raise DocumentConversionError(
            format, f"The container '::: {name} {arguments}' takes no arguments{but}."
        )


def column_widths(arguments: str) -> list[int] | None:
    """The widths of ``::: columns 1:2`` as weights; None when they are not two or three whole
    numbers from 1 to 99."""
    parts = arguments.split(":")
    if len(parts) not in (2, 3) or not all(p.isascii() and p.isdigit() for p in parts):
        return None
    widths = [int(p) for p in parts]
    return widths if all(0 < w < 100 for w in widths) else None


def columns(parts: int, any_empty: bool, arguments: str, format: DocumentFormat) -> list[int]:
    """The weights of a ``::: columns`` of ``parts`` parts (split at ``---``): those of its
    arguments, else equal. Raises when there are not two or three parts with content, or the
    widths do not match them."""
    if parts not in (2, 3) or any_empty:
        raise DocumentConversionError(
            format,
            "A '::: columns' holds two or three columns, separated by a line '---' with a blank "
            "line before it.",
        )
    widths = column_widths(arguments) if arguments else [1] * parts
    if widths is None or len(widths) != parts:
        count = len(widths) if widths is not None else 0
        raise DocumentConversionError(
            format, f"'::: columns {arguments}' gives {count} widths for {parts} columns."
        )
    return widths


def is_important(kind: str, format: DocumentFormat) -> bool:
    """Whether an alert kind stands out (important, warning, caution) rather than being a note
    or tip; raises for an unknown kind."""
    upper = kind.upper()
    if upper not in ALERT_KINDS:
        raise DocumentConversionError(format, f"Unknown alert '[!{kind}]'. Valid alerts: {ALERTS}.")
    return upper in _IMPORTANT


def heading(
    inline: Token, level: int, format: DocumentFormat
) -> tuple[str | None, heading_attributes.HeadingAttributes | None]:
    """The attributes at the end of a ``#``/``##`` heading's inline token, checked for its
    level, and the text of its last child without them (None when that child is no text)."""
    children = inline.children or []
    if not children or children[-1].type != "text":
        return None, None
    text, attributes = heading_attributes.split(children[-1].content, format)
    if attributes is not None:
        heading_attributes.check_level(attributes, level, format)
    return text, attributes


def without_attributes(
    inline: Token, level: int, format: DocumentFormat
) -> tuple[Token, heading_attributes.HeadingAttributes | None]:
    """The inline token of a heading of ``level`` without its attributes (a copy; ``inline``
    itself when it has none or is no ``#``/``##``), and the attributes, checked for the level."""
    if level > 2:
        return inline, None
    text, attributes = heading(inline, level, format)
    if attributes is None or text is None:
        return inline, attributes
    children = list(inline.children or [])
    children[-1] = children[-1].copy(content=text)
    return inline.copy(children=children), attributes


def coloured(inline: Token, format: DocumentFormat) -> Token:
    """The inline token with ``[words]{.success}`` taken apart: brackets and braces gone, the
    words in text tokens of their own with the category in ``meta[STATUS]`` (a copy; ``inline``
    itself without coloured words)."""
    children = inline.children or []
    result = coloured_words.apply(
        children,
        token_text,
        token_is_code,
        lambda child, text: child.copy(content=text),
        lambda child, category: child.copy(meta={**child.meta, STATUS: category}),
        format,
    )
    return inline if result == children else inline.copy(children=result)


def check(tokens: Sequence[Token], format: DocumentFormat, line_offset: int = 0) -> None:
    """Check every container, alert, heading attribute and coloured word of a document.

    ``tokens`` are those of ``markdown.parser.parse`` on the body, ``line_offset`` the lines of
    front matter before it. A mistake raises ``DocumentConversionError`` whose reason starts
    with its line: ``Line 12: Unknown container '::: card'. …``.
    """
    for i, token in enumerate(tokens):
        line = line_of(token, line_offset)
        try:
            if token.type == CONTAINER_OPEN:
                check_container(*container(token), format)
            elif token.type == "blockquote_open" and ALERT in token.meta:
                is_important(str(token.meta[ALERT]), format)
            elif token.type == "heading_open" and token.tag in ("h1", "h2"):
                heading(tokens[i + 1], int(token.tag[1]), format)
        except DocumentConversionError as error:
            raise _at(error, line) from None
        if token.type == "inline":
            heading_level = (
                int(tokens[i - 1].tag[1])
                if i > 0 and tokens[i - 1].type == "heading_open"
                else None
            )
            _check_coloured_words(token, heading_level, format, line_offset)


def _check_coloured_words(
    inline: Token, heading_level: int | None, format: DocumentFormat, line_offset: int
) -> None:
    children = list(inline.children or [])
    if heading_level in (1, 2) and children and children[-1].type == "text":
        # The attribute block of a heading is no coloured word.
        text, _ = heading_attributes.split(children[-1].content, format)
        children[-1] = children[-1].copy(content=text)
    lines = child_lines(inline, line_offset)
    whole: list[str] = []
    line_at: list[int | None] = []
    for child, line in zip(children, lines, strict=True):
        part = coloured_words.masked(token_text(child), token_is_code(child))
        whole.append(part)
        line_at.extend([line] * len(part))
    for span in coloured_words.PATTERN.finditer("".join(whole)):
        try:
            coloured_words.category(span, format)
        except DocumentConversionError as error:
            raise _at(error, line_at[span.start()]) from None


def token_text(child: Token) -> str:
    """The text an inline child adds to its paragraph for ``coloured_words.apply``: a line break
    is ``"\\n"``, an image, HTML or footnote one masked character, markup nothing."""
    match child.type:
        case "text" | "code_inline":
            return child.content
        case "softbreak" | "hardbreak":
            return "\n"
        case "image" | "html_inline" | "footnote_ref":
            return coloured_words.MASK
        case _:
            return ""


def token_is_code(child: Token) -> bool:
    """Whether no coloured span may start, end or cross the inline child (all but text)."""
    return child.type != "text"


def _at(error: DocumentConversionError, line: int | None) -> DocumentConversionError:
    if line is None:
        return error
    return DocumentConversionError(error.format, f"Line {line}: {error.reason}")
