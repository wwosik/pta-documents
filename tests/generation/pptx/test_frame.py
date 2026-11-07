"""E04-S01: the deck on the PTA template."""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import pytest
from PIL import Image
from pptx.enum.shapes import MSO_SHAPE_TYPE

from pta_documents import DocumentConversionError, DocumentFormat
from pta_documents.design import slides as design
from pta_documents.markdown import DocumentResource
from tests.generation.pptx.conftest import (
    generate,
    layout_names,
    open_pptx,
    placeholder_texts,
    texts,
)


def png(width: int = 800, height: int = 600) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (0, 70, 118)).save(buffer, "PNG")
    return buffer.getvalue()


IMAGES = (DocumentResource("images/foto.png", "image/png", png()),)

DECK = """---
untertitel: Lenkungskreis
autor: Erika Muster
ort: Hamburg
datum: 06.11.2026
---
# Projekt Nordlicht

# Ausgangslage

## Ziele

- Kosten senken
- Qualität steigern

## Team

Das Team bei der Arbeit.

![Team im Workshop](images/foto.png)

# Ergebnisse

## Bild allein

![Foto](images/foto.png)

# Vielen Dank! {.closing}
"""


def test_slides_use_pta_layouts(review_dir: Path) -> None:
    data = generate(DECK, resources=IMAGES)
    (review_dir / "frame.pptx").write_bytes(data)
    assert layout_names(data) == [
        "Titelfolie mit Bild 02",
        "Trennfolie",
        "Titel und Text",
        "Titel, Text und Bild 01",
        "Trennfolie",
        "Titel und Bild 01",
        "Abbschlussfolie",
    ]


def test_title_chapter_and_closing_texts() -> None:
    slides = list(open_pptx(generate(DECK, resources=IMAGES)).slides)
    ph = design.PLACEHOLDERS
    title = texts(slides[0])
    assert title[ph.title] == "Projekt Nordlicht"
    assert title[ph.subtitle] == "Lenkungskreis"
    assert title[ph.byline] == "Erika Muster, Hamburg, 06.11.2026"
    assert texts(slides[1])[ph.chapter_number] == "01"
    assert texts(slides[4])[ph.chapter_number] == "02"
    assert texts(slides[4])[ph.title] == "Ergebnisse"
    assert texts(slides[6])[ph.title] == "Vielen Dank!"


def test_no_sample_slides_remain_and_decorations_are_kept() -> None:
    data = generate("---\ntitelfolie: branchen\n---\n# Titel\n\n## Folie\n\nText\n")
    presentation = open_pptx(data)
    assert len(presentation.slides) == 2
    cover = presentation.slides[0]
    assert cover.slide_layout.name == "Titelfolie Branchen"
    # Corner brackets, line and logo of this layout are invisible placeholders (prompt "x").
    present = {s.placeholder_format.idx for s in cover.placeholders}
    assert {35, 30, 36, 37} <= present


def test_footer_and_slide_number_without_date() -> None:
    data = generate(
        "---\nfusszeile: Lenkungskreis Q3\n---\n# Deck\n\n## Eins\n\nText\n\n## Zwei\n\nText\n"
    )
    presentation = open_pptx(data)
    cover, first, second = presentation.slides
    assert "FOOTER" not in placeholder_texts(cover)
    for number, slide in ((2, first), (3, second)):
        kinds = placeholder_texts(slide)
        assert kinds["FOOTER"] == "PTA – Lenkungskreis Q3"
        assert kinds["SLIDE_NUMBER"] == str(number)
        assert "DATE" not in kinds


def test_footer_defaults_to_the_title() -> None:
    data = generate("# Mein Deck\n\n## Eins\n\nText\n")
    slide = open_pptx(data).slides[1]
    assert placeholder_texts(slide)["FOOTER"] == "PTA – Mein Deck"


def test_metadata() -> None:
    data = generate("---\nautor: Erika Muster\n---\n# Mein Deck\n")
    properties = open_pptx(data).core_properties
    assert properties.title == "Mein Deck"
    assert properties.author == "Erika Muster"
    app = zipfile.ZipFile(io.BytesIO(data)).read("docProps/app.xml").decode()
    assert "PTA Unternehmensberatung" in app


def test_named_layout_splits_text_at_rules() -> None:
    data = generate(
        '# Deck\n\n## Zwei Spalten {layout="Titel und Text (zweispaltig)"}\n\nLinks\n\n---\n\n'
        "Rechts\n"
    )
    slide = open_pptx(data).slides[1]
    assert slide.slide_layout.name == "Titel und Text (zweispaltig)"
    found = texts(slide)
    assert found[12] == "Links" and found[13] == "Rechts"


def test_training_and_english_templates() -> None:
    data = generate("---\nvorlage: schulung\n---\n# Schulung\n")
    assert open_pptx(data).slides[0].slide_layout.name == "Titelfolie mit Bild 02"
    english = generate("---\nsprache: en\n---\n# Deck\n")
    cover = open_pptx(english).slides[0]
    pictures = [s for s in cover.shapes if s.shape_type == MSO_SHAPE_TYPE.PICTURE]
    assert len(pictures) == 1  # the English logo


def test_title_from_front_matter_makes_a_cover() -> None:
    data = generate("---\ntitel: Aus dem Front Matter\n---\n## Folie\n\nText\n")
    assert layout_names(data)[0] == "Titelfolie mit Bild 02"
    assert texts(open_pptx(data).slides[0])[0] == "Aus dem Front Matter"


@pytest.mark.parametrize(
    ("markdown", "expected"),
    [
        ("---\nvorlage: hell\n---\n# A\n", "Valid values: basis, schulung"),
        ("---\ntitelfolie: rot\n---\n# A\n", "expected 'bild-01' or 'bild-02'"),
        ("---\nfirma: X\n---\n# A\n", "'firma' is not supported here"),
        ("# A\n\n# B\n\nText unter dem Kapitel\n", "no place for content"),
        ('# A\n\n## B {layout="Gibt es nicht"}\n', "no layout 'Gibt es nicht'"),
        ("# A\n\n## B {.wide}\n", "Unknown heading attribute '.wide'"),
        ("# A\n\n## B {.closing}\n", "{.closing} goes on a '#' heading"),
        ("# A\n\n## B\n\n![x](images/fehlt.png)\n", "'images/fehlt.png' is not among"),
    ],
)
def test_mistakes(markdown: str, expected: str) -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate(markdown)
    assert error.value.format is DocumentFormat.PPTX
    assert expected in error.value.reason


def test_slide_parts_are_well_formed() -> None:
    data = generate(DECK, resources=IMAGES)
    content = zipfile.ZipFile(io.BytesIO(data))
    for name in content.namelist():
        if re.fullmatch(r"ppt/slides/slide\d+\.xml", name):
            xml = content.read(name).decode()
            ids = re.findall(r'<p:cNvPr id="(\d+)"', xml)
            assert len(ids) == len(set(ids)), name
