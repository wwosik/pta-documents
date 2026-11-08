"""Block markers (E09-S02): a line of only ``{.build}``, ``{.frag}``, ``{.exit}`` or
``{.emphasize}`` marks the block after it for a click of the presentation.

Port of vt-tools-libs ``BlockMarkers``. The line stands on its own — as a paragraph of its own
before the block, or as the first line of the paragraph it marks — and is taken out of the
token stream by a core rule of the shared parser, so that every format reads the same
Markdown: decks build the block (``generation.pptx.animations``), Word and PDF show it as if the
line were not there. ``{.build}`` and ``{.frag}`` take an entrance, ``{.build=fly}``.
``{.internal}`` (E16-S01) is no build: it keeps the block out of the customer version in every
format (``generation.common.audience.filter_tokens``, which takes the marker away).

The marked block's first token carries the ``Marker`` in ``meta[MARKER]``. A marker line that is
wrong stays in the stream as the paragraph it is, with the reason in
``paragraph_open.meta[ERROR]``; ``generation.common.layout_syntax.check`` raises it with its
line, as for every other mistake in the slide syntax.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Final

from markdown_it.rules_core import StateCore
from markdown_it.token import Token

MARKER: Final = "block_marker"
"""The key in the ``meta`` of the first token of a marked block: its ``Marker``."""
ERROR: Final = "block_marker_error"
"""The key in the ``meta`` of a ``paragraph_open`` that is a wrong marker line: the reason."""

BUILD: Final = "build"
"""Lists item by item (every paragraph of every level), cards, rows, columns and image rows
element by element; any other block as a whole."""
FRAGMENT: Final = "frag"
"""The block as a whole on one click."""
EXIT: Final = "exit"
"""The block is there from the start and fades out on its click."""
EMPHASIZE: Final = "emphasize"
"""Text that turns PTA blue on its click."""
INTERNAL: Final = "internal"
"""The block only in the internal and the trainer version (E16-S01,
``generation.common.audience``); in every format."""
NAMES: Final = (BUILD, FRAGMENT, EXIT, EMPHASIZE, INTERNAL)

FADE: Final = "fade"
ENTRANCES: Final = (FADE, "appear", "fly", "wipe")
"""The entrances of ``{.build=…}`` and ``{.frag=…}``; ``fade`` is the default."""
WITH_ENTRANCE: Final = (BUILD, FRAGMENT)

VALID: Final = "{.build}, {.frag}, {.exit}, {.emphasize}, {.internal}"
"""The markers, for error messages."""
VALID_ENTRANCES: Final = ", ".join(f"={e}" for e in ENTRANCES)

LINE: Final = re.compile(r"^[ \t]*\{[ \t]*(?:\.[A-Za-z][\w-]*(?:=[\w-]*)?[ \t]*)+\}[ \t]*$")
"""A line of only classes in braces: a marker line, right or wrong."""
_NUMBERED: Final = re.compile(r"^ {0,3}\d{1,9}[.)](?:[ \t]|$)")
_CLASS: Final = re.compile(r"\.([A-Za-z][\w-]*)(?:=([\w-]*))?")


@dataclass(frozen=True)
class Marker:
    name: str
    """One of ``NAMES``."""
    entrance: str = FADE
    """For ``build`` and ``frag``: one of ``ENTRANCES``."""
    text: str = ""
    """The marker as written, for messages."""
    line: int = field(default=0, compare=False)
    """Its zero-based line in the Markdown parsed, for messages."""


class MarkerError(ValueError):
    """A marker line that names no marker, or more than one."""


def read(line: str) -> Marker | None:
    """The marker of ``line``; None when it is no line of only classes in braces. Raises
    ``MarkerError`` when it is one, but no valid marker."""
    if LINE.match(line) is None:
        return None
    text = line.strip()
    classes = _CLASS.findall(text)
    for name, _ in classes:
        if name not in NAMES:
            raise MarkerError(
                f"Unknown block marker '{text}'. Valid markers: {VALID}; {{.build}} and "
                f"{{.frag}} take an entrance: {VALID_ENTRANCES}."
            )
    if len(classes) != 1:
        raise MarkerError(f"The line '{text}' holds more than one block marker; use one.")
    name, value = classes[0]
    if "=" in text and name not in WITH_ENTRANCE:
        raise MarkerError(f"The block marker '{{.{name}}}' takes no value: write '{{.{name}}}'.")
    if "=" in text and value not in ENTRANCES:
        raise MarkerError(
            f"Unknown entrance '{text}'. {{.{name}}} takes: {VALID_ENTRANCES} (or none: fade)."
        )
    return Marker(name, value or FADE, text)


TEXT_BLOCKS: Final = ("paragraph_open", "heading_open", "bullet_list_open", "ordered_list_open")
"""What ``{.emphasize}`` takes: text that can change its colour."""
_SLIDE_HEADINGS: Final = ("h1", "h2")


def block_markers_rule(state: StateCore) -> None:
    """The core rule (after the block rules, before the inline ones): marker lines out, their
    markers on the blocks they mark.

    A marker line is a paragraph of its own, the first line of the paragraph it marks, or the
    last line of a paragraph right before the block it marks (in a list item, ``{.build}``
    before a nested list continues the item's text).
    """
    tokens = state.tokens
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type != "paragraph_open" or i + 1 >= len(tokens):
            i += 1
            continue
        if _paragraph(tokens, i):
            del tokens[i : i + 3]
        else:
            i += 1


def _paragraph(tokens: list[Token], i: int) -> bool:
    """Take the marker lines of the paragraph at ``tokens[i]``; True when the paragraph was
    nothing but a marker and goes."""
    token, inline = tokens[i], tokens[i + 1]
    lines = inline.content.split("\n")
    markers: list[Marker | None] = []
    start = token.map[0] if token.map is not None else 0
    for n, line in enumerate(lines):
        try:
            marker = read(line)
            markers.append(None if marker is None else replace(marker, line=start + n))
        except MarkerError as error:
            token.meta[ERROR] = str(error)
            return False
    if all(m is None for m in markers):
        return False
    after = tokens[i + 3] if i + 3 < len(tokens) else None
    first, last = markers[0], markers[-1]
    second = next((m for m in markers if m is not None), None)
    if (len(lines) == 2 and first is not None and last is not None) or (
        last is not None and _marker_follows(tokens, i + 3)
    ):
        assert second is not None
        token.meta[ERROR] = f"The block after '{second.text}' has a second block marker."
        return False
    if len(lines) == 1:
        assert first is not None
        reason = _wrong_target(first, after)
        if reason is not None or after is None:
            token.meta[ERROR] = reason or _nothing(first)
            return False
        after.meta[MARKER] = first
        return True
    if any(m is not None for m in markers[1:-1]) or (first is not None and last is not None):
        marker = next(m for m in markers if m is not None)
        token.meta[ERROR] = (
            f"The block marker '{marker.text}' stands within a paragraph: put it on the line "
            "right before the block it marks."
        )
        return False
    if first is not None:
        # The first line of the paragraph it marks.
        reason = _wrong_target(first, token)
        if _NUMBERED.match(lines[1]):
            # CommonMark: a list starting at another number than 1 cannot interrupt a paragraph.
            reason = (
                f"After '{first.text}' a numbered list that does not start at 1 needs a blank "
                "line, or it is read as text."
            )
        if reason is not None:
            token.meta[ERROR] = reason
            return False
        token.meta[MARKER] = first
        _cut(token, inline, lines[1:], first_line=True)
        return False
    assert last is not None
    # The last line of a paragraph, right before the block it marks.
    reason = _wrong_target(last, after)
    if reason is not None or after is None:
        token.meta[ERROR] = reason or _nothing(last)
        return False
    after.meta[MARKER] = last
    _cut(token, inline, lines[:-1], first_line=False)
    return False


def _marker_follows(tokens: list[Token], i: int) -> bool:
    """Whether the block at ``tokens[i]`` is a paragraph that starts with a marker line."""
    if i + 1 >= len(tokens) or tokens[i].type != "paragraph_open":
        return False
    try:
        return read(tokens[i + 1].content.partition("\n")[0]) is not None
    except MarkerError:
        return True


def _cut(token: Token, inline: Token, lines: list[str], first_line: bool) -> None:
    """The paragraph without its marker line."""
    inline.content = "\n".join(lines)
    if inline.map is not None:
        start, end = inline.map
        inline.map = [start + 1, end] if first_line else [start, end - 1]
        token.map = inline.map


def _nothing(marker: Marker) -> str:
    return (
        f"The block marker '{marker.text}' marks nothing: put it on the line right before a "
        "list, table, picture, paragraph or container of the slide."
    )


def _wrong_target(marker: Marker, target: Token | None) -> str | None:
    """Why ``marker`` cannot mark the block that starts with ``target``; None when it can."""
    if target is None or target.nesting == -1 or target.type == "hr":
        return _nothing(marker)
    if MARKER in target.meta:
        return f"The block after '{marker.text}' has a second block marker."
    if target.type == "heading_open" and target.tag in _SLIDE_HEADINGS and target.level == 0:
        if marker.name == INTERNAL:
            return (
                "'{.internal}' before a '#' or '##' heading: write it at the end of the heading "
                "instead ('## Title {.internal}') to leave out the whole chapter or slide."
            )
        return (
            f"The block marker '{marker.text}' stands before a heading that starts a slide; put "
            "it before a block under the heading."
        )
    if (
        target.type.startswith("container_")
        and target.info.strip().split(" ")[0] == "notes"
        and marker.name != INTERNAL
    ):
        return f"The block marker '{marker.text}' cannot mark speaker notes."
    if marker.name == EMPHASIZE and target.type not in TEXT_BLOCKS:
        return (
            f"'{marker.text}' turns text PTA blue: put it before a paragraph, a list or a heading."
        )
    return None
