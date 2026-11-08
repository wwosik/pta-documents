"""Options of the PPTX generator; the front matter overrides them."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from pta_documents.design.slides import DEFAULT_TITLE_SLIDE
from pta_documents.design.variants import DEFAULT_SLIDES_VARIANT, Language, SlidesVariant
from pta_documents.generation.common.images import ImageConverter, default_converters
from pta_documents.generation.common.renderers import CodeBlockRenderer, default_renderers


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
    typography: bool = True
    """``typografie:``: German (or English) typography on the text — „quotes“, dashes,
    non-breaking spaces (``markdown.typography``); code, links and front matter stay as written."""
    highlight: bool = True
    """``syntaxhervorhebung:``: code blocks with a known language in the PTA colours."""
    code_block_renderers: tuple[CodeBlockRenderer, ...] = field(default_factory=default_renderers)
    """Asked in order for every fenced code block with an info string; the first graphic wins.
    Defaults to every renderer of the library that is available; ``()`` turns them off."""
    image_converters: tuple[ImageConverter, ...] = field(default_factory=default_converters)
    """Asked in order (scale 2) for every image in a format the generator does not take.
    Defaults to every converter of the library that is available; ``()`` turns them off."""
