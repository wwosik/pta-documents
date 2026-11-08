"""``![Foto](a.jpg){focus=top .round}``: the braces right after an image (E15-S04).

An inline rule of its own, not ``mdit_py_plugins.attrs``: there ``%`` starts a comment and
``.``/``,`` need quotes, so ``{focus=30%,20%}`` and ``{scale=0.5}`` would stay text. The rule
takes ``{…}`` directly after an image (no space between) up to the next ``}`` on the line and
keeps what is inside, as written, in the image token's ``meta[ATTRIBUTES]``. Which attributes and
values are valid is checked by ``generation.common.image_attributes``, with the line.
"""

from __future__ import annotations

import re
from typing import Final

from markdown_it import MarkdownIt
from markdown_it.rules_inline.state_inline import StateInline

ATTRIBUTES: Final = "pta_documents.image_attributes"
"""The key in an image token's ``meta``: the text between the braces after it."""
RULE: Final = "image_attributes"
PATTERN: Final = re.compile(r"\{([^{}\n]*)\}")


def image_attributes_plugin(md: MarkdownIt) -> None:
    md.inline.ruler.push(RULE, _tokenize)


def _tokenize(state: StateInline, silent: bool) -> bool:
    if state.src[state.pos] != "{" or state.pending or not state.tokens:
        return False
    image = state.tokens[-1]
    if image.type != "image" or ATTRIBUTES in (image.meta or {}):
        return False
    match = PATTERN.match(state.src, state.pos)
    if match is None:
        return False
    if not silent:
        image.meta = {**(image.meta or {}), ATTRIBUTES: match.group(1)}
    state.pos = match.end()
    return True


def markdown(attributes: str) -> str:
    """The braces of ``attributes`` (``.round``) as written after an image; empty for none."""
    return "{" + attributes + "}" if attributes else ""
