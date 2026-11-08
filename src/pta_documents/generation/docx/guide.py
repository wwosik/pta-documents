"""The authoring guide of the DOCX generator (E03-S05): the guide „Dokumente“
(``generation.common.document_guide``, shared with the PDF since E05-S05) with Word's own
texts — from the same options as ``generate``."""

from __future__ import annotations

from typing import Final

from pta_documents.errors import DocumentFormat
from pta_documents.generation.common import document_guide
from pta_documents.generation.common.authoring_guides import GuideKey
from pta_documents.generation.common.document_guide import (
    FRONT_MATTER_EXAMPLE,
    VARIANT_TEXTS,
    FormatTexts,
    variants_paragraph,
)
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.docx.writer import SUPPORTED_IMAGES

__all__ = [
    "EFFECT",
    "FORMAT",
    "FRONT_MATTER_EXAMPLE",
    "NATIVE_IMAGES",
    "TEXTS",
    "VARIANT_TEXTS",
    "authoring_guide",
    "front_matter_rows",
    "variants_paragraph",
]

FORMAT: Final = DocumentFormat.DOCX

NATIVE_IMAGES: Final = tuple(t.partition("/")[2].upper() for t in SUPPORTED_IMAGES)
"""The image formats Word places as they are: ``PNG``, ``JPEG`` …"""

EFFECT: Final = (
    "Word zeigt sie schlicht: der Inhalt eines Containers nacheinander, `###` darin fett; "
    "Fazit, Kommentar und Alerts als Hinweisabsatz mit fetter Art („Fazit:“), `==…==` gelb, "
    "farbige Wörter und Status-Labels in der Statusfarbe. Zeitstrahl, Schrittfolge und "
    "Risikomatrix werden ein Bild, der Projektplan eine Tabelle."
)
"""How Word shows the slide syntax (E03-S03, E15-S01, E15-S02)."""

TEXTS: Final = FormatTexts(
    format=FORMAT,
    heading="Ein PTA-Word-Dokument aus Markdown",
    target="In Word",
    footnote="Word-Fußnote",
    links="| `[PTA](https://pta.de)` | Link; relative Links bleiben Text |",
    native_images=NATIVE_IMAGES,
    image_error="DOCX takes PNG, JPEG, GIF, BMP and TIFF",
    effect=EFFECT,
    toc="Ein Inhaltsverzeichnis vor Kapitel 1; Word füllt es beim Öffnen.",
)
"""Word's own parts of the guide „Dokumente“."""


def front_matter_rows(options: DocxOptions) -> list[GuideKey]:
    """A row for every key of ``generator.VALID_KEYS``, with the defaults of ``options``."""
    from pta_documents.generation.docx.generator import VALID_KEYS

    return document_guide.front_matter_rows(options, TEXTS, VALID_KEYS)


def authoring_guide(options: DocxOptions) -> str:
    """The guide for ``options`` (see ``DocxGenerator.authoring_guide``)."""
    from pta_documents.generation.docx.generator import VALID_KEYS

    return document_guide.authoring_guide(options, TEXTS, VALID_KEYS)
