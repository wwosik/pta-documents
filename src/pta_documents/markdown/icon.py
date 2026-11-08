"""``:icon-check:`` as an ``icon`` token with the name in ``meta[NAME]`` (E15-S03).

An inline rule of its own: a colon, ``icon-``, a name of lower-case letters, digits and
hyphens, a colon. Code spans keep it as text (their rule runs first). Whether the name is one of
the bundled icons (``design.icons``) is checked by ``generation.common.layout_syntax.check``,
like the names of containers.
"""

from __future__ import annotations

import re
from typing import Final

from markdown_it import MarkdownIt
from markdown_it.rules_inline.state_inline import StateInline

ICON: Final = "icon"
"""The token type."""
NAME: Final = "name"
"""The key of the icon's name in the token's ``meta``."""
PATTERN: Final = re.compile(r":icon-([a-z0-9]+(?:-[a-z0-9]+)*):")


def icon_plugin(md: MarkdownIt) -> None:
    md.inline.ruler.before("emphasis", ICON, _tokenize)


def _tokenize(state: StateInline, silent: bool) -> bool:
    if state.src[state.pos] != ":":
        return False
    match = PATTERN.match(state.src, state.pos)
    if match is None:
        return False
    if not silent:
        token = state.push(ICON, "", 0)
        token.markup = match.group(0)
        token.meta = {NAME: match.group(1)}
    state.pos = match.end()
    return True


def markdown(name: str) -> str:
    """The Markdown of the icon ``name``: ``:icon-name:``."""
    return f":icon-{name}:"
