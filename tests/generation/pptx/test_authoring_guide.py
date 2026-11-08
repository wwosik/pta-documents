"""E04-S06: the authoring guide of the PPTX generator (port of DocLibs
``Pptx.Tests/AuthoringGuideTests.cs`` with the helpers of E02-S05).

Everything the code lists — containers, alerts, heading attributes, block markers, front matter
keys, the layouts of the template, transitions, scene kinds, title slides, icons — has to be
named in the guide, so that new syntax without a mention fails here; every example of the guide
generates, as PPTX and as HTML deck (which follows this guide)."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Final

import pytest

from pta_documents.charts.renderer import ChartRenderer
from pta_documents.design import icons
from pta_documents.design import slides as design
from pta_documents.design.variants import Marking, SlidesVariant
from pta_documents.diagrams.mermaid import MermaidRenderer
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.common import authoring_guides as guides
from pta_documents.generation.common import heading_attributes, layout_syntax, scene
from pta_documents.generation.common.images import ImageConverter
from pta_documents.generation.common.renderers import CodeBlockRenderer
from pta_documents.generation.common.slide_transition import SlideTransition
from pta_documents.generation.html.generator import HtmlDeckGenerator
from pta_documents.generation.pptx import generator as pptx_generator
from pta_documents.generation.pptx import guide as pptx_guide
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import MarkdownDocument, block_markers
from pta_documents.markdown.front_matter import Keys
from pta_documents.svg.image_converter import SvgImageConverter
from tests.expected import assert_matches_expected
from tests.generation.guides import (
    assert_examples_generate,
    assert_names_everything,
    assert_under,
    examples,
)

SAMPLES: Final = Path(__file__).parent / "samples"
WORD_LIMIT: Final = 3500
"""The PPTX guide's budget: above ``guides.WORD_LIMIT``, since it names everything the decks can
do (the shared slide syntax, icons and the chart section alone take about 1 800 words)."""
VARIANTS: Final = tuple(SlidesVariant)


def fixed(
    variant: SlidesVariant,
    renderers: tuple[CodeBlockRenderer, ...] = (ChartRenderer(),),
    converters: tuple[ImageConverter, ...] = (SvgImageConverter(),),
) -> PptxOptions:
    """Options that do not depend on what is installed here: by default the chart renderer and
    the SVG converter, whatever the machine has."""
    return PptxOptions(variant=variant, code_block_renderers=renderers, image_converters=converters)


def guide(variant: SlidesVariant = SlidesVariant.BASIC) -> str:
    return PptxGenerator().authoring_guide(fixed(variant))


def section(text: str, heading: str) -> str:
    """The ``##`` section ``heading`` of ``text``, up to the next ``##`` outside a fence."""
    lines = text.split("\n")
    start = lines.index(f"## {heading}")
    fence = ""
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.startswith("```"):
            marks = line[: len(line) - len(line.lstrip("`"))]
            fence = "" if fence and marks == fence else fence or marks
        elif not fence and line.startswith("## "):
            return "\n".join(lines[start:i])
    return "\n".join(lines[start:])


def pptx(markdown: str, options: PptxOptions | None = None) -> object:
    return PptxGenerator().generate(MarkdownDocument(markdown), io.BytesIO(), options)


# ---------------------------------------------------------------------- examples and size


@pytest.mark.parametrize("variant", VARIANTS, ids=lambda v: v.value)
def test_every_example_generates(variant: SlidesVariant) -> None:
    options = fixed(variant)
    assert_examples_generate(
        PptxGenerator().authoring_guide(options), lambda md: pptx(md, options), at_least=4
    )


@pytest.mark.parametrize("variant", VARIANTS, ids=lambda v: v.value)
def test_every_example_generates_as_html_deck(variant: SlidesVariant) -> None:
    assert_examples_generate(
        guide(variant),
        lambda md: HtmlDeckGenerator().generate(MarkdownDocument(md), io.BytesIO()),
    )


@pytest.mark.parametrize("variant", VARIANTS, ids=lambda v: v.value)
def test_the_full_example_generates_without_notes(variant: SlidesVariant) -> None:
    example = examples(section(guide(variant), "Beispiel"))
    assert len(example) == 1
    output = io.BytesIO()
    result = PptxGenerator().generate(MarkdownDocument(example[0]), output)
    assert result.notes == ()
    assert result.slides is not None and result.slides >= 6


def test_the_guide_starts_at_level_two_and_stays_within_its_budget() -> None:
    every_renderer = (ChartRenderer(), MermaidRenderer())
    text = PptxGenerator().authoring_guide(fixed(SlidesVariant.TRAINING, every_renderer))
    assert text.startswith("## ")
    assert "\n# " not in text.split("````markdown")[0]
    assert_under(text, WORD_LIMIT)


def test_the_default_options_give_a_guide() -> None:
    text = PptxGenerator().authoring_guide()
    assert text.startswith("## Eine PTA-Präsentation aus Markdown")
    assert "`basis` (Standard)" in text


# ---------------------------------------------------------------------- names everything


def test_the_guide_names_every_container_alert_attribute_and_marker() -> None:
    text = guide()
    assert_names_everything(text, (f"::: {name}" for name in layout_syntax.CONTAINER_NAMES))
    assert_names_everything(text, (f"[!{kind}]" for kind in layout_syntax.ALERT_KINDS))
    attributes = [e.strip() for e in heading_attributes.VALID.split(",")]
    assert_names_everything(
        text, (f"{{{e}" for e in attributes if e.startswith(".") and e != ".appendix")
    )
    assert_names_everything(text, ("kicker=", "layout=", "uebergang=", "dauer=", "`.appendix`"))
    assert_names_everything(text, (f"{{.{name}}}" for name in block_markers.NAMES))
    assert_names_everything(text, (f"={e}" for e in block_markers.ENTRANCES))


def test_the_guide_has_a_row_for_every_valid_key() -> None:
    text = guide()
    assert guides.named_keys(text) == [*pptx_generator.VALID_KEYS, "status.<kategorie>"]


@pytest.mark.parametrize("variant", VARIANTS, ids=lambda v: v.value)
def test_the_guide_names_every_layout_of_the_template(variant: SlidesVariant) -> None:
    text = guide(variant)
    layouts = pptx_guide.layout_names(fixed(variant))
    assert len(layouts) == 35
    assert_names_everything(section(text, "Vorlagenlayouts"), (f"„{name}“" for name in layouts))


def test_the_guide_names_every_value_the_deck_takes() -> None:
    text = guide()
    assert_names_everything(text, (f"`{t.value}`" for t in SlideTransition))
    assert_names_everything(text, (f"`{name}`" for name in design.TITLE_SLIDES))
    assert_names_everything(text, (f"`{kind.value}`" for kind in scene.ShapeKind))
    assert_names_everything(text, (f"`{name}`" for name in icons.ICONS))
    assert_names_everything(text, (f"`{m.value}`" for m in Marking))
    assert_names_everything(text, ("(qr:", "{focus=", "{fit=contain}", "{.round}", "{.grey}"))
    assert_names_everything(text, ("--html", Keys.PROGRESS, Keys.CHAPTERS))


# ---------------------------------------------------------------------- made from the options


def row(text: str, key: str) -> list[str]:
    """The cells of the front matter row of ``key``."""
    line = next(line for line in text.split("\n") if line.startswith(f"| `{key}` |"))
    return [cell.strip() for cell in line.strip("|").split("|")]


def test_the_marking_and_its_default_follow_the_template() -> None:
    basis = row(guide(SlidesVariant.BASIC), Keys.MARKING)
    training = row(guide(SlidesVariant.TRAINING), Keys.MARKING)
    assert basis[1] == "`vertraulich`, `intern`, `entwurf`, `kein` (Standard)"
    assert training[1] == "`vertraulich`, `intern` (Standard), `entwurf`"
    assert "`kein` ist dort ein Fehler" in training[2]
    assert row(guide(SlidesVariant.TRAINING), Keys.TEMPLATE)[1] == "`basis`, `schulung` (Standard)"


def test_the_diagrams_come_from_the_renderers() -> None:
    without = PptxGenerator().authoring_guide(fixed(SlidesVariant.BASIC, ()))
    assert "```chart" not in without and "## Charts" not in without
    charts = guide()
    assert "```chart" in charts and "```mermaid" not in charts
    every = PptxGenerator().authoring_guide(
        fixed(SlidesVariant.BASIC, (ChartRenderer(), MermaidRenderer()))
    )
    assert "```mermaid" in every


def test_the_image_formats_come_from_the_converters() -> None:
    assert "Bildformate: PNG, JPEG, SVG," in guide()
    plain = PptxGenerator().authoring_guide(fixed(SlidesVariant.BASIC, converters=()))
    assert "Bildformate: PNG, JPEG," in plain


@pytest.mark.parametrize("variant", VARIANTS, ids=lambda v: v.value)
def test_the_guide_matches_the_expected_file(variant: SlidesVariant) -> None:
    assert_matches_expected(
        SAMPLES / f"authoring-guide-{variant.value}.expected.md", guide(variant)
    )


# ---------------------------------------------------------------------- the mistakes it names


MISTAKES: Final = {
    "content under a chapter": "# Deck\n\n# Kapitel\n\nText\n\n## Folie\n\nText\n",
    "content under the closing": "# Deck\n\n## Folie\n\nText\n\n# Danke {.closing}\n\nText\n",
    "unknown container": "# Deck\n\n## Folie\n\n::: card\nText\n:::\n",
    "unknown alert": "# Deck\n\n## Folie\n\n> [!INFO]\n> Text\n",
    "unknown attribute": "# Deck\n\n## Folie {.darkk}\n\nText\n",
    "unknown icon": "# Deck\n\n## Folie\n\n- :icon-rakete: Start\n",
    "card without a bold start": "# Deck\n\n## Folie\n\n::: cards\n- Titel – Text\n:::\n",
    "conclusion with a table": "# Deck\n\n## Folie\n\n::: conclusion\n"
    + "| a | b |\n| - | - |\n| 1 | 2 |\n:::\n",
    "conclusion too long": "# Deck\n\n## Folie\n\nText\n\n::: conclusion\n"
    + "Ein langer Satz mit vielen Wörtern, der nicht in zwei Zeilen der Fazit-Box passt. " * 6
    + "\n:::\n",
    "agenda too long": "# Deck\n\n## Agenda {.agenda}\n\n"
    + "".join(f"- Punkt {n}\n" for n in range(1, design.AGENDA_ITEMS + 2)),
    "unknown layout": '# Deck\n\n## Folie {layout="Titel und Text zweispaltig"}\n\nText\n',
    "icon in text": "# Deck\n\n## Folie\n\nEin :icon-rocket: im Text.\n",
}
"""What the section „Wenn etwas falsch ist“ names: each is an error."""


@pytest.mark.parametrize("markdown", MISTAKES.values(), ids=list(MISTAKES))
def test_the_mistakes_the_guide_names_are_errors(markdown: str) -> None:
    with pytest.raises(DocumentConversionError):
        pptx(markdown)


def test_the_mistakes_are_in_the_guide() -> None:
    mistakes = section(guide(), "Wenn etwas falsch ist")
    assert_names_everything(
        mistakes,
        (
            "`# Kapitel`",
            "{.closing}",
            "::: card`",
            "[!INFO]",
            "{.darkk}",
            ":icon-rakete:",
            "ohne fetten Anfang",
            "Fazit-Box",
            f"mehr als {design.AGENDA_ITEMS} Punkten",
            "Titel und Text zweispaltig",
            "Fließtext",
        ),
    )
