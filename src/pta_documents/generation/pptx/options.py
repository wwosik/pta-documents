"""Options of the PPTX generator; the front matter overrides them."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from pta_documents.design.slides import DEFAULT_TITLE_SLIDE
from pta_documents.design.variants import DEFAULT_SLIDES_VARIANT, Language, SlidesVariant


@dataclass(frozen=True)
class PptxOptions:
    variant: SlidesVariant = DEFAULT_SLIDES_VARIANT
    """``vorlage:`` — ``basis`` or ``schulung``."""
    language: Language = Language.DE
    """``sprache:`` — ``en`` takes the English title slide and English generated texts."""
    footer: str | None = None
    """``fusszeile:`` — the footer reads "PTA – <footer>"; defaults to the presentation title."""
    title_slide: str = DEFAULT_TITLE_SLIDE
    """``titelfolie:`` — ``bild-01``, ``bild-02``, ``branchen`` or ``ohne-bild``."""
    date: dt.date | None = None
    """``datum:`` — shown on the title slide after author and location."""
    show_slide_numbers: bool = True
