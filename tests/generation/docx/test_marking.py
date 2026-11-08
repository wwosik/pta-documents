"""E12-S03: ``kennzeichnung:`` in Word — the text below the logo of every header, on the cover,
and the watermark „ENTWURF". The documents go to ``.tmp/review/marking-<wert>.docx``."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest
from lxml import etree

from pta_documents import DocumentConversionError, DocumentFormat
from pta_documents.conversions.docx import DocxConverter
from pta_documents.design import word, word_frame
from pta_documents.design.variants import TEXTS, Language, Marking, WordVariant
from pta_documents.generation.docx import marking
from pta_documents.generation.docx.options import DocxOptions
from tests.generation.docx.conftest import generate, open_docx, parts

W: Final = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP: Final = marking.WP
HEADER: Final = re.compile(r"word/header\d+\.xml")
EMU: Final = marking.EMU_PER_POINT


def markdown(variant: WordVariant, value: str | None, language: str = "de") -> str:
    key = f"kennzeichnung: {value}\n" if value is not None else ""
    return (
        f"---\nvorlage: {variant.value}\ntitel: Angebot\nautor: Anna Nowak\nsprache: {language}\n"
        f"datum: 2026-11-08\n{key}---\n# Ausgangslage\n\nText.\n"
    )


def headers(data: bytes) -> dict[str, etree._Element]:
    return {n: etree.fromstring(c) for n, c in parts(data).items() if HEADER.fullmatch(n)}


def child(element: etree._Element, path: str) -> etree._Element:
    found = element.find(path)
    assert found is not None, path
    return found


def box_texts(root: etree._Element) -> list[str]:
    return [
        "".join(t.text or "" for t in box.iter(f"{{{W}}}t"))
        for box in root.iter(f"{{{W}}}txbxContent")
    ]


@pytest.mark.parametrize("variant", list(WordVariant), ids=lambda v: v.value)
@pytest.mark.parametrize("value", [m for m in Marking if m is not Marking.NONE])
def test_every_header_shows_the_marking(variant: WordVariant, value: Marking) -> None:
    data = generate(markdown(variant, value.value))
    found = headers(data)
    assert found
    for name, root in found.items():
        assert box_texts(root) == [TEXTS[Language.DE].marking(value)], name
        assert bool(marking.watermarks(root)) is (value is Marking.DRAFT), name


def test_the_marking_is_in_pta_blue_capitals_by_theme_colour() -> None:
    data = generate(markdown(WordVariant.PORTRAIT, "vertraulich"))
    for root in headers(data).values():
        box = next(root.iter(f"{{{W}}}txbxContent"))
        paragraph = next(box.iter(f"{{{W}}}p"))
        assert child(paragraph, f"{{{W}}}pPr/{{{W}}}pStyle").get(f"{{{W}}}val") == "Kopfzeile"
        assert child(paragraph, f"{{{W}}}pPr/{{{W}}}jc").get(f"{{{W}}}val") == "right"
        r_pr = next(paragraph.iter(f"{{{W}}}rPr"))
        assert r_pr.find(f"{{{W}}}caps") is not None
        assert child(r_pr, f"{{{W}}}color").get(f"{{{W}}}themeColor") == "accent1"
        assert child(r_pr, f"{{{W}}}sz").get(f"{{{W}}}val") == "18"


@pytest.mark.parametrize("variant", list(WordVariant), ids=lambda v: v.value)
def test_the_text_box_sits_below_the_rule_and_above_the_text(variant: WordVariant) -> None:
    data = generate(markdown(variant, "intern"))
    frame = word_frame.read(variant)
    area = word_frame.marking_area(frame)
    for root in headers(data).values():
        anchor = next(
            a
            for a in root.iter(f"{{{WP}}}anchor")
            if child(a, f"{{{WP}}}docPr").get("name") == word.MARKING.shape_name
        )
        top = int(child(anchor, f"{{{WP}}}positionV/{{{WP}}}posOffset").text or "0") / EMU
        height = int(child(anchor, f"{{{WP}}}extent").get("cy") or "0") / EMU
        assert anchor.find(f"{{{WP}}}wrapNone") is not None
        assert child(anchor, f"{{{WP}}}positionH/{{{WP}}}align").text == "right"
        assert top == pytest.approx(area.y_pt, abs=0.01)
        assert frame.other.header.rules[0].y_pt < top
        assert top + height <= frame.page.top_pt


def test_the_cover_shows_the_marking_below_the_byline() -> None:
    data = generate(markdown(WordVariant.PORTRAIT, "vertraulich"))
    paragraphs = open_docx(data).paragraphs
    texts = [p.text for p in paragraphs]
    byline = texts.index("Anna Nowak, 08.11.2026")
    assert texts[byline + 1] == "VERTRAULICH"
    style = paragraphs[byline + 1].style
    assert style is not None
    assert style.name == word.STYLES.author


def test_no_cover_no_cover_line() -> None:
    data = generate(markdown(WordVariant.PORTRAIT_NO_COVER, "vertraulich"))
    assert "VERTRAULICH" not in [p.text for p in open_docx(data).paragraphs]


def test_english_texts() -> None:
    data = generate(markdown(WordVariant.PORTRAIT, "entwurf", language="en"))
    for root in headers(data).values():
        assert box_texts(root) == ["DRAFT"]
        assert [
            child(s, f"{{{marking.V}}}textpath").get("string") for s in marking.watermarks(root)
        ] == ["DRAFT"]
    data = generate(markdown(WordVariant.PORTRAIT, "intern", language="en"))
    assert all(box_texts(r) == ["For internal use only"] for r in headers(data).values())


@pytest.mark.parametrize("variant", list(WordVariant), ids=lambda v: v.value)
def test_kein_leaves_the_headers_of_the_template(variant: WordVariant) -> None:
    without = parts(generate(markdown(variant, None)))
    none = parts(generate(markdown(variant, "kein")))
    names = [n for n in without if HEADER.fullmatch(n)]
    assert names
    for name in names:
        assert none[name] == without[name], name


def test_the_option_works_without_front_matter() -> None:
    text = "---\nvorlage: hoch-ohne-deckblatt\n---\n# Titel\n"
    data = generate(text, DocxOptions(marking=Marking.CONFIDENTIAL))
    assert all(box_texts(r) == ["VERTRAULICH"] for r in headers(data).values())


def test_the_front_matter_wins_over_the_option() -> None:
    data = generate(
        markdown(WordVariant.PORTRAIT_NO_COVER, "intern"), DocxOptions(marking=Marking.DRAFT)
    )
    assert all(not marking.watermarks(r) for r in headers(data).values())


def test_an_unknown_value_names_the_valid_ones() -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate(markdown(WordVariant.PORTRAIT, "geheim"))
    assert error.value.format is DocumentFormat.DOCX
    assert "vertraulich, intern, entwurf, kein" in error.value.reason


def test_the_watermark_fits_the_diagonal_of_the_type_area() -> None:
    data = generate(markdown(WordVariant.LANDSCAPE, "entwurf"))
    page = word_frame.read(WordVariant.LANDSCAPE).page
    for root in headers(data).values():
        (shape,) = marking.watermarks(root)
        style = dict(
            item.split(":", 1) for item in str(shape.get("style")).split(";") if ":" in item
        )
        width = float(style["width"].removesuffix("pt"))
        height = float(style["height"].removesuffix("pt"))
        assert style["rotation"] == "315"
        assert style["mso-position-horizontal-relative"] == "margin"
        assert style["mso-position-vertical"] == "center"
        assert int(style["z-index"]) < 0  # behind the text
        assert (width + height) / 2**0.5 == pytest.approx(
            min(page.text_width_pt, page.text_height_pt), rel=0.01
        )
        assert shape.get("fillcolor") == "#" + word.WATERMARK.color
        assert shape.get(f"{{{marking.OFFICE}}}allowincell") == "f"


def test_the_text_boxes_take_drawing_ids_nobody_else_has() -> None:
    data = generate(markdown(WordVariant.PORTRAIT, "entwurf") + "\n![Bild](qr:https://pta.de)\n")
    doc_prs = [
        d
        for name, content in parts(data).items()
        if name.endswith(".xml") and name.startswith("word/")
        for d in etree.fromstring(content).iter(f"{{{WP}}}docPr")
    ]
    ours = [d.get("id") for d in doc_prs if d.get("name") == word.MARKING.shape_name]
    others = {d.get("id") for d in doc_prs if d.get("name") != word.MARKING.shape_name}
    assert len(ours) == 2
    assert len(set(ours)) == len(ours)
    assert not others & set(ours)


def test_the_round_trip_does_not_change(review_dir: Path) -> None:
    variant = WordVariant.PORTRAIT_NO_COVER
    marked = generate(markdown(variant, "entwurf"))
    (review_dir / "marking-entwurf.docx").write_bytes(marked)
    (review_dir / "marking-vertraulich.docx").write_bytes(
        generate(markdown(WordVariant.PORTRAIT, "vertraulich"))
    )
    plain = generate(markdown(variant, None))
    assert DocxConverter().convert(marked).text == DocxConverter().convert(plain).text
