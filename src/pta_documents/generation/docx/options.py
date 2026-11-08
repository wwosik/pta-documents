"""Options of the DOCX generator; the front matter overrides them."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from pta_documents.design.variants import DEFAULT_WORD_VARIANT, Language, WordVariant
from pta_documents.generation.common.images import ImageConverter, default_converters
from pta_documents.generation.common.renderers import CodeBlockRenderer, default_renderers


@dataclass(frozen=True)
class DocxOptions:
    variant: WordVariant = DEFAULT_WORD_VARIANT
    """``vorlage:`` in the front matter."""
    language: Language = Language.DE
    """``sprache:``: the language of generated texts (Seite/Page, Tabelle/Table …)."""
    date: dt.date | None = None
    """``datum:``: shown on the cover and in the footer; the footer falls back to today."""
    company: str | None = None
    """``firma:``: replaces the company line of the footer (template: "PTA IT-Beratung")."""
    toc: bool = False
    """``inhaltsverzeichnis: ja``: a table of contents after the cover."""
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
