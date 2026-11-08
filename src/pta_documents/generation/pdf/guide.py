"""The authoring guide of the PDF generator (E05-S05): the guide „Dokumente“
(``generation.common.document_guide``, shared with Word) with the PDF's own texts and a section
on the characters the embedded fonts lack — from the same options as ``generate``."""

from __future__ import annotations

from typing import Final

from pta_documents.design import fonts as design_fonts
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common import authoring_guides as guides
from pta_documents.generation.common import document_guide
from pta_documents.generation.common.document_guide import FormatTexts
from pta_documents.generation.common.result import NoteCodes
from pta_documents.generation.pdf.layout.fonts import CODE_FACES, TEXT_FACES, question_mark, shows
from pta_documents.generation.pdf.layout.story import DIRECT_IMAGES, PILLOW_IMAGES
from pta_documents.generation.pdf.options import PdfOptions

FORMAT: Final = DocumentFormat.PDF

_NAMES: Final = {"webp": "WebP"}


def _name(content_type: str) -> str:
    subtype = content_type.partition("/")[2]
    return _NAMES.get(subtype, subtype.upper())


NATIVE_IMAGES: Final = tuple(_name(t) for t in (*DIRECT_IMAGES, *PILLOW_IMAGES))
"""The image formats the PDF places without a converter: ``PNG``, ``JPEG`` … ``WebP``."""

EFFECT: Final = (
    "Das PDF zeigt sie wie Word: der Inhalt eines Containers nacheinander, `###` darin fett; "
    "Fazit, Kommentar und Alerts als graue Box, `==…==` gelb, Statuswörter in ihrer Farbe. "
    "Zeitstrahl, Schrittfolge, Risikomatrix und Szene werden Vektorgrafiken, der Projektplan "
    "eine Tabelle."
)
"""How the PDF shows the slide syntax (E05-S02, E05-S04, E09-S04)."""

CHARACTERS_HEADING: Final = "## Zeichen"

INTRO: Final = "Den Schriften im PDF fehlen Emoji und viele Symbole;"
REPLACED: Final = {
    "question": f"ein fehlendes Zeichen wird `?` (Hinweis `{NoteCodes.CHARACTER_MISSING}`).",
    "hook": f"ein fehlendes Zeichen wird ersetzt (Hinweis `{NoteCodes.CHARACTER_MISSING}`).",
    "error": "ein fehlendes Zeichen ist ein Fehler, der es und die Schrift nennt.",
}
"""What happens to a character the fonts lack: the default ``question_mark``, another
``replace_unsupported`` or none (``None``)."""


def characters_intro(options: PdfOptions) -> str:
    """The paragraph before the table of symbols; it follows ``replace_unsupported``."""
    hook = options.replace_unsupported
    case = "error" if hook is None else "question" if hook is question_mark else "hook"
    return f"{INTRO} {REPLACED[case]}"


def characters(options: PdfOptions) -> str:
    """The section „Zeichen“: the ``SYMBOLS`` the fonts of ``options`` lack — the same fonts and
    the same rule as ``generate`` (``design.fonts.resolve``, ``layout.fonts.shows``)."""
    fonts = design_fonts.resolve(system_fonts=options.system_fonts)
    body = guides.characters_section(
        lambda c: shows(fonts, c, TEXT_FACES),
        lambda c: shows(fonts, c, CODE_FACES),
        characters_intro(options),
    )
    return f"{CHARACTERS_HEADING}\n\n{body}"


def texts(options: PdfOptions) -> FormatTexts:
    """The PDF's own parts of the guide „Dokumente“ for ``options``."""
    return FormatTexts(
        format=FORMAT,
        heading="Ein PTA-PDF aus Markdown",
        target="Im PDF",
        footnote="Fußnote am Seitenende",
        links=(
            "| `[PTA](https://pta.de)`, `[Lage](#lage)` | Link; `#…` springt zur Überschrift, "
            "andere relative Links bleiben Text |"
        ),
        native_images=NATIVE_IMAGES,
        image_error="PDF takes PNG, JPEG, GIF, BMP, TIFF and WebP",
        effect=EFFECT,
        toc="Ein Inhaltsverzeichnis mit Seitenzahlen vor Kapitel 1.",
        characters=characters(options),
    )


def authoring_guide(options: PdfOptions) -> str:
    """The guide for ``options`` (see ``PdfGenerator.authoring_guide``)."""
    from pta_documents.generation.pdf.generator import VALID_KEYS

    return document_guide.authoring_guide(options, texts(options), VALID_KEYS)
