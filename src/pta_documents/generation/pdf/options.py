"""Options of the PDF generator; the front matter overrides them."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from pta_documents.design.variants import DEFAULT_WORD_VARIANT, Language, WordVariant
from pta_documents.generation.common.images import ImageConverter, default_converters
from pta_documents.generation.common.renderers import CodeBlockRenderer, default_renderers


@dataclass(frozen=True)
class PdfOptions:
    variant: WordVariant = DEFAULT_WORD_VARIANT
    """``vorlage:`` — the PDF follows the PTA Word template of the same name (orientation,
    cover)."""
    language: Language = Language.DE
    """``sprache:``: generated texts and the document language (``/Lang``, ``dc:language``)."""
    typography: bool = True
    """``typografie:``: German (or English) typography on the text, as in Word
    (``markdown.typography``)."""
    highlight: bool = True
    """``syntaxhervorhebung:``: code blocks with a known language in the PTA colours."""
    date: dt.date | None = None
    """``datum:``: shown on the cover and in the footer; without it the footer shows the day of
    ``created`` (or today)."""
    company: str | None = None
    """``firma:``: the company of the footer in place of „PTA IT-Beratung"."""
    toc: bool = False
    """``inhaltsverzeichnis: ja``: a table of contents after the cover."""
    replace_unsupported: bool = True
    """Characters the fonts lack are replaced (E05-S04); PDF/A allows no ``.notdef``."""
    system_fonts: bool = True
    """Take Segoe UI, Consolas and Georgia from the system when installed
    (``design.fonts.resolve``); ``False`` always embeds the bundled fonts."""
    created: dt.datetime | None = None
    """The creation time in the metadata; None is now (UTC). Equal input and equal ``created``
    give byte-equal files."""
    code_block_renderers: tuple[CodeBlockRenderer, ...] = field(default_factory=default_renderers)
    """Asked in order for every fenced code block with an info string; the first graphic wins.
    Defaults to every renderer of the library that is available; ``()`` turns them off."""
    image_converters: tuple[ImageConverter, ...] = field(default_factory=default_converters)
    """Asked in order (scale 2) for every image that is not PNG, JPEG, GIF, BMP, TIFF or WebP.
    Defaults to every converter of the library that is available; ``()`` turns them off."""
