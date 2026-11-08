"""Options of the HTML deck generator; the front matter overrides them."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from pta_documents.design.slides import DEFAULT_TITLE_SLIDE
from pta_documents.design.variants import DEFAULT_SLIDES_VARIANT, Language, Marking, SlidesVariant
from pta_documents.generation.common.audience import Audience
from pta_documents.generation.common.images import ImageConverter, default_converters
from pta_documents.generation.common.renderers import CodeBlockRenderer, default_renderers
from pta_documents.generation.common.slide_transition import SlideTransition
from pta_documents.generation.pptx.options import PptxOptions


@dataclass(frozen=True)
class HtmlDeckOptions:
    """The options of ``PptxOptions`` (the deck is the same) and two of the HTML deck's own."""

    variant: SlidesVariant = DEFAULT_SLIDES_VARIANT
    """``vorlage:`` — ``basis`` or ``schulung``."""
    language: Language = Language.DE
    """``sprache:`` — also the language of the page (``lang``) and of its key hint."""
    marking: Marking | None = None
    """``kennzeichnung:`` — as in PowerPoint."""
    audience: Audience | None = None
    """As in PowerPoint, the version (E16-S01): ``kunde``, ``intern`` or ``trainer``; it wins
    over ``fassung:`` in the front matter (``--audience``). None: ``fassung:``, else ``kunde``."""
    footer: str | None = None
    """``fusszeile:`` — the footer reads "PTA – <footer>"; defaults to the presentation title."""
    title_slide: str = DEFAULT_TITLE_SLIDE
    """``titelfolie:`` — ``bild-01``, ``bild-02``, ``branchen`` or ``ohne-bild``."""
    date: dt.date | None = None
    """``datum:`` — shown on the title slide after author and location."""
    show_slide_numbers: bool = True
    typography: bool = True
    """``typografie:`` — as in PowerPoint."""
    highlight: bool = True
    """``syntaxhervorhebung:`` — as in PowerPoint."""
    build_lists: bool = False
    """``aufbau: listen`` — every list appears item by item (E09-S02)."""
    transition: SlideTransition = SlideTransition.NONE
    """``uebergang:`` — how every slide comes in (E09-S03); ``morph`` fades in the browser."""
    show_progress: bool = True
    """``fortschritt:`` — a progress bar under the slide."""
    show_chapters: bool = True
    """``kapitelanzeige:`` — the chapters (``#`` headings) above the slide, the current marked."""
    code_block_renderers: tuple[CodeBlockRenderer, ...] = field(default_factory=default_renderers)
    """As in PowerPoint: asked in order for every fenced code block with an info string."""
    image_converters: tuple[ImageConverter, ...] = field(default_factory=default_converters)
    """As in PowerPoint: asked in order for every image in a format slides do not take."""

    def slides(self) -> PptxOptions:
        """The options of the PowerPoint deck the HTML deck shows."""
        return PptxOptions(
            variant=self.variant,
            language=self.language,
            marking=self.marking,
            audience=self.audience,
            footer=self.footer,
            title_slide=self.title_slide,
            date=self.date,
            show_slide_numbers=self.show_slide_numbers,
            typography=self.typography,
            highlight=self.highlight,
            build_lists=self.build_lists,
            transition=self.transition,
            code_block_renderers=self.code_block_renderers,
            image_converters=self.image_converters,
        )
