"""Options of the DOCX generator; the front matter overrides them."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from pta_documents.design.variants import DEFAULT_WORD_VARIANT, Language, WordVariant


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
