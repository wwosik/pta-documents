"""Raw HTML in the Markdown: no generator renders it; it is left out with a ``raw-html`` note.

Two kinds of HTML are not "raw" in that sense: comments are left out silently (they are notes
to the writer), and ``<br>`` is a line break — the converters write it in table cells.
"""

from __future__ import annotations

import re
from typing import Final

from pta_documents.generation.common.result import NoteCodes, Notes

_LINE_BREAK: Final = re.compile(r"^<br\s*/?>$", re.IGNORECASE)


def is_comment(html: str) -> bool:
    return html.lstrip().startswith("<!--")


def is_line_break(html: str) -> bool:
    return _LINE_BREAK.match(html.strip()) is not None


def is_checkbox(html: str) -> bool:
    """The ``<input type="checkbox">`` the task-list plugin makes of ``- [ ]``."""
    return html.lstrip().startswith("<input") and "checkbox" in html


def note_raw_html(notes: Notes, line: int | None, what: str) -> None:
    """Note HTML left out of ``what`` ("the deck", "the document"); comments get no note."""
    notes.add(
        NoteCodes.RAW_HTML,
        line,
        f"Raw HTML is left out of {what}. Write it in Markdown, or leave it out.",
    )
