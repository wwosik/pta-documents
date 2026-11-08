"""E04-S05: the sticker on the master (``kennzeichnung:``)."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from lxml import etree

from pta_documents.design import slides as design
from pta_documents.design.variants import Language, Marking, SlidesVariant
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.pptx import sticker
from pta_documents.generation.pptx.options import PptxOptions
from tests.conftest import SOURCE_TEMPLATES
from tests.generation.pptx.conftest import generate, open_pptx

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = {"a": A, "p": P}
DECK = "# Titel\n\n## Inhalt\n\nText\n\n## Mehr\n\n- Punkt\n"
MASTER = "ppt/slideMasters/slideMaster1.xml"


def master(data: bytes) -> etree._Element:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return etree.fromstring(z.read(MASTER))


def stickers(root: etree._Element) -> list[etree._Element]:
    name = design.STICKER.shape_name
    found = root.xpath(f"p:cSld/p:spTree/p:sp[p:nvSpPr/p:cNvPr/@name='{name}']", namespaces=NS)
    assert isinstance(found, list)
    return [e for e in found if isinstance(e, etree._Element)]


def text(element: etree._Element) -> str:
    return "".join(t.text or "" for t in element.iter(f"{{{A}}}t"))


def deck(front_matter: str = "", options: PptxOptions | None = None) -> bytes:
    head = f"---\n{front_matter}\n---\n" if front_matter else ""
    return generate(head + DECK, options)


def test_a_basic_deck_has_no_sticker() -> None:
    assert stickers(master(deck())) == []


def test_a_training_deck_looks_like_the_template() -> None:
    (shape,) = stickers(master(deck("vorlage: schulung")))
    with zipfile.ZipFile(SOURCE_TEMPLATES / "PTA-Powerpoint-Schulungsvorlage.potx") as z:
        (original,) = stickers(etree.fromstring(z.read(MASTER)))
    assert etree.tostring(shape, method="c14n", exclusive=True) == etree.tostring(
        original, method="c14n", exclusive=True
    )
    assert text(shape) == "Für den internen Gebrauch"


@pytest.mark.parametrize("variant", ["basis", "schulung"])
def test_confidential_on_both_templates(variant: str) -> None:
    root = master(deck(f"vorlage: {variant}\nkennzeichnung: vertraulich"))
    (shape,) = stickers(root)
    assert text(shape) == "VERTRAULICH"
    off = shape.find("p:spPr/a:xfrm/a:off", NS)
    ext = shape.find("p:spPr/a:xfrm/a:ext", NS)
    assert off is not None and ext is not None
    area = design.STICKER.area
    assert (int(off.get("x", "")), int(off.get("y", ""))) == (area.left, area.top)
    assert (int(ext.get("cx", "")), int(ext.get("cy", ""))) == (area.width, area.height)
    # Right-aligned before the corner bracket, top right.
    assert area.right <= design.cm(33.867) and area.left > design.cm(25)
    # Scheme colours only, like the template's.
    assert shape.find(".//a:srgbClr", NS) is None
    assert [c.get("val") for c in shape.iterfind(".//a:gs/a:schemeClr", NS)] == [
        "accent6",
        "accent6",
        "tx2",
    ]
    ids = [e.get("id") for e in root.iter(f"{{{P}}}cNvPr")]
    assert len(ids) == len(set(ids))


def test_the_basic_sticker_is_built_like_the_training_one() -> None:
    (built,) = stickers(master(deck("kennzeichnung: intern")))
    (template,) = stickers(master(deck("vorlage: schulung")))
    for path in ("p:spPr/a:xfrm", "p:spPr/a:gradFill", "p:txBody/a:bodyPr", ".//a:pPr"):
        first, second = built.find(path, NS), template.find(path, NS)
        assert first is not None and second is not None
        assert etree.tostring(first, method="c14n", exclusive=True) == etree.tostring(
            second, method="c14n", exclusive=True
        ), path
    assert text(built) == text(template)


@pytest.mark.parametrize(
    ("marking", "language", "expected"),
    [
        ("vertraulich", "de", "VERTRAULICH"),
        ("intern", "de", "Für den internen Gebrauch"),
        ("entwurf", "de", "ENTWURF"),
        ("vertraulich", "en", "CONFIDENTIAL"),
        ("intern", "en", "For internal use only"),
        ("entwurf", "en", "DRAFT"),
    ],
)
def test_texts(marking: str, language: str, expected: str) -> None:
    for variant in ("basis", "schulung"):
        root = master(deck(f"vorlage: {variant}\nsprache: {language}\nkennzeichnung: {marking}"))
        (shape,) = stickers(root)
        assert text(shape) == expected
        r_pr = shape.find(".//a:rPr", NS)
        assert r_pr is not None
        assert r_pr.get("lang") == ("en-US" if language == "en" else "de-DE")


def test_unknown_values_list_the_valid_ones() -> None:
    with pytest.raises(DocumentConversionError) as error:
        deck("kennzeichnung: geheim")
    assert "vertraulich, intern, entwurf, kein" in error.value.reason


def test_the_training_marking_cannot_be_removed() -> None:
    with pytest.raises(DocumentConversionError) as error:
        deck("vorlage: schulung\nkennzeichnung: kein")
    assert "internal use" in error.value.reason
    assert "vertraulich, intern, entwurf" in error.value.reason
    assert stickers(master(deck("kennzeichnung: kein"))) == []


def test_options_and_front_matter() -> None:
    assert sticker.resolve(SlidesVariant.BASIC, None) is Marking.NONE
    assert sticker.resolve(SlidesVariant.TRAINING, None) is Marking.INTERNAL
    assert sticker.resolve(SlidesVariant.BASIC, Marking.DRAFT) is Marking.DRAFT
    data = deck(options=PptxOptions(marking=Marking.CONFIDENTIAL, language=Language.EN))
    (shape,) = stickers(master(data))
    assert text(shape) == "CONFIDENTIAL"
    # The front matter wins over the options.
    data = deck("kennzeichnung: entwurf", PptxOptions(marking=Marking.CONFIDENTIAL))
    assert text(stickers(master(data))[0]) == "ENTWURF"


def test_the_sticker_shows_on_slides_with_master_graphics() -> None:
    presentation = open_pptx(deck("kennzeichnung: vertraulich"))
    for slide in presentation.slides:
        layout = slide.slide_layout
        if layout.name == design.LAYOUTS.title_and_text:
            assert layout._element.get("showMasterSp") != "0"
            assert slide._element.get("showMasterSp") != "0"


def test_review_files(review_dir: Path) -> None:
    (review_dir / "deck-vertraulich.pptx").write_bytes(
        deck("kennzeichnung: vertraulich\ntitel: Vertrauliche Präsentation")
    )
