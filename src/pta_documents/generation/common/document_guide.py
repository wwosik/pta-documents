"""The authoring guide „Dokumente“ of Word and the PDF (E03-S05, E05-S05): German Markdown from
``##`` for whoever writes a PTA report, from one template (``authoring_guide/documents.md``) and
the shared sections of ``authoring_guides``.

Both formats take the same Markdown and the same front matter and show it in the design of the
Word template, so they share the text (decision 2026-11-07: one guide for documents). What
differs — the name of the format, the footnotes, links, the table of contents, the image
formats, how the slide syntax looks, the notes and the characters the PDF fonts lack — comes in
a ``FormatTexts`` from the generator's own guide module (``docx.guide``, ``pdf.guide``)."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass, replace
from typing import Final, Protocol

from pta_documents.design.variants import Language, Marking, WordVariant
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common import authoring_guides as guides
from pta_documents.generation.common.audience import Audience
from pta_documents.generation.common.authoring_guides import GuideKey, choices
from pta_documents.generation.common.images import ImageConverter
from pta_documents.generation.common.renderers import CodeBlockRenderer
from pta_documents.markdown.front_matter import NO, YES, Keys

PACKAGE: Final = "pta_documents.generation.common"
TEMPLATE: Final = "documents"

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

FRONT_MATTER_EXAMPLE: Final = (
    "titel: Netzausbau 2027\nuntertitel: Zwischenbericht\nautor: Erika Mustermann\n"
    "datum: 2026-05-15\nvorlage: quer"
)


class DocumentOptions(Protocol):
    """What the guide reads from ``DocxOptions`` and ``PdfOptions``."""

    @property
    def variant(self) -> WordVariant: ...
    @property
    def language(self) -> Language: ...
    @property
    def typography(self) -> bool: ...
    @property
    def highlight(self) -> bool: ...
    @property
    def toc(self) -> bool: ...
    @property
    def marking(self) -> Marking: ...
    @property
    def audience(self) -> Audience | None: ...
    @property
    def image_converters(self) -> tuple[ImageConverter, ...]: ...
    @property
    def code_block_renderers(self) -> tuple[CodeBlockRenderer, ...]: ...


@dataclass(frozen=True, slots=True)
class FormatTexts:
    """The parts of the guide that are the format's own."""

    format: DocumentFormat
    heading: str
    """The first heading, without ``## ``: „Ein PTA-Word-Dokument aus Markdown“."""
    target: str
    """The head of the second column of the table „Inhalte“: „In Word“."""
    footnote: str
    """What a footnote becomes."""
    links: str
    """The row of the table „Inhalte“ on links, a whole table row."""
    native_images: tuple[str, ...]
    """The image formats the format places as they are (``PNG`` …)."""
    image_error: str
    """The part of the error on an image format without a converter that the guide quotes."""
    effect: str
    """How the format shows the slide syntax (``layout_syntax_section``)."""
    toc: str
    """What ``inhaltsverzeichnis: ja`` does."""
    characters: str = ""
    """The section on characters the fonts lack; empty where the installed font is taken."""


def variants_paragraph(default: WordVariant) -> str:
    """„`vorlage:` wählt …“ with a line per template."""
    lines = [f"`{Keys.TEMPLATE}:` wählt die PTA-Vorlage:", ""]
    for variant in WordVariant:
        marked = " (Standard)" if variant is default else ""
        must = f"; `{Keys.TITLE}:` ist Pflicht" if variant.has_cover else ""
        lines.append(f"- `{variant.value}`{marked}: {VARIANT_TEXTS[variant]}{must}.")
    return "\n".join(lines) + "\n"


def front_matter_rows(
    options: DocumentOptions, texts: FormatTexts, valid_keys: Collection[str]
) -> list[GuideKey]:
    """A row for every key of ``valid_keys``, with the defaults of ``options``."""

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
        GuideKey(Keys.TOC, yes_no(options.toc), texts.toc),
        GuideKey(
            Keys.MARKING,
            choices((m.value for m in Marking), options.marking.value),
            "Text unter dem Logo jeder Seite und auf dem Deckblatt; `entwurf` dazu das "
            "Wasserzeichen „ENTWURF“.",
        ),
    )
    rows = {row.key: row for row in own} | common
    return [rows[key] for key in valid_keys]


def authoring_guide(
    options: DocumentOptions, texts: FormatTexts, valid_keys: Collection[str]
) -> str:
    """The guide of ``texts.format`` for ``options``; ``valid_keys`` are the generator's."""
    return guides.fill(
        guides.template(PACKAGE, TEMPLATE),
        {
            "heading": texts.heading,
            "variants": variants_paragraph(options.variant),
            "target": texts.target,
            "footnote": texts.footnote,
            "links": texts.links,
            "imageFormats": ", ".join(
                guides.image_formats(texts.native_images, options.image_converters)
            ),
            "syntax": guides.layout_syntax_section(texts.format, texts.effect),
            "icons": guides.icons_section(texts.format),
            "typography": guides.typography_section(),
            "characters": texts.characters,
            "diagrams": guides.renderers_section(options.code_block_renderers),
            "frontMatter": guides.front_matter_section(
                front_matter_rows(options, texts, valid_keys), valid_keys, FRONT_MATTER_EXAMPLE
            ),
            "imageError": texts.image_error,
            # Under „Wenn etwas falsch ist“: what comes back is the writer's to fix, too.
            "notes": guides.notes_section(texts.format).replace("## ", "### ", 1),
        },
    )
