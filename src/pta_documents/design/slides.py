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
    agenda_short: str = "Agenda (kurz)"
    agenda_long: str = "Agenda (lang)"
    interim_01: str = "Zwischenfazit 01"
    interim_02: str = "Zwischenfazit 02"
    quote_01: str = "Zitat 01"
    quote_02: str = "Zitat 02"
    contact_01: str = "Kontakt 01"
    contact_02: str = "Kontakt 02"
    contact_03: str = "Kontakt 03"
    contact_04: str = "Kontakt 04"
    contact_05: str = "Kontakt 05"
    contact_text: str = "Kontakt mit Text"
    chart: str = "Titel und Diagramm"
    two_charts: str = "Titel und zwei Diagramme"
    chart_and_text: str = "Titel, Diagramm und Text"
    text_and_chart: str = "Titel, Text und Diagramm"


LAYOUTS: Final = Layouts()

CONTACT_LAYOUTS: Final = (
    LAYOUTS.contact_01,
    LAYOUTS.contact_02,
    LAYOUTS.contact_03,
    LAYOUTS.contact_04,
    LAYOUTS.contact_05,
)
"""``Kontakt 0n`` for n persons."""
KIND_LAYOUTS: Final = {
    "agenda": (LAYOUTS.agenda_short, LAYOUTS.agenda_long),
    "interim": (LAYOUTS.interim_01, LAYOUTS.interim_02),
    "quote": (LAYOUTS.quote_01, LAYOUTS.quote_02),
    "contact": (*CONTACT_LAYOUTS, LAYOUTS.contact_text),
}
"""The layouts of each PTA slide kind (``heading_attributes.SLIDE_KINDS``), the default first:
``layout="…"`` may choose any of its own kind (E04-S04)."""

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
    agenda_numbers: tuple[int, ...] = (14, 16, 18, 20, 22, 24, 26, 28)
    """``Agenda (kurz)`` has the first four, ``Agenda (lang)`` all eight."""
    agenda_texts: tuple[int, ...] = (15, 17, 19, 21, 23, 25, 27, 29)
    agenda_rules: tuple[int, ...] = (30, 31, 32, 33, 34, 35, 36)
    """The rules between the agenda items (decorative): rule n lies under item n."""
    contacts: tuple[tuple[int, int, int, int, int], ...] = (
        (34, 14, 35, 36, 38),
        (39, 40, 41, 42, 43),
        (44, 45, 46, 47, 48),
        (49, 50, 51, 52, 53),
        (54, 55, 56, 57, 58),
    )
    """Per person of ``Kontakt 0n``: photo, name, function, e-mail, phone (``Kontakt mit Text``:
    the first)."""
    contact_text: int = 37
    chart_title: int = 12
    chart_unit: int = 13
    chart_source: int = 14
    chart: int = 15
    second_chart: tuple[int, int, int, int] = (16, 17, 18, 19)
    """``Titel und zwei Diagramme``, right: title, unit, source, chart."""
    chart_text: int = 16
    """The text of ``Titel, Diagramm und Text`` and ``Titel, Text und Diagramm``."""


PLACEHOLDERS: Final = Placeholders()

AGENDA_SHORT_ITEMS: Final = 4
"""Up to this many items on ``Agenda (kurz)``, up to ``AGENDA_ITEMS`` on ``Agenda (lang)``."""
AGENDA_ITEMS: Final = 8
CONTACT_PERSONS: Final = 5
QUOTE_SOURCE_PT: Final = 24.0
"""The source of a quote: a second paragraph in its placeholder, Segoe UI Light, not italic."""

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

COLUMN_GUIDES: Final = (
    (1.33, 8.33),
    (9.43, 16.43),
    (17.43, 24.43),
    (25.53, 32.53),
)
"""The vertical guides of the master in cm, as (start, end) of its four columns of 7.00 cm;
two columns of 15.10 cm span two of them each (``Titel und Text (zweispaltig)``)."""


def grid(columns: int) -> tuple[tuple[int, int], ...]:
    """(left, width) of ``columns`` equal columns across the content area, at the guides: two
    and four columns on the master's guides, three (and more) with ``COLUMN_GAP`` between."""
    if columns == 4:
        return tuple((cm(start), cm(end - start)) for start, end in COLUMN_GUIDES)
    if columns == 2:
        (start, _), (_, middle), (other, _), (_, end) = COLUMN_GUIDES
        return ((cm(start), cm(middle - start)), (cm(other), cm(end - other)))
    area = CONTENT_AREA
    width = (area.width - (columns - 1) * COLUMN_GAP) // columns
    return tuple((area.left + n * (width + COLUMN_GAP), width) for n in range(columns))


@dataclass(frozen=True)
class FlowStyle:
    """Flow slides (cards, rows, panels, alerts, tags, code, statement, kicker) in the PTA style,
    and the PTA conclusion and comment boxes of the template collection (slides 43, 32)."""

    text_pt: float = 18
    """Text on the slide: the introduction text level of the body (Segoe UI Light, 404040)."""
    card_text_pt: float = 14
    title_pt: float = 18
    """Card and row titles: like the subheadline (Segoe UI, PTA blue)."""
    figure_pt: float = 32
    statement_pt: float = 24
    kicker_pt: float = 12
    kicker_left: int = cm(1.33)
    kicker_top: int = cm(1.60)
    kicker_color: str = colors.DARK_BLUE
    tag_pt: float = 12
    code_pt: float = CODE_SIZE_PT
    code_line_spacing: float = 1.30
    gap: int = cm(0.40)
    """Between blocks; half of it on a shrunk slide."""
    pad: int = cm(0.30)
    row_pad: int = cm(0.15)
    max_cards_per_row: int = 4
    card_line: str = colors.GREY_LIGHT
    card_line_pt: float = 0.75
    rule: str = colors.GREY_LIGHT
    closing_rule: str = colors.TEXT_SLIDES
    rule_pt: float = 0.5
    surface: str = colors.GREY_LIGHT
    """Panels, alerts and code."""
    dark_surface: str = colors.DARK_BLUE
    alert_bar: int = cm(0.15)
    note_bar: str = colors.PTA_BLUE
    important_bar: str = colors.YELLOW
    tag_line: str = colors.PTA_BLUE
    tag_line_pt: float = 0.75
    chip_pad_x: int = cm(0.18)
    chip_pad_y: int = cm(0.06)
    chip_gap: int = cm(0.18)
    highlight: str = colors.YELLOW
    """``==mark==`` and marked table rows."""
    min_visual_height: int = cm(4.76)
    """Images on a flow slide get at least this height (a quarter of the slide)."""
    shrink_steps: tuple[float, ...] = (1.0, 0.875, 0.75)
    """Flow slides shrink all sizes by an eighth, twice (DocLibs), never below 12 pt."""


FLOW: Final = FlowStyle()


@dataclass(frozen=True)
class ConclusionStyle:
    """The conclusion box (Fazit-Box) of the template collection, slide 43."""

    area: Area = Area(cm(1.33), cm(15.78), cm(31.20), cm(1.94))
    fill: str = colors.DARK_BLUE
    color: str = colors.WHITE
    sizes_pt: tuple[float, ...] = (18, 16, 14)
    """18 pt bold; shrunk to 14 pt at most to stay within ``max_lines``."""
    max_lines: int = 2
    inset_left: int = 684000
    inset_right: int = 180000
    inset_y: int = 72000


CONCLUSION: Final = ConclusionStyle()


@dataclass(frozen=True)
class CommentStyle:
    """The comment box (Kommentarbox) of the template collection, slide 32: a speech bubble."""

    fill: str = colors.WHITE
    line_from: str = colors.LIGHT_BLUE
    line_to: str = colors.PTA_BLUE
    line_pt: float = 1.5
    size_pt: float = 14
    color: str = colors.PTA_BLUE
    inset_x: int = cm(0.30)
    inset_y: int = cm(0.20)
    max_share: float = 0.5
    """At most half the width it is placed in."""


COMMENT: Final = CommentStyle()

DARK_BACKGROUND_LAYOUT: Final = LAYOUTS.title_plain
"""``## Title {.dark}``: ``Nur Titel`` with the background of this layout, text in white."""

QUOTE_SOURCE_FONT: Final = BODY_FONT
