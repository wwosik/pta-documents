"""E03-S05: the authoring guide of the DOCX generator (port of the cases of DocLibs
``AuthoringGuideTests``: the examples generate, under 2 500 words, names every key and every
piece of syntax, the renderers' sections only with the renderers, compared with
``samples/authoring-guide.expected.md``)."""

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
from pta_documents.design.colors import StatusCategory
from pta_documents.design.variants import Language, Marking, WordVariant
from pta_documents.diagrams.mermaid import MermaidRenderer
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.common import authoring_guides, heading_attributes, layout_syntax
from pta_documents.generation.common.renderers import CodeBlockGraphic, CodeBlockRequest
from pta_documents.generation.docx import guide
from pta_documents.generation.docx.generator import VALID_KEYS, DocxGenerator
from pta_documents.generation.docx.options import DocxOptions
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

EXPECTED: Final = Path(__file__).parent / "samples" / "authoring-guide.expected.md"
HEADINGS: Final = (
    "## Ein PTA-Word-Dokument aus Markdown",
    "## Gliederung",
    "## Inhalte",
    "## Folien-Syntax",
    "## Icons",
    "## Typografie und Code",
    "## Charts",
    "## Diagramme",
    "## Front Matter",
    "## Wenn etwas falsch ist",
    "### Hinweise",
    "## Beispiel",
)
IMAGE: Final = re.compile(r"!\[[^\]]*\]\((?!qr:)([^)\s]+)")


@dataclass(frozen=True)
class Converter:
    """An image converter that only names its format (the guide lists it)."""

    format: str | None

    def convert(self, image: object, scale: float) -> None:
        return None


@dataclass(frozen=True)
class Described:
    """A renderer with a section of its own and no graphic."""

    authoring_guide: str | None

    def render(self, request: CodeBlockRequest) -> CodeBlockGraphic | None:
        return None


def full_options(**changes: object) -> DocxOptions:
    """Every renderer of the library and an SVG converter, whatever is set up here."""
    return DocxOptions(
        code_block_renderers=(ChartRenderer(), MermaidRenderer()),
        image_converters=(Converter("SVG"),),
        **changes,  # type: ignore[arg-type]
    )


def full_guide() -> str:
    return DocxGenerator().authoring_guide(full_options())


def png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (800, 400), (0, 111, 185)).save(buffer, "PNG", dpi=(96, 96))
    return buffer.getvalue()


def generate_in(variant: WordVariant) -> Callable[[str], None]:
    """Generate an example in ``variant`` without notes, with a picture for every image path;
    a Mermaid example only where mermaid-cli draws. An example without front matter is a part of
    a document: it gets a title, which the templates with a cover need."""

    def generate(markdown: str) -> None:
        if not drawable(markdown):
            return
        if not markdown.startswith("---\n"):
            markdown = f"---\n{Keys.TITLE}: Beispiel\n---\n# Kapitel\n\n{markdown}"
        resources = tuple(
            DocumentResource(path, "image/png", png()) for path in set(IMAGE.findall(markdown))
        )
        result = DocxGenerator().generate(
            MarkdownDocument(markdown, resources), io.BytesIO(), DocxOptions(variant=variant)
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


def test_the_guide_matches_the_expected_file() -> None:
    assert_matches_expected(EXPECTED, full_guide())


def test_the_guide_stays_under_the_word_limit() -> None:
    assert_under(full_guide())
    assert_under(DocxGenerator().authoring_guide())


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


def test_every_template_has_its_sentence_and_the_options_choose_the_defaults() -> None:
    assert set(guide.VARIANT_TEXTS) == set(WordVariant)
    text = DocxGenerator().authoring_guide(
        DocxOptions(
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
    for variant in WordVariant:
        line = next(line for line in text.splitlines() if line.startswith(f"- `{variant.value}`"))
        assert ("`titel:` ist Pflicht" in line) is variant.has_cover, line


def test_the_renderers_sections_come_with_the_renderers() -> None:
    without = DocxGenerator().authoring_guide(DocxOptions(code_block_renderers=()))
    assert "## Charts" not in without and "```chart" not in without
    own = Described("## Testdiagramme\n\nBlöcke `test` werden gezeichnet.\n")
    with_own = DocxGenerator().authoring_guide(DocxOptions(code_block_renderers=(own,)))
    assert "\n## Testdiagramme\n\nBlöcke `test` werden gezeichnet.\n\n## Front Matter\n" in with_own
    assert "## Diagramme" in full_guide()


def test_the_image_formats_come_from_the_converters() -> None:
    assert "Bildformate: PNG, JPEG, GIF, BMP, TIFF, SVG." in full_guide()
    without = DocxGenerator().authoring_guide(DocxOptions(image_converters=()))
    assert "Bildformate: PNG, JPEG, GIF, BMP, TIFF." in without


# ---------------------------------------------------------------------- the mistakes it names


@pytest.mark.parametrize(
    ("markdown", "options", "message"),
    [
        ("---\nvorlage: hoch\n---\n# A\n", DocxOptions(), "has a cover page and needs a title"),
        (
            "---\ntitel: T\n---\n# A\n\n::: karte\nx\n:::\n",
            DocxOptions(),
            "Unknown container '::: karte'. Valid containers: ",
        ),
        (
            "---\ntitel: T\n---\n# A\n\n![A](images/a.png)\n",
            DocxOptions(),
            "is not among the document's resources.",
        ),
        (
            "---\ntitel: T\n---\n# A\n\n![A](images/a.svg)\n",
            DocxOptions(image_converters=()),
            "DOCX takes PNG, JPEG, GIF, BMP and TIFF",
        ),
    ],
    ids=["no-title", "container", "missing-image", "image-format"],
)
def test_the_mistakes_of_the_guide_are_the_generators_errors(
    markdown: str, options: DocxOptions, message: str
) -> None:
    resources = (
        (DocumentResource("images/a.svg", "image/svg+xml", b"<svg/>"),)
        if "a.svg" in markdown
        else ()
    )
    with pytest.raises(DocumentConversionError) as error:
        DocxGenerator().generate(MarkdownDocument(markdown, resources), io.BytesIO(), options)
    assert message in error.value.reason
    mistakes = full_guide().partition("## Wenn etwas falsch ist")[2].partition("### Hinweise")[0]
    assert message in mistakes
