"""E05-S05: the authoring guide of the PDF generator — the guide „Dokumente“ with the PDF's own
parts (port of the cases of DocLibs ``AuthoringGuideTests``: the examples generate, under
2 500 words, names every key and every piece of syntax, the template default follows the
options, the section on characters follows the fonts and ``replace_unsupported``, every
replacement is in every font, compared with ``samples/authoring-guide.expected.md``)."""

from __future__ import annotations

import io
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest
from PIL import Image

from pta_documents.charts.renderer import ChartRenderer
from pta_documents.design import fonts as design_fonts
from pta_documents.design.colors import StatusCategory
from pta_documents.design.variants import Language, Marking, WordVariant
from pta_documents.diagrams.mermaid import MermaidRenderer
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.common import authoring_guides, heading_attributes, layout_syntax
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.pdf import PdfGenerator, PdfOptions, guide
from pta_documents.generation.pdf.generator import VALID_KEYS
from pta_documents.generation.pdf.layout.fonts import CODE_FACES, TEXT_FACES, shows
from pta_documents.markdown import DocumentResource, MarkdownDocument
from pta_documents.markdown.front_matter import Keys
from tests.diagrams.support import drawable
from tests.expected import assert_matches_expected
from tests.generation.guides import (
    assert_examples_generate,
    assert_names_everything,
    assert_under,
    examples,
)
from tests.generation.pdf.test_generator import CREATED

EXPECTED: Final = Path(__file__).parent / "samples" / "authoring-guide.expected.md"
HEADINGS: Final = (
    "## Ein PTA-PDF aus Markdown",
    "## Gliederung",
    "## Inhalte",
    "## Folien-Syntax",
    "## Icons",
    "## Typografie und Code",
    "## Zeichen",
    "## Charts",
    "## Diagramme",
    "## Front Matter",
    "## Wenn etwas falsch ist",
    "### Hinweise",
    "## Beispiel",
)
IMAGE: Final = re.compile(r"!\[[^\]]*\]\((?!qr:)([^)\s]+)")
ROW: Final = re.compile(r"^\| (?P<symbols>[^`|]+?) \| `(?P<instead>(?:\\\||[^`])+)` \|$", re.M)
"""A row of the table of the section „Zeichen“."""


@dataclass(frozen=True)
class Converter:
    """An image converter that only names its format (the guide lists it)."""

    format: str | None

    def convert(self, image: object, scale: float) -> None:
        return None


def full_options(**changes: object) -> PdfOptions:
    """Every renderer of the library, an SVG converter and the bundled fonts (Selawik,
    Inconsolata), whatever is set up or installed here."""
    return PdfOptions(
        code_block_renderers=(ChartRenderer(), MermaidRenderer()),
        image_converters=(Converter("SVG"),),
        system_fonts=False,
        **changes,  # type: ignore[arg-type]
    )


def full_guide() -> str:
    return PdfGenerator().authoring_guide(full_options())


def section(text: str, heading: str) -> str:
    """The section ``heading`` of ``text``, up to the next heading of its level or above."""
    rest = text.partition(f"\n{heading}\n")[2]
    level = heading.split(" ")[0]
    found = re.search(rf"^#{{1,{len(level)}}} ", rest, re.MULTILINE)
    return rest[: found.start()] if found else rest


def png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (800, 400), (0, 111, 185)).save(buffer, "PNG", dpi=(96, 96))
    return buffer.getvalue()


def generate_in(variant: WordVariant) -> Callable[[str], None]:
    """Generate an example as a PDF in ``variant`` without notes, with a picture for every image
    path; a Mermaid example only where mermaid-cli draws. An example without front matter is a
    part of a document: it gets a title, which the templates with a cover need."""

    def generate(markdown: str) -> None:
        if not drawable(markdown):
            return
        if not markdown.startswith("---\n"):
            markdown = f"---\n{Keys.TITLE}: Beispiel\n---\n# Kapitel\n\n{markdown}"
        resources = tuple(
            DocumentResource(path, "image/png", png()) for path in set(IMAGE.findall(markdown))
        )
        options = PdfOptions(variant=variant, created=CREATED, system_fonts=False)
        result = PdfGenerator().generate(
            MarkdownDocument(markdown, resources), io.BytesIO(), options
        )
        assert result.notes == (), str(result)

    return generate


# ---------------------------------------------------------------------- the guide


def test_the_guide_is_german_markdown_from_level_two_with_every_section() -> None:
    text = full_guide()
    assert text.startswith(HEADINGS[0] + "\n\n")
    prose = re.sub(r"^(`{3,}).*?^\1$", "", text, flags=re.MULTILINE | re.DOTALL)
    assert not re.search(r"^# ", prose, re.MULTILINE)
    positions = [text.find(f"\n{heading}\n") for heading in HEADINGS[1:]]
    assert all(p > 0 for p in positions), dict(zip(HEADINGS[1:], positions, strict=True))
    assert positions == sorted(positions)
    assert "{{" not in text and "\n\n\n" not in text and text.endswith("````\n")
    assert "Word füllt" not in text and "Word-Fußnote" not in text


def test_the_guide_matches_the_expected_file() -> None:
    assert_matches_expected(EXPECTED, full_guide())


def test_the_guide_stays_under_the_word_limit() -> None:
    assert_under(full_guide())
    assert_under(PdfGenerator().authoring_guide())
    assert_under(PdfGenerator().authoring_guide(full_options(replace_unsupported=None)))


@pytest.mark.parametrize("variant", list(WordVariant), ids=lambda v: v.value)
def test_every_example_generates_in_every_template(variant: WordVariant) -> None:
    text = full_guide()
    # front matter, chart, financial chart, Mermaid, the report
    assert len(examples(text)) == 5
    assert_examples_generate(text, generate_in(variant), at_least=5)


def test_the_guide_names_every_key_template_and_value() -> None:
    text = full_guide()
    assert_names_everything(text, [f"| `{key}` |" for key in VALID_KEYS])
    assert authoring_guides.named_keys(text) == [*VALID_KEYS, f"{Keys.STATUS_PREFIX}<kategorie>"]
    assert_names_everything(text, [f"- `{v.value}`" for v in WordVariant])
    assert_names_everything(text, [f"`{m.value}`" for m in Marking])
    assert_names_everything(text, [f"`{language.value}`" for language in Language])
    assert_names_everything(text, [f"`{c.value}`" for c in StatusCategory])


def test_the_guide_names_every_container_alert_and_attribute() -> None:
    text = full_guide()
    left_out = authoring_guides.LEFT_OUT_CONTAINERS[guide.FORMAT]
    assert_names_everything(
        text,
        [
            f"`{name}`" if name in left_out else f"`::: {name}`"
            for name in layout_syntax.CONTAINER_NAMES
        ],
    )
    assert_names_everything(text, [f"`> [!{kind}]`" for kind in layout_syntax.ALERT_KINDS])
    for entry in (e.strip() for e in heading_attributes.VALID.split(",")):
        written, _ = authoring_guides.ATTRIBUTE_TEXTS[entry]
        assert written in text or f"`{entry}`" in text, entry


def test_the_options_choose_the_defaults() -> None:
    text = PdfGenerator().authoring_guide(
        PdfOptions(
            variant=WordVariant.LANDSCAPE_NO_COVER,
            toc=True,
            marking=Marking.DRAFT,
            language=Language.EN,
            typography=False,
        )
    )
    assert "- `quer-ohne-deckblatt` (Standard): " in text
    assert "`hoch-ohne-deckblatt`, `quer`, `quer-ohne-deckblatt` (Standard) |" in text
    assert "| `inhaltsverzeichnis` | `ja` (Standard), `nein` |" in text
    assert "`entwurf` (Standard)" in text
    assert "| `sprache` | `de`, `en` (Standard) |" in text
    assert "| `typografie` | `ja`, `nein` (Standard) |" in text
    assert "- `hoch` (Standard): " in PdfGenerator().authoring_guide()


def test_the_renderers_sections_and_image_formats_come_with_the_options() -> None:
    without = PdfGenerator().authoring_guide(
        PdfOptions(code_block_renderers=(), image_converters=())
    )
    assert "## Charts" not in without and "```chart" not in without
    assert "Bildformate: PNG, JPEG, GIF, BMP, TIFF, WebP." in without
    assert "Bildformate: PNG, JPEG, GIF, BMP, TIFF, WebP, SVG." in full_guide()
    assert "## Diagramme" in full_guide()


def test_the_guide_is_the_word_guide_with_the_pdfs_own_parts() -> None:
    """One guide „Dokumente“ (decision 2026-11-07): the PDF guide names Word's syntax and beyond
    it only the transition in the row of the scene, which the PDF shows and Word leaves out."""
    pdf = authoring_guides.named_syntax(full_guide())
    word = authoring_guides.named_syntax(
        DocxGenerator().authoring_guide(
            DocxOptions(
                code_block_renderers=(ChartRenderer(), MermaidRenderer()),
                image_converters=(Converter("SVG"),),
            )
        )
    )
    assert set(pdf) - set(word) == {"{uebergang"}
    assert set(word) - set(pdf) == set()


# ---------------------------------------------------------------------- the characters


def named_symbols(text: str) -> dict[str, str]:
    """The symbols of the table of the section „Zeichen“, each with its replacement."""
    rows = section(text, "## Zeichen")
    return {
        symbol: m.group("instead").replace("\\|", "|")
        for m in ROW.finditer(rows)
        for symbol in m.group("symbols").split(" ")
    }


def test_the_characters_section_names_exactly_the_symbols_the_fonts_lack() -> None:
    fonts = design_fonts.resolve(system_fonts=False)
    lacking = [
        symbol
        for symbol, _ in authoring_guides.SYMBOLS
        if not (shows(fonts, ord(symbol), TEXT_FACES) and shows(fonts, ord(symbol), CODE_FACES))
    ]
    named = named_symbols(full_guide())
    assert lacking and sorted(named) == sorted(lacking)
    in_code = [s for s in lacking if shows(fonts, ord(s), CODE_FACES)]
    assert f"In Code gehen: {' '.join(in_code)}." in section(full_guide(), "## Zeichen")


def test_every_replacement_is_in_every_font() -> None:
    fonts = design_fonts.resolve(system_fonts=False)
    for symbol, instead in named_symbols(full_guide()).items():
        for char in instead:
            assert shows(fonts, ord(char), TEXT_FACES), (symbol, instead)
            assert shows(fonts, ord(char), CODE_FACES), (symbol, instead)


def test_with_fonts_that_have_every_symbol_the_section_has_no_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Everything:
        def has_glyph(self, code_point: int, face: object) -> bool:
            return True

    monkeypatch.setattr(guide.design_fonts, "resolve", lambda system_fonts: Everything())
    text = section(full_guide(), "## Zeichen")
    assert "| Vermeiden |" not in text and text.strip() == guide.characters_intro(full_options())


def test_the_characters_intro_follows_replace_unsupported() -> None:
    def intro(**changes: object) -> str:
        return section(PdfGenerator().authoring_guide(full_options(**changes)), "## Zeichen")

    assert "ein fehlendes Zeichen wird `?` (Hinweis `character-missing`)." in intro()
    assert "wird ersetzt (Hinweis" in intro(replace_unsupported=lambda _: "x")
    assert "ein fehlendes Zeichen ist ein Fehler" in intro(replace_unsupported=None)


# ---------------------------------------------------------------------- the mistakes it names


@pytest.mark.parametrize(
    ("markdown", "options", "message"),
    [
        ("---\nvorlage: hoch\n---\n# A\n", PdfOptions(), "has a cover page and needs a title"),
        (
            "---\ntitel: T\n---\n# A\n\n::: karte\nx\n:::\n",
            PdfOptions(),
            "Unknown container '::: karte'. Valid containers: ",
        ),
        (
            "---\ntitel: T\n---\n# A\n\n![A](images/a.png)\n",
            PdfOptions(),
            "is not among the document's resources.",
        ),
        (
            "---\ntitel: T\n---\n# A\n\n![A](images/a.svg)\n",
            PdfOptions(image_converters=()),
            "PDF takes PNG, JPEG, GIF, BMP, TIFF and WebP",
        ),
    ],
    ids=["no-title", "container", "missing-image", "image-format"],
)
def test_the_mistakes_of_the_guide_are_the_generators_errors(
    markdown: str, options: PdfOptions, message: str
) -> None:
    resources = (
        (DocumentResource("images/a.svg", "image/svg+xml", b"<svg/>"),)
        if "a.svg" in markdown
        else ()
    )
    with pytest.raises(DocumentConversionError) as error:
        PdfGenerator().generate(MarkdownDocument(markdown, resources), io.BytesIO(), options)
    assert message in error.value.reason
    assert message in section(full_guide(), "## Wenn etwas falsch ist")


def test_a_link_to_a_heading_as_the_guide_shows_it_works() -> None:
    import pikepdf

    markdown = "---\ntitel: T\n---\n# Lage\n\nText\n\n# Weiter\n\nSiehe [Lage](#lage).\n"
    output = io.BytesIO()
    PdfGenerator().generate(MarkdownDocument(markdown), output, PdfOptions(system_fonts=False))
    with pikepdf.open(io.BytesIO(output.getvalue())) as pdf:
        links = [
            annotation
            for page in pdf.pages
            for annotation in page.get("/Annots", [])
            if annotation.get("/Subtype") == "/Link"
        ]
    assert links and all("/URI" not in str(link.get("/A", {})) for link in links)
