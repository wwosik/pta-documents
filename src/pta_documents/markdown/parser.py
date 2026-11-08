"""The Markdown parser all generators share: markdown-it-py with the extensions DocLibs used."""

from __future__ import annotations

import re
from typing import Final

from markdown_it import MarkdownIt
from markdown_it.rules_core import StateCore
from markdown_it.token import Token
from mdit_py_plugins.container import container_plugin
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin

from pta_documents.markdown.icon import icon_plugin
from pta_documents.markdown.image_attributes import image_attributes_plugin
from pta_documents.markdown.mark import mark_plugin

CONTAINER_OPEN: Final = "container_layout_open"
"""The token type of a ``::: name arguments`` fence; ``container(token)`` reads both."""
CONTAINER_CLOSE: Final = "container_layout_close"
ALERT: Final = "alert"
"""The key in ``blockquote_open.meta`` of a GitHub alert (``> [!NOTE]``): its kind, upper case."""

_ALERT_MARKER: Final = re.compile(r"^\[!([A-Za-z]+)\][ \t]*(?:\n|$)")


def create_parser() -> MarkdownIt:
    """CommonMark plus tables, strikethrough, footnotes, task lists, definition lists and the
    slide-layout syntax: ``:::`` containers, ``==marks==``, ``:icon-name:`` (E15-S03), image
    attributes ``![…](a.jpg){focus=top}`` (E15-S04) and GitHub alerts.

    Raw HTML is recognised (``html_block``/``html_inline`` tokens) so that the generators can
    leave it out and say so (``raw-html`` note); none of them renders it.

    A container of any name is parsed (token types ``CONTAINER_OPEN``/``CONTAINER_CLOSE``);
    whether the name exists is checked by ``generation.common.layout_syntax.check``. Containers
    nest with longer fences outside (``::::`` around ``:::``). An alert is a block quote whose
    first paragraph starts with a line ``[!KIND]``: the line is removed and the kind is in
    ``blockquote_open.meta[ALERT]``.
    """
    parser = MarkdownIt("commonmark", {"html": True, "linkify": False, "typographer": False})
    parser.enable(["table", "strikethrough"])
    parser.use(footnote_plugin).use(tasklists_plugin).use(deflist_plugin)
    parser.use(container_plugin, "layout", validate=_any_name).use(mark_plugin)
    parser.use(icon_plugin).use(image_attributes_plugin)
    parser.core.ruler.before("inline", "alerts", _alerts)
    return parser


def container(token: Token) -> tuple[str, str]:
    """The name and the arguments of a ``CONTAINER_OPEN`` token: ``::: panel dark`` →
    ``("panel", "dark")``."""
    name, _, arguments = token.info.strip().partition(" ")
    return name, arguments.strip()


def _any_name(params: str, *_: object) -> bool:
    return bool(params.strip())


def _alerts(state: StateCore) -> None:
    tokens = state.tokens
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if (
            token.type == "blockquote_open"
            and i + 2 < len(tokens)
            and tokens[i + 1].type == "paragraph_open"
            and (match := _ALERT_MARKER.match(tokens[i + 2].content)) is not None
        ):
            token.meta[ALERT] = match.group(1).upper()
            inline = tokens[i + 2]
            inline.content = inline.content[match.end() :]
            if not inline.content.strip():
                # The marker was the whole paragraph: drop it.
                del tokens[i + 1 : i + 4]
            elif inline.map is not None:
                inline.map = [inline.map[0] + 1, inline.map[1]]
                tokens[i + 1].map = inline.map
        i += 1


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
