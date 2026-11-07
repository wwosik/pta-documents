"""The Markdown parser all generators share: markdown-it-py with the extensions DocLibs used."""

from __future__ import annotations

from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin


def create_parser() -> MarkdownIt:
    """CommonMark plus tables, strikethrough, footnotes, task lists and definition lists.

    Raw HTML is recognised (``html_block``/``html_inline`` tokens) so that the generators can
    leave it out and say so (``raw-html`` note); none of them renders it.
    """
    parser = MarkdownIt("commonmark", {"html": True, "linkify": False, "typographer": False})
    parser.enable(["table", "strikethrough"])
    parser.use(footnote_plugin).use(tasklists_plugin).use(deflist_plugin)
    return parser


def parse(markdown: str) -> list[Token]:
    """The block token stream; ``token.map`` holds zero-based [start, end) line numbers."""
    return create_parser().parse(markdown)


def line_of(token: Token, offset: int = 0) -> int | None:
    """The one-based line of a block token in the original Markdown (``offset`` = front matter)."""
    if token.map is None:
        return None
    return token.map[0] + 1 + offset


def child_lines(inline: Token, offset: int = 0) -> list[int | None]:
    """The one-based line of each child of an ``inline`` token, counting its line breaks.

    Inline tokens carry the lines of their block; a child after a soft or hard break is on the
    next line. Table cells all get the line of their row.
    """
    if inline.map is None:
        return [None] * len(inline.children or [])
    line = inline.map[0] + 1 + offset
    result: list[int | None] = []
    for child in inline.children or []:
        result.append(line)
        if child.type in ("softbreak", "hardbreak"):
            line += 1
    return result
