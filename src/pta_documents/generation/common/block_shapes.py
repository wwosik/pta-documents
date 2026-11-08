"""Shapes of Markdown blocks that Word and PDF give the same meaning (E05-S02).

A paragraph that is bold from start to end is "Standard fett", a paragraph of images only is a
figure, ``Tabelle: …`` after a table and ``Abbildung: …`` after a graphic are captions. The DOCX
writer and the PDF layout engine both recognise them here, so that both formats agree.
"""

from __future__ import annotations

from markdown_it.token import Token

from pta_documents.design.variants import GeneratedTexts


def only_strong(children: list[Token]) -> bool:
    """Whether inline ``children`` are bold from the first to the last (``**…**``) and nothing
    else: such a paragraph is "Standard fett"."""
    children = [c for c in children if not (c.type == "text" and not c.content)]
    if (
        len(children) < 3
        or children[0].type != "strong_open"
        or children[-1].type != "strong_close"
    ):
        return False
    depth = 0
    for n, child in enumerate(children):
        if child.type == "strong_open":
            depth += 1
        elif child.type == "strong_close":
            depth -= 1
            if depth == 0 and n != len(children) - 1:
                return False
    return True


def only_images(children: list[Token]) -> bool:
    """Whether inline ``children`` are one or more images and nothing but spaces: a figure."""
    images = [c for c in children if c.type == "image"]
    rest = [c for c in children if c.type != "image"]
    return bool(images) and all(
        c.type == "softbreak" or (c.type == "text" and not c.content.strip()) for c in rest
    )


def is_table_caption(inline: Token, texts: GeneratedTexts) -> bool:
    """``Tabelle: …`` (or ``Table: …``, or the word of the document's language)."""
    return inline.content.startswith((texts.table + ":", "Tabelle:", "Table:"))


def is_figure_caption(inline: Token, texts: GeneratedTexts) -> bool:
    """``Abbildung: …`` (or ``Figure: …``, or the word of the document's language)."""
    return inline.content.startswith((texts.figure + ":", "Abbildung:", "Figure:"))


def strip_caption_prefix(inline: Token) -> Token:
    """A copy of a caption's inline token without the word and colon it starts with."""
    children = list(inline.children or [])
    if children and children[0].type == "text":
        first = children[0]
        content = first.content.split(":", 1)[1].lstrip() if ":" in first.content else first.content
        children[0] = first.copy(content=content)
    return inline.copy(children=children)
