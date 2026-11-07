"""Shapes of markdown-it tokens the slide-layout syntax gives a meaning to.

Port of the recognisers in DocLibs ``DeckParser`` (``Tags``, ``LabelledTags``, the label cell,
the marked row, the image row), on the token stream of ``markdown.parser.parse`` so that every
generator finds the same shapes.
"""

from __future__ import annotations

from collections.abc import Sequence

from markdown_it.token import Token


def _blank(child: Token) -> bool:
    return (child.type == "text" and not child.content.strip()) or child.type in (
        "softbreak",
        "hardbreak",
    )


def tags(inline: Token) -> list[str] | None:
    """A paragraph of two or more code spans with nothing but spaces between them (``a``
    ``b``): the texts of the spans; None for any other paragraph."""
    found: list[str] = []
    for child in inline.children or []:
        if child.type == "code_inline":
            found.append(child.content)
        elif not _blank(child):
            return None
    return found if len(found) >= 2 else None


def labelled_tags(tokens: Sequence[Token], i: int) -> list[tuple[str, list[Token]]] | None:
    """A list (``tokens[i]`` its ``*_list_open``) whose every item is one paragraph that starts
    with a code span and goes on with text: per item the label and the inline children after
    it (leading spaces dropped). None for any other list."""
    opening = tokens[i]
    close = opening.type.replace("_open", "_close")
    items: list[tuple[str, list[Token]]] = []
    depth = 0
    j = i + 1
    while j < len(tokens):
        token = tokens[j]
        if token.type == opening.type:
            depth += 1
        elif token.type == close:
            if depth == 0:
                break
            depth -= 1
        elif token.type == "list_item_open" and depth == 0:
            # Exactly list_item_open, paragraph_open, inline, paragraph_close, list_item_close.
            if (
                j + 4 >= len(tokens)
                or tokens[j + 1].type != "paragraph_open"
                or tokens[j + 4].type != "list_item_close"
            ):
                return None
            children = list(tokens[j + 2].children or [])
            if not children or children[0].type != "code_inline":
                return None
            rest = children[1:]
            while rest and _blank(rest[0]):
                rest.pop(0)
            if rest and rest[0].type == "text":
                rest[0] = rest[0].copy(content=rest[0].content.lstrip())
            if not any(c.content.strip() for c in rest if c.type != "softbreak"):
                return None
            items.append((children[0].content, rest))
            j += 5
            continue
        j += 1
    return items or None


def label_cell(inline: Token) -> str | None:
    """A table cell that is exactly one code span (spaces aside): its text, else None."""
    children = [c for c in inline.children or [] if not _blank(c)]
    if len(children) == 1 and children[0].type == "code_inline":
        return children[0].content
    return None


def is_marked(inline: Token) -> bool:
    """Whether an inline token is marked from start to end (``==WaitingForApproval==``)."""
    children = [c for c in inline.children or [] if not _blank(c)]
    if len(children) < 3 or children[0].type != "mark_open" or children[-1].type != "mark_close":
        return False
    depth = 0
    for n, child in enumerate(children):
        if child.type == "mark_open":
            depth += 1
        elif child.type == "mark_close":
            depth -= 1
            if depth == 0 and n != len(children) - 1:
                return False
    return True


def marked_row(cells: Sequence[Token]) -> bool:
    """Whether a table row (the inline tokens of its cells) is highlighted: its first cell is
    marked as a whole."""
    return bool(cells) and is_marked(cells[0])


def only_images(inline: Token) -> list[Token] | None:
    """A paragraph of two or more images and nothing but spaces between them (an image row):
    the image tokens; None for any other paragraph."""
    images: list[Token] = []
    for child in inline.children or []:
        if child.type == "image":
            images.append(child)
        elif not _blank(child):
            return None
    return images if len(images) >= 2 else None
