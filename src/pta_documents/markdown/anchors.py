"""Anchors of headings as GitHub makes them, so that ``[text](#anker)`` works as on GitHub.

The text of a heading in lower case, without punctuation, spaces as hyphens; a second heading
with the same anchor gets ``-1``, a third ``-2`` (E05-S02).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Final

_DROPPED: Final = re.compile(r"[^\w\- ]")


def slug(text: str) -> str:
    """The anchor GitHub gives a heading of ``text``: ``"Größe & Maß"`` → ``"größe--maß"``."""
    lowered = unicodedata.normalize("NFC", text.strip()).lower()
    return _DROPPED.sub("", lowered).replace(" ", "-")


class Anchors:
    """Unique anchors in the order the headings come (a new instance per document)."""

    def __init__(self) -> None:
        self._seen: dict[str, int] = {}

    def add(self, text: str) -> str:
        base = slug(text)
        count = self._seen.get(base)
        if count is None:
            self._seen[base] = 0
            return base
        count += 1
        self._seen[base] = count
        anchor = f"{base}-{count}"
        while anchor in self._seen:
            count += 1
            anchor = f"{base}-{count}"
        self._seen[base] = count
        self._seen[anchor] = 0
        return anchor
