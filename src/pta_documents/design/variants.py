"""The selectable variants of the PTA templates and the language of generated texts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from pta_documents.errors import DocumentConversionError, DocumentFormat


class Orientation(StrEnum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class Language(StrEnum):
    """The language of texts the generators write themselves (``sprache:`` in the front matter)."""

    DE = "de"
    EN = "en"

    @classmethod
    def parse(cls, value: str, format: DocumentFormat) -> Language:
        return _parse(cls, value, format, "sprache")


@dataclass(frozen=True)
class GeneratedTexts:
    """Words the generators write into documents."""

    page: str
    as_of: str
    table: str
    figure: str
    contents: str
    continued: str
    note: str = ""
    tip: str = ""
    important: str = ""
    warning: str = ""
    caution: str = ""
    conclusion: str = ""
    comment: str = ""

    def alert(self, kind: str) -> str:
        """The word an alert of ``kind`` (``NOTE`` …) starts with."""
        return str(getattr(self, kind.lower()))


TEXTS: Final = {
    Language.DE: GeneratedTexts(
        page="Seite",
        as_of="Stand",
        table="Tabelle",
        figure="Abbildung",
        contents="Inhalt",
        continued="(Forts.)",
        note="Hinweis",
        tip="Tipp",
        important="Wichtig",
        warning="Warnung",
        caution="Vorsicht",
        conclusion="Fazit",
        comment="Kommentar",
    ),
    Language.EN: GeneratedTexts(
        page="Page",
        as_of="As of",
        table="Table",
        figure="Figure",
        contents="Contents",
        continued="(cont.)",
        note="Note",
        tip="Tip",
        important="Important",
        warning="Warning",
        caution="Caution",
        conclusion="Conclusion",
        comment="Comment",
    ),
}


class WordVariant(StrEnum):
    """A PTA Word template; the value is the name used in the front matter (``vorlage:``)."""

    PORTRAIT = "hoch"
    PORTRAIT_NO_COVER = "hoch-ohne-deckblatt"
    LANDSCAPE = "quer"
    LANDSCAPE_NO_COVER = "quer-ohne-deckblatt"

    @classmethod
    def parse(cls, value: str) -> WordVariant:
        return _parse(cls, value, DocumentFormat.DOCX, "vorlage")

    @property
    def has_cover(self) -> bool:
        return self in (WordVariant.PORTRAIT, WordVariant.LANDSCAPE)

    @property
    def orientation(self) -> Orientation:
        if self in (WordVariant.PORTRAIT, WordVariant.PORTRAIT_NO_COVER):
            return Orientation.PORTRAIT
        return Orientation.LANDSCAPE

    @property
    def source_file(self) -> str:
        """The file in ``source-templates/`` the embedded template is prepared from."""
        return _WORD_SOURCES[self]

    @property
    def package_file(self) -> str:
        """The file name of the embedded template in ``pta_documents/design/templates/``."""
        return f"word-{self.value}.docx"


DEFAULT_WORD_VARIANT: Final = WordVariant.PORTRAIT

_WORD_SOURCES: Final = {
    WordVariant.PORTRAIT: "PTA-Dokument_Hochformat_mit-Deckblatt.dotx",
    WordVariant.PORTRAIT_NO_COVER: "PTA-Dokument_Hochformat_ohne-Deckblatt.dotx",
    WordVariant.LANDSCAPE: "PTA-Dokument_Querformat_mit-Deckblatt.dotx",
    WordVariant.LANDSCAPE_NO_COVER: "PTA-Dokument_Querformat_ohne-Deckblatt.dotx",
}


class SlidesVariant(StrEnum):
    """A PTA PowerPoint template; the value is the name used in the front matter."""

    BASIC = "basis"
    TRAINING = "schulung"

    @classmethod
    def parse(cls, value: str) -> SlidesVariant:
        return _parse(cls, value, DocumentFormat.PPTX, "vorlage")

    def package_file(self, language: Language) -> str:
        """The embedded template; English basic decks use the English title slide template."""
        if self is SlidesVariant.BASIC and language is Language.EN:
            return "slides-basis-en.pptx"
        return f"slides-{self.value}.pptx"


DEFAULT_SLIDES_VARIANT: Final = SlidesVariant.BASIC

SLIDES_SOURCES: Final = {
    "slides-basis.pptx": "PTA-Powerpoint-Basisvorlage.potx",
    "slides-schulung.pptx": "PTA-Powerpoint-Schulungsvorlage.potx",
    "slides-basis-en.pptx": "PTA-Powerpoint-Titelfolie EN.pptx",
}
"""Embedded slide template -> file in ``source-templates/``."""


def _parse[E: StrEnum](cls: type[E], value: str, format: DocumentFormat, key: str) -> E:
    wanted = value.strip().lower()
    for member in cls:
        if member.value == wanted:
            return member
    valid = ", ".join(member.value for member in cls)
    raise DocumentConversionError(
        format, f"Unknown value '{value}' for '{key}'. Valid values: {valid}."
    )
