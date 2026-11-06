"""What the PowerPoint generator needs to know beyond the template itself.

Layouts, placeholders, text levels and the theme come from the PTA template; this module names the
layouts (they have no ``type``, only names) and defines what the generator draws itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from pta_documents.design import colors

CM: Final = 360_000
"""EMU per centimetre."""


def cm(value: float) -> int:
    """Centimetres to EMU."""
    return round(value * CM)


@dataclass(frozen=True)
class Layouts:
    """Names of the PTA slide layouts, verbatim (including the typo of the closing layout)."""

    title_image_01: str = "Titelfolie mit Bild 01"
    title_image_02: str = "Titelfolie mit Bild 02"
    title_industries: str = "Titelfolie Branchen"
    title_plain: str = "Titelfolie ohne Bild"
    chapter: str = "Trennfolie"
    title_only: str = "Nur Titel"
    title_and_text: str = "Titel und Text"
    title_and_two_texts: str = "Titel und Text (zweispaltig)"
    title_text_image: str = "Titel, Text und Bild 01"
    title_image: str = "Titel und Bild 01"
    closing: str = "Abbschlussfolie"


LAYOUTS: Final = Layouts()

TITLE_SLIDES: Final = {
    "bild-01": LAYOUTS.title_image_01,
    "bild-02": LAYOUTS.title_image_02,
    "branchen": LAYOUTS.title_industries,
    "ohne-bild": LAYOUTS.title_plain,
}
"""Front matter ``titelfolie:`` -> layout."""
DEFAULT_TITLE_SLIDE: Final = "bild-02"


@dataclass(frozen=True)
class Placeholders:
    """Placeholder indices (``p:ph/@idx``) of the layouts the generator fills."""

    title: int = 0
    subtitle: int = 12
    byline: int = 13
    chapter_number: int = 14
    body: int = 12
    second_body: int = 13
    picture: int = 31
    footer_types: tuple[str, str, str] = ("ftr", "sldNum", "dt")


PLACEHOLDERS: Final = Placeholders()

DECORATIVE_PROMPT: Final = "x"
"""Layout placeholders with this prompt only draw graphics and are created empty on every slide."""


@dataclass(frozen=True)
class Area:
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


CONTENT_AREA: Final = Area(cm(1.33), cm(4.62), cm(31.20), cm(13.10))
"""The content area of the master (x 1.33-32.53 cm, y 4.62-17.72 cm)."""
COLUMN_GAP: Final = cm(1.00)


@dataclass(frozen=True)
class TextLevels:
    """Paragraph levels (``a:p/a:pPr/@lvl``) of the PTA body placeholders, zero-based."""

    subheadline: int = 0
    intro: int = 1
    bullets: tuple[int, int, int] = (2, 3, 4)


TEXT_LEVELS: Final = TextLevels()

LEVEL_SIZES_PT: Final = (18.0, 18.0, 18.0, 16.0, 14.0)
"""Font sizes of the five text levels of the master (for fitting)."""
MIN_FONT_PT: Final = 12.0
"""Fitting shrinks text down to this size, then continues on a new slide (decision 2026-11-06)."""

HEADING_FONT: Final = "Segoe UI"
BODY_FONT: Final = "Segoe UI Light"
"""Emphasis (``**bold**``) is set in the heading font: PTA rule for highlights."""
CODE_FONT: Final = "Consolas"
CODE_SIZE_PT: Final = 14.0
CODE_BACKGROUND: Final = colors.GREY_LIGHT
LINK_COLOR: Final = colors.DARK_BLUE


@dataclass(frozen=True)
class TableStyle:
    """Slide tables after the sample table of the template collection (slide 38)."""

    title_height: int = cm(1.30)
    title_size_pt: float = 18
    title_color: str = colors.PTA_BLUE
    header_height: int = cm(1.30)
    header_size_pt: float = 16
    header_fill: str = colors.DARK_BLUE
    header_color: str = colors.WHITE
    row_height: int = cm(1.10)
    row_size_pt: float = 14
    row_color: str = colors.TEXT_SLIDES
    rule_color: str = colors.GREY_LIGHT
    closing_rule_color: str = colors.TEXT_SLIDES
    rule_width_pt: float = 0.5


TABLE: Final = TableStyle()

FOOTER_PREFIX: Final = "PTA – "
"""The slide footer reads "PTA – <presentation title>"."""

ENGLISH_LOGO_AREA: Final = Area(cm(1.40), cm(1.30), cm(6.35), cm(3.59))
"""Where the English title slide template places the English logo (its sample slide)."""

PICTURE_GAP: Final = cm(0.50)
"""Room between pictures side by side on a slide."""
MAX_PICTURES_PER_ROW: Final = 4
