"""The PTA colours — the only module of the library that spells out colour values.

Values come from the themes of the PTA templates (Word theme ``PTA``, PowerPoint theme
``PTA 2020``); ``tests/design/test_model_matches_templates.py`` checks them against the files.
Colours are RGB hex strings without ``#``, as Office XML writes them.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

PTA_BLUE: Final = "006FB9"
"""Accent 1: titles, heading 1, bullets, Word table header, captions, logo."""
DARK_BLUE: Final = "004676"
"""Accent 2: hyperlinks, slide table header, conclusion box."""
LIGHT_BLUE: Final = "9FD8FF"
"""Accent 3: the gradient lines under headers and over footers."""
GREY_DARK: Final = "787878"
"""Accent 4: visited hyperlinks, slide footer."""
GREY_MID: Final = "AFAFAF"
"""Accent 5: Word table rules, horizontal rules."""
GREY_LIGHT: Final = "E6E6E6"
"""Accent 6 and dark 2: areas, slide table rules, code backgrounds."""
YELLOW: Final = "FDDC35"
"""Light 2: highlights (``==mark==``)."""
WHITE: Final = "FFFFFF"
SIGNAL_GREEN: Final = "00B070"
SIGNAL_AMBER: Final = "EAB500"
SIGNAL_RED: Final = "D91E18"

TEXT_WORD: Final = "000000"
"""Text colour of the Word templates (dark 1)."""
TEXT_SLIDES: Final = "404040"
"""Text colour of the PowerPoint templates (dark 1), also the closing rule of slide tables."""

ACCENTS: Final = (PTA_BLUE, DARK_BLUE, LIGHT_BLUE, GREY_DARK, GREY_MID, GREY_LIGHT)
"""The accent order of the themes, also the order of chart series."""

SIGNALS: Final = (SIGNAL_GREEN, SIGNAL_AMBER, SIGNAL_RED)
"""The custom colours of the PowerPoint theme (traffic light), only for status."""


class StatusCategory(StrEnum):
    """A status category of coloured words and status labels."""

    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"
    INFO = "info"
    NEUTRAL = "neutral"


STATUS_COLORS: Final = {
    StatusCategory.SUCCESS: SIGNAL_GREEN,
    StatusCategory.WARNING: SIGNAL_AMBER,
    StatusCategory.DANGER: SIGNAL_RED,
    StatusCategory.INFO: PTA_BLUE,
    StatusCategory.NEUTRAL: GREY_MID,
}
