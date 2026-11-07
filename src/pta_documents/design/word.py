"""What the Word generator needs to know beyond the template itself.

Everything the PTA Word templates define (styles, numbering, page setup, header, footer) is read
from the template; this module only names the styles the generator uses and defines the few
things the templates lack.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from pta_documents.design import colors, slides


@dataclass(frozen=True)
class WordStyles:
    """Style names as stored in ``styles.xml`` (``w:name``), which python-docx looks up.

    Built-in styles carry their English internal names; Word shows them in German
    (``heading 1`` is "Überschrift 1", ``List Bullet`` is "Aufzählungszeichen").
    """

    normal: str = "Normal"
    normal_bold: str = "Standard fett"
    title: str = "Title"
    subtitle: str = "Subtitle"
    author: str = "Autor"
    headings: tuple[str, str, str] = ("heading 1", "heading 2", "heading 3")
    sub_heading: str = "Zwischenüberschrift"
    list_bullet: str = "List Bullet"
    list_number: str = "List Paragraph"
    caption: str = "caption"
    footnote_text: str = "footnote text"
    footnote_reference: str = "footnote reference"
    table: str = "PTA"
    hyperlink: str = "Hyperlink"
    toc: tuple[str, str] = ("toc 1", "toc 2")
    code: str = "Code"
    """Added by the generator; the templates have no code style."""
    quote: str = "Zitat"
    """Added by the generator; the templates have no quote style."""
    note: str = "Hinweis"
    """Added by the generator: alerts NOTE and TIP, conclusion and comment boxes."""
    note_important: str = "Hinweis wichtig"
    """Added by the generator: alerts IMPORTANT, WARNING and CAUTION."""
    mark: str = "Markierung"
    """Added by the generator: the character style of ``==mark==``."""
    picture_row: str = "Bildreihe"
    """Added by the generator: the table style without rules of a row of pictures."""
    status: tuple[tuple[colors.StatusCategory, str], ...] = (
        (colors.StatusCategory.SUCCESS, "Status Erfolg"),
        (colors.StatusCategory.WARNING, "Status Warnung"),
        (colors.StatusCategory.DANGER, "Status Gefahr"),
        (colors.StatusCategory.INFO, "Status Info"),
        (colors.StatusCategory.NEUTRAL, "Status Neutral"),
    )
    """Added by the generator: the bold character styles of coloured words and status labels."""

    def status_style(self, category: colors.StatusCategory) -> str:
        return dict(self.status)[category]


STYLES: Final = WordStyles()

BORROWED_STYLES: Final = (STYLES.hyperlink, *STYLES.toc)
"""Styles missing from the landscape templates; taken over from the portrait template."""

TITLE_PLACEHOLDER: Final = "Titel des Dokuments"
SUBTITLE_PLACEHOLDER: Final = "Untertitel des Dokuments"
DATE_PLACEHOLDER: Final = "xx.xx.xxxx"
AS_OF_LABEL: Final = "Stand:"
PAGE_LABEL: Final = "Seite"
TOC_FIELD: Final = 'TOC \\o "1-2" \\h \\z \\u'


@dataclass(frozen=True)
class CodeStyle:
    """The paragraph style for code blocks (decision 2026-11-06: Consolas on light grey)."""

    font: str = "Consolas"
    size_pt: float = 9
    background: str = colors.GREY_LIGHT


CODE: Final = CodeStyle()

QUOTE_INDENT_CM: Final = 1.25
"""Quotes are indented by one default tab stop."""

HORIZONTAL_RULE_COLOR: Final = colors.GREY_MID

INLINE_CODE_FONT: Final = "Consolas"


@dataclass(frozen=True)
class NoteStyle:
    """A paragraph style for alerts and boxes: a rule on the left on a light grey area."""

    rule: str
    rule_pt: float = 3
    background: str = colors.GREY_LIGHT
    indent_pt: float = 6
    """Room between the rule and the text."""


NOTE: Final = NoteStyle(rule=colors.PTA_BLUE)
NOTE_IMPORTANT: Final = NoteStyle(rule=colors.YELLOW)
MARK_COLOR: Final = colors.YELLOW
"""``==mark==`` in exact PTA yellow (Word's highlighter only knows its own yellow)."""

PICTURES_PER_ROW: Final = slides.MAX_PICTURES_PER_ROW
"""More pictures in one paragraph go on further rows (as ``MAX_PICTURES_PER_ROW`` on slides)."""
PICTURE_GAP_CM: Final = 0.3
"""Room between the pictures of a row."""
CONTACT_PHOTO_CM: Final = 3.0
"""The width a contact photo is shown at, at most."""
TABLE_BASE_STYLE: Final = "Normal Table"
"""The built-in table style without rules the picture row style is based on."""
