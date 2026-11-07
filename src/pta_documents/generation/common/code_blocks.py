"""Fenced code blocks in a diagram or chart language.

Blocks in ``KNOWN_GRAPHIC_LANGUAGES`` are meant to be drawn. Until a renderer for them exists
(E02-S04, E06) every such block shows as code, with a ``code-not-drawn`` note.
"""

from __future__ import annotations

from typing import Final

from pta_documents.generation.common.result import NoteCodes, Notes

KNOWN_GRAPHIC_LANGUAGES: Final = ("mermaid", "chart", "financial-chart")


def fence_language(info: str) -> str:
    """The language of a fence's info string: its first word, lower case (``""`` if none)."""
    words = info.split(maxsplit=1)
    return words[0].lower() if words else ""


def note_not_drawn(notes: Notes, info: str, line: int | None) -> None:
    """Note a block in a graphic language that shows as code because nothing drew it."""
    language = fence_language(info)
    if language in KNOWN_GRAPHIC_LANGUAGES:
        notes.add(
            NoteCodes.CODE_NOT_DRAWN,
            line,
            f"The `{language}` block was not drawn and shows as code: no renderer for it is "
            "set up, or it has an error. Check it, or leave it out.",
        )
