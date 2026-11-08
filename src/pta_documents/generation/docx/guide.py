"""The authoring guide of the DOCX generator (E03-S05): German Markdown from ``##`` for whoever
writes a PTA Word document, filled from the template ``authoring_guide/docx.md`` and the shared
sections of ``generation.common.authoring_guides`` — from the same options as ``generate``."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Final

from pta_documents.design.variants import Language, Marking, WordVariant
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common import authoring_guides as guides
from pta_documents.generation.common.audience import Audience
from pta_documents.generation.common.authoring_guides import GuideKey, choices
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.docx.writer import SUPPORTED_IMAGES
from pta_documents.markdown.front_matter import NO, YES, Keys

FORMAT: Final = DocumentFormat.DOCX
PACKAGE: Final = "pta_documents.generation.docx"
TEMPLATE: Final = "docx"

NATIVE_IMAGES: Final = tuple(t.partition("/")[2].upper() for t in SUPPORTED_IMAGES)
"""The image formats Word places as they are: ``PNG``, ``JPEG`` …"""

VARIANT_TEXTS: Final[Mapping[WordVariant, str]] = {
    WordVariant.PORTRAIT: "Hochformat mit Deckblatt",
    WordVariant.PORTRAIT_NO_COVER: (
        "Hochformat ohne Deckblatt; Titel und Untertitel in der Kopfzeile"
    ),
    WordVariant.LANDSCAPE: "Querformat mit Deckblatt",
    WordVariant.LANDSCAPE_NO_COVER: (
        "Querformat ohne Deckblatt; Titel und Untertitel in der Kopfzeile"
    ),
}
"""One sentence on each template of ``WordVariant``."""

EFFECT: Final = (
    "Word zeigt sie schlicht: der Inhalt eines Containers nacheinander, `###` darin fett; "
    "Fazit, Kommentar und Alerts als Hinweisabsatz mit fetter Art („Fazit:“), `==…==` gelb, "
    "farbige Wörter und Status-Labels in der Statusfarbe. Zeitstrahl, Schrittfolge und "
    "Risikomatrix werden ein Bild, der Projektplan eine Tabelle."
)
"""How Word shows the slide syntax (E03-S03, E15-S01, E15-S02)."""

FRONT_MATTER_EXAMPLE: Final = (
    "titel: Netzausbau 2027\nuntertitel: Zwischenbericht\nautor: Erika Mustermann\n"
    "datum: 2026-05-15\nvorlage: quer"
)


def variants_paragraph(default: WordVariant) -> str:
    """„`vorlage:` wählt …“ with a line per template."""
    lines = [f"`{Keys.TEMPLATE}:` wählt die PTA-Vorlage:", ""]
    for variant in WordVariant:
        marked = " (Standard)" if variant is default else ""
        must = f"; `{Keys.TITLE}:` ist Pflicht" if variant.has_cover else ""
        lines.append(f"- `{variant.value}`{marked}: {VARIANT_TEXTS[variant]}{must}.")
    return "\n".join(lines) + "\n"


def front_matter_rows(options: DocxOptions) -> list[GuideKey]:
    """A row for every key of ``generator.VALID_KEYS``, with the defaults of ``options``."""
    from pta_documents.generation.docx.generator import VALID_KEYS

    def yes_no(value: bool) -> str:
        return choices((YES, NO), YES if value else NO)

    common = guides.common_keys(options.audience or Audience.KUNDE)
    common[Keys.LANGUAGE] = replace(
        common[Keys.LANGUAGE], values=choices((v.value for v in Language), options.language.value)
    )
    common[Keys.TYPOGRAPHY] = replace(common[Keys.TYPOGRAPHY], values=yes_no(options.typography))
    common[Keys.HIGHLIGHT] = replace(common[Keys.HIGHLIGHT], values=yes_no(options.highlight))
    own = (
        GuideKey(
            Keys.TEMPLATE,
            choices((v.value for v in WordVariant), options.variant.value),
            "Die PTA-Vorlage, siehe oben.",
        ),
        GuideKey(Keys.TITLE, "Text", "Der Titel auf dem Deckblatt und in der Kopfzeile."),
        GuideKey(Keys.SUBTITLE, "Text", "Die Zeile unter dem Titel."),
        GuideKey(Keys.AUTHOR, "Text", "„Autor, Ort, Datum“ auf dem Deckblatt."),
        GuideKey(Keys.LOCATION, "Text", "Der Ort darin."),
        GuideKey(Keys.COMPANY, "Text", "Ersetzt „PTA IT-Beratung“ in der Fußzeile."),
        GuideKey(
            Keys.TOC,
            yes_no(options.toc),
            "Ein Inhaltsverzeichnis vor Kapitel 1; Word füllt es beim Öffnen.",
        ),
        GuideKey(
            Keys.MARKING,
            choices((m.value for m in Marking), options.marking.value),
            "Text unter dem Logo jeder Seite und auf dem Deckblatt; `entwurf` dazu das "
            "Wasserzeichen „ENTWURF“.",
        ),
    )
    rows = {row.key: row for row in own} | common
    return [rows[key] for key in VALID_KEYS]


def authoring_guide(options: DocxOptions) -> str:
    """The guide for ``options`` (see ``DocxGenerator.authoring_guide``)."""
    from pta_documents.generation.docx.generator import VALID_KEYS

    return guides.fill(
        guides.template(PACKAGE, TEMPLATE),
        {
            "variants": variants_paragraph(options.variant),
            "imageFormats": ", ".join(
                guides.image_formats(NATIVE_IMAGES, options.image_converters)
            ),
            "syntax": guides.layout_syntax_section(FORMAT, EFFECT),
            "icons": guides.icons_section(FORMAT),
            "typography": guides.typography_section(),
            "diagrams": guides.renderers_section(options.code_block_renderers),
            "frontMatter": guides.front_matter_section(
                front_matter_rows(options), VALID_KEYS, FRONT_MATTER_EXAMPLE
            ),
            # Under „Wenn etwas falsch ist“: what comes back is the writer's to fix, too.
            "notes": guides.notes_section(FORMAT).replace("## ", "### ", 1),
        },
    )
