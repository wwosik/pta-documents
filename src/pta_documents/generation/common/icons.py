"""Icons in the Markdown (E15-S03): checking their names and finding the ones that are figures.

``:icon-check:`` is an ``icon`` token (``markdown.icon``). Where it stands decides what it is:

- at the start of the ``###`` title of a card (``::: cards``): the card's figure (decks);
- at the start of every item of a bullet list: the items' bullets (``list_icons``);
- anywhere else: inline, as high as the text (Word and PDF; decks refuse it).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from markdown_it.token import Token

from pta_documents.design import colors, icons
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.markdown.icon import ICON, NAME
from pta_documents.markdown.parser import child_lines

COLOR: Final = colors.PTA_BLUE
"""The colour of figures and bullets; on dark areas they are white."""


def name_of(child: Token) -> str:
    """The name of an ``icon`` child."""
    return str(child.meta[NAME])


def color_on(dark: bool) -> str:
    return colors.WHITE if dark else COLOR


def check(inline: Token, format: DocumentFormat, line_offset: int = 0) -> None:
    """Raise for an icon of ``inline`` that is not bundled: ``Line N: Unknown icon …`` with the
    three most similar names."""
    children = inline.children or []
    for child, line in zip(children, child_lines(inline, line_offset), strict=True):
        if child.type == ICON and not icons.is_icon(name_of(child)):
            reason = icons.unknown(name_of(child))
            raise DocumentConversionError(format, f"Line {line}: {reason}" if line else reason)


def leading(inline: Token) -> str | None:
    """The name of the icon ``inline`` starts with (spaces before it aside); None: none."""
    for child in inline.children or []:
        if child.type == "text" and not child.content.strip():
            continue
        return name_of(child) if child.type == ICON else None
    return None


def without_leading(inline: Token) -> Token:
    """A copy of ``inline`` without its leading icon and the spaces around it (``inline``
    itself when it does not start with an icon)."""
    children = list(inline.children or [])
    start = next(
        (k for k, c in enumerate(children) if not (c.type == "text" and not c.content.strip())),
        None,
    )
    if start is None or children[start].type != ICON:
        return inline
    rest = children[start + 1 :]
    if rest and rest[0].type == "text":
        stripped = rest[0].content.lstrip()
        rest = ([rest[0].copy(content=stripped)] if stripped else []) + rest[1:]
    return inline.copy(children=rest)


def list_icons(tokens: Sequence[Token], i: int) -> list[str] | None:
    """For the bullet list opening at ``tokens[i]``: the icon each of its items starts with,
    when every item's first paragraph starts with one; None otherwise (also for ordered
    lists)."""
    if tokens[i].type != "bullet_list_open":
        return None
    level = tokens[i].level
    names: list[str] = []
    j = i + 1
    while j < len(tokens) and not (
        tokens[j].type == "bullet_list_close" and tokens[j].level == level
    ):
        token = tokens[j]
        if token.type == "list_item_open" and token.level == level + 1:
            after = tokens[j + 1] if j + 2 < len(tokens) else None
            name = (
                leading(tokens[j + 2])
                if after is not None and after.type == "paragraph_open"
                else None
            )
            if name is None:
                return None
            names.append(name)
        j += 1
    return names or None
