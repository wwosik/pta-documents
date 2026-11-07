"""``==marked text==`` as ``mark_open``/``mark_close`` tokens (tag ``mark``).

The rule of ``markdown-it-mark`` (MIT), written after the ``~~strikethrough~~`` rule of
markdown-it-py (MIT): the same delimiter handling with ``=`` instead of ``~``. mdit-py-plugins
has no such plugin.
"""

from __future__ import annotations

from typing import Final

from markdown_it import MarkdownIt
from markdown_it.rules_inline.state_inline import Delimiter, StateInline

_EQUALS: Final = 0x3D


def mark_plugin(md: MarkdownIt) -> None:
    md.inline.ruler.before("emphasis", "mark", _tokenize)
    md.inline.ruler2.before("emphasis", "mark", _post_process)


def _tokenize(state: StateInline, silent: bool) -> bool:
    start = state.pos
    if silent or state.src[start] != "=":
        return False
    scanned = state.scanDelims(start, True)
    length = scanned.length
    if length < 2:
        return False
    if length % 2:
        token = state.push("text", "", 0)
        token.content = "="
        length -= 1
    for _ in range(length // 2):
        token = state.push("text", "", 0)
        token.content = "=="
        state.delimiters.append(
            Delimiter(
                marker=_EQUALS,
                length=0,
                token=len(state.tokens) - 1,
                end=-1,
                open=scanned.can_open,
                close=scanned.can_close,
            )
        )
    state.pos += scanned.length
    return True


def _balance(state: StateInline, delimiters: list[Delimiter]) -> None:
    lone_markers: list[int] = []
    for start in delimiters:
        if start.marker != _EQUALS or start.end == -1:
            continue
        end = delimiters[start.end]
        token = state.tokens[start.token]
        token.type, token.tag, token.nesting, token.markup, token.content = (
            "mark_open",
            "mark",
            1,
            "==",
            "",
        )
        token = state.tokens[end.token]
        token.type, token.tag, token.nesting, token.markup, token.content = (
            "mark_close",
            "mark",
            -1,
            "==",
            "",
        )
        previous = state.tokens[end.token - 1]
        if previous.type == "text" and previous.content == "=":
            lone_markers.append(end.token - 1)
    # An odd run '=====' is split into '=' '==' '==': move the lone '=' after the closers.
    while lone_markers:
        i = lone_markers.pop()
        j = i + 1
        while j < len(state.tokens) and state.tokens[j].type == "mark_close":
            j += 1
        j -= 1
        if i != j:
            state.tokens[i], state.tokens[j] = state.tokens[j], state.tokens[i]


def _post_process(state: StateInline) -> None:
    _balance(state, state.delimiters)
    for meta in state.tokens_meta:
        if meta and "delimiters" in meta:
            _balance(state, meta["delimiters"])
