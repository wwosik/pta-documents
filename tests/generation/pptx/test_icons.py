"""E15-S03: icons on slides — the figure of a card and the bullets of a list."""

from __future__ import annotations

from typing import Final

import pytest
from lxml import etree

from pta_documents.conversions.pptx import PptxConverter
from pta_documents.design import colors
from pta_documents.design import slides as design
from pta_documents.design.icons import raster
from pta_documents.errors import DocumentConversionError
from tests.generation.pptx.conftest import generate, open_pptx
from tests.generation.pptx.test_schedule import deck, frame, groups

A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
R: Final = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CARDS: Final = """::: cards
### :icon-rocket: Start
Schnell los.

### :icon-shield: Sicherheit
Geprüft.
:::
"""
BULLETS: Final = "- :icon-check: Erledigt\n- :icon-clock: Offen\n- :icon-x: Verworfen\n"


def name(group: etree._Element) -> str:
    return str(group.find(f"{{{P}}}nvGrpSpPr/{{{P}}}cNvPr").get("name"))  # type: ignore[union-attr]


def strokes(group: etree._Element) -> set[str]:
    return {str(e.get("val")) for e in group.iter(f"{{{A}}}ln") for e in e.iter(f"{{{A}}}srgbClr")}


def tree(data: bytes, slide: int = 1) -> etree._Element:
    return open_pptx(data).slides[slide].shapes._spTree  # type: ignore[attr-defined, no-any-return]


def test_an_icon_before_a_card_title_is_the_cards_figure_in_pta_blue() -> None:
    data = generate(deck(CARDS))
    icons = [g for g in groups(data) if name(g).startswith("icon:")]
    assert [name(g) for g in icons] == ["icon:rocket", "icon:shield"]
    assert strokes(icons[0]) == {colors.PTA_BLUE}
    _, _, width, height = frame(icons[0])
    assert abs(width - design.FLOW.icon) <= 2 and abs(height - design.FLOW.icon) <= 2
    texts = [t.text for t in tree(data).iter(f"{{{A}}}t")]
    assert "Start" in texts and not any(":icon-" in (t or "") for t in texts)


def test_the_list_form_of_cards_takes_an_icon_too() -> None:
    body = "::: cards\n- :icon-users: **Team** – gemeinsam\n- :icon-bulb: **Idee** – neu\n:::\n"
    names = [name(g) for g in groups(generate(deck(body)))]
    assert names == ["icon:users", "icon:bulb"]


def test_on_a_dark_slide_the_figure_is_white() -> None:
    data = generate(f"# Deck\n\n## Plan {{.dark}}\n\n{CARDS}")
    icons = [g for g in groups(data) if name(g).startswith("icon:")]
    assert icons and all(strokes(g) == {colors.WHITE} for g in icons)


def test_an_icon_and_a_number_in_one_card_are_an_error() -> None:
    body = "::: cards\n### :icon-rocket: Start\n**26 %**\n\nText\n:::\n"
    with pytest.raises(DocumentConversionError, match="Line 6: A card has one figure"):
        generate(deck(body))


def test_icons_before_every_item_are_picture_bullets() -> None:
    data = generate(deck(BULLETS))
    slide = open_pptx(data).slides[1]
    paragraphs = [
        p for p in tree(data).iter(f"{{{A}}}p") if p.find(f"{{{A}}}pPr/{{{A}}}buBlip") is not None
    ]
    assert len(paragraphs) == 3
    texts = ["".join(t.text or "" for t in p.iter(f"{{{A}}}t")) for p in paragraphs]
    assert texts == ["Erledigt", "Offen", "Verworfen"]
    blip = paragraphs[0].find(f"{{{A}}}pPr/{{{A}}}buBlip/{{{A}}}blip")
    assert blip is not None
    part = slide.part.related_part(str(blip.get(f"{{{R}}}embed")))
    assert raster.name_of(part.blob) == "check"


def test_a_list_where_not_every_item_starts_with_an_icon_is_an_error_on_a_slide() -> None:
    with pytest.raises(DocumentConversionError, match="Line 5: Icons in slide text"):
        generate(deck("- :icon-check: Erledigt\n- Offen\n"))


@pytest.mark.parametrize(
    "body",
    [
        "Der Server :icon-server: läuft.\n",
        "| A | B |\n| - | - |\n| :icon-check: | x |\n",
        "Text\n\n::: notes\nSiehe :icon-check:\n:::\n",
    ],
    ids=["text", "table", "notes"],
)
def test_icons_in_slide_text_are_an_error_that_points_to_cards_and_lists(body: str) -> None:
    with pytest.raises(DocumentConversionError, match=r"card title .* bullet list"):
        generate(deck(body))


def test_unknown_icons_are_an_error_with_suggestions() -> None:
    with pytest.raises(DocumentConversionError, match=r"Line 5: Unknown icon ':icon-chek:'\. Did"):
        generate(deck("- :icon-chek: a\n"))


def test_icons_in_code_stay_text() -> None:
    data = generate(deck("Schreibe `:icon-check:` vor den Titel.\n"))
    texts = "".join(t.text or "" for t in tree(data).iter(f"{{{A}}}t"))
    assert ":icon-check:" in texts


def test_the_converter_writes_the_icons_again() -> None:
    text = PptxConverter().convert(generate(deck(CARDS + "\n## Liste\n\n" + BULLETS))).text
    assert ":icon-rocket: Start" in text and ":icon-shield: Sicherheit" in text
    assert ":icon-check: Erledigt" in text and ":icon-x: Verworfen" in text
