"""Text split into grapheme clusters: what a reader sees as one character (E05-S04).

Port of the use DocLibs makes of ``StringInfo.GetTextElementEnumerator``, without a new
dependency and deliberately simpler than UAX #29: a cluster is a base character with what
follows it and cannot stand alone — combining marks (``unicodedata.combining`` and the
categories ``Mn``, ``Mc``, ``Me``, so also the keycap U+20E3), variation selectors, the emoji
modifiers U+1F3FB–U+1F3FF, tag characters (flags of regions) and, after a zero-width joiner,
the next character (``👨‍👩‍👧``); two regional indicators make one flag; CR LF stays one
cluster. If this is not enough, the package ``regex`` (``\\X``) would be the alternative.
"""

from __future__ import annotations

import unicodedata
from typing import Final

ZERO_WIDTH_JOINER: Final = "‍"
EXTENDING_CATEGORIES: Final = frozenset({"Mn", "Mc", "Me"})


def _extends(char: str) -> bool:
    """Whether ``char`` belongs to the cluster before it."""
    code = ord(char)
    return (
        unicodedata.combining(char) != 0
        or unicodedata.category(char) in EXTENDING_CATEGORIES
        or 0xFE00 <= code <= 0xFE0F
        or 0xE0100 <= code <= 0xE01EF
        or 0x1F3FB <= code <= 0x1F3FF
        or 0xE0020 <= code <= 0xE007F
        or char == ZERO_WIDTH_JOINER
    )


def _regional_indicator(char: str) -> bool:
    return 0x1F1E6 <= ord(char) <= 0x1F1FF


def clusters(text: str) -> list[str]:
    """The grapheme clusters of ``text`` in order; joined, they are ``text`` again."""
    result: list[str] = []
    i = 0
    while i < len(text):
        start = i
        char = text[i]
        i += 1
        following = text[i] if i < len(text) else ""
        crlf = char == "\r" and following == "\n"
        flag = _regional_indicator(char) and following != "" and _regional_indicator(following)
        if crlf or flag:
            i += 1
        while i < len(text) and _extends(text[i]):
            joiner = text[i] == ZERO_WIDTH_JOINER
            i += 1
            if joiner and i < len(text):
                i += 1  # the character the joiner joins
        result.append(text[start:i])
    return result


def code_points(cluster: str) -> str:
    """``U+1F44D U+1F3FD``: the code points of ``cluster``, each as one (outside the BMP too)."""
    return " ".join(f"U+{ord(c):04X}" for c in cluster)
