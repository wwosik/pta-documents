"""E04-S05: the training template over all slide kinds, and English title slides."""

from __future__ import annotations

import io
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest
from lxml import etree
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.slide import Slide

from pta_documents.conversions.pptx import PptxConverter
from pta_documents.design import slides as design
from pta_documents.design import templates
from pta_documents.design.variants import Language, SlidesVariant
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import MarkdownDocument
from tests.conftest import SOURCE_TEMPLATES
from tests.expected import assert_matches_expected
from tests.generation.pptx.conftest import generate, open_pptx
from tests.generation.pptx.test_content import DIAGRAM
from tests.generation.pptx.test_flow import LAYOUTS
from tests.generation.pptx.test_kinds import SAMPLE as KINDS
from tests.generation.pptx.test_kinds import photo

SAMPLES = Path(__file__).parent / "samples"
DECK = (SAMPLES / "deck.md").read_text(encoding="utf-8")
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
TRAINING = PptxOptions(variant=SlidesVariant.TRAINING)
TRAINING_SOURCE = SOURCE_TEMPLATES / "PTA-Powerpoint-Schulungsvorlage.potx"
BASIC_SOURCE = SOURCE_TEMPLATES / "PTA-Powerpoint-Basisvorlage.potx"
LAY = design.LAYOUTS
CHANGED_LAYOUTS = {
    LAY.title_plain: "0",
    LAY.quote_01: "0",
    "Titel, Bild und Text": None,
    "Titel, Text und Bild 02": None,
    "Titel, Text und zwei Bilder 01": None,
}
"""Layouts whose ``showMasterSp`` the training template changes against the basic one."""

SAMPLE_DECKS = {
    "deck": (DECK, (DIAGRAM,)),
    "layouts-pta": (KINDS, (photo(),)),
    "layouts": (LAYOUTS, ()),
}


def training_deck(name: str) -> bytes:
    markdown, resources = SAMPLE_DECKS[name]
    return generate(markdown, TRAINING, resources)


def show_master_shapes(path_or_data: Path | bytes) -> dict[str, str | None]:
    """Layout name -> its ``showMasterSp`` attribute."""
    source = io.BytesIO(path_or_data) if isinstance(path_or_data, bytes) else path_or_data
    result: dict[str, str | None] = {}
    with zipfile.ZipFile(source) as z:
        for name in z.namelist():
            if name.startswith("ppt/slideLayouts/slideLayout") and name.endswith(".xml"):
                layout = etree.fromstring(z.read(name))
                c_sld = layout.find(f"{{{P}}}cSld")
                assert c_sld is not None
                result[str(c_sld.get("name"))] = layout.get("showMasterSp")
    return result


@pytest.mark.parametrize("name", list(SAMPLE_DECKS))
def test_the_samples_round_trip_on_the_training_template(name: str) -> None:
    markdown = PptxConverter().convert(training_deck(name)).text
    assert_matches_expected(SAMPLES / f"{name}.roundtrip.expected.md", markdown)


@pytest.mark.parametrize("name", ["layouts-pta", "layouts"])
def test_the_samples_generate_without_notes_on_the_training_template(name: str) -> None:
    markdown, resources = SAMPLE_DECKS[name]
    result = PptxGenerator().generate(MarkdownDocument(markdown, resources), io.BytesIO(), TRAINING)
    assert result.notes == ()


def test_the_training_layouts_keep_their_master_graphics_setting() -> None:
    training, basic = show_master_shapes(TRAINING_SOURCE), show_master_shapes(BASIC_SOURCE)
    assert {name for name in training if training[name] != basic[name]} == set(CHANGED_LAYOUTS)
    for name, value in CHANGED_LAYOUTS.items():
        assert training[name] == value, name
    assert show_master_shapes(training_deck("deck")) == training


def test_the_sticker_shows_on_the_content_slides_of_a_training_deck() -> None:
    hidden = {name for name, value in show_master_shapes(TRAINING_SOURCE).items() if value == "0"}
    content = 0
    for name in SAMPLE_DECKS:
        for slide in open_pptx(training_deck(name)).slides:
            if slide.slide_layout.name in hidden:
                continue
            assert slide._element.get("showMasterSp") != "0"
            content += 1
    assert content > 20


def layout_emf_logos(slide: Slide) -> list[str]:
    """The EMF pictures of the slide's layout — the German logo of the title layouts."""
    return [
        rel.target_ref
        for rel in slide.slide_layout.part.rels.values()
        if not rel.is_external and rel.target_ref.lower().endswith(".emf")
    ]


@pytest.mark.parametrize("variant", list(SlidesVariant))
@pytest.mark.parametrize("title_slide", list(design.TITLE_SLIDES))
def test_english_title_slides_show_only_the_english_logo(
    variant: SlidesVariant, title_slide: str
) -> None:
    german = PptxOptions(variant=variant, title_slide=title_slide)
    (slide,) = open_pptx(generate("# Title\n", replace(german, language=Language.EN))).slides
    assert slide.slide_layout.name == design.TITLE_SLIDES[title_slide]
    assert layout_emf_logos(slide) == []
    pictures = [s for s in slide.shapes if s.shape_type == MSO_SHAPE_TYPE.PICTURE]
    assert [picture.image.blob for picture in pictures] == [  # type: ignore[attr-defined]
        templates.read(templates.ENGLISH_LOGO)
    ]
    # No placeholder draws a picture either (idx 36 of 'Titelfolie Branchen' is the German logo).
    for shape in slide.placeholders:
        assert next(shape._element.iter(f"{{{A}}}blip"), None) is None
    (german_slide,) = open_pptx(generate("# Titel\n", german)).slides
    assert layout_emf_logos(german_slide), "the German title layout shows the German logo"
    assert not [s for s in german_slide.shapes if s.shape_type == MSO_SHAPE_TYPE.PICTURE]


def test_review_files(review_dir: Path) -> None:
    (review_dir / "deck-schulung.pptx").write_bytes(training_deck("deck"))
    english = PptxOptions(language=Language.EN, title_slide="branchen")
    (review_dir / "deck-en.pptx").write_bytes(generate(DECK, english, (DIAGRAM,)))
    training_english = replace(TRAINING, language=Language.EN)
    (review_dir / "deck-schulung-en.pptx").write_bytes(generate(DECK, training_english, (DIAGRAM,)))
