"""E09-S03: slide transitions — the front matter ``uebergang`` for every slide, ``{uebergang="…"}``
on a ``##`` for its slide and on a ``#`` for its chapter; morph with a fade for older programs
(port of vt-tools-libs ``Animations.Transition``)."""

from __future__ import annotations

import datetime as dt
import io
from pathlib import Path
from typing import Final

import pytest
from lxml import etree

from pta_documents.conversions.pptx import PptxConverter
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.common.slide_transition import VALID, SlideTransition
from pta_documents.generation.pptx.animations import transition
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import MarkdownDocument
from tests.generation.docx.conftest import generate as docx_generate
from tests.generation.docx.conftest import parts as docx_parts
from tests.generation.pptx.conftest import generate, open_pptx

P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
MC: Final = "http://schemas.openxmlformats.org/markup-compatibility/2006"
P159: Final = "http://schemas.microsoft.com/office/powerpoint/2015/09/main"
NS: Final = {"p": P, "mc": MC, "p159": P159}

DECK: Final = (
    "# Deck\n\nSubtitle\n\n## Intro\n\nText\n\n"
    "# Chapter{chapter}\n\n## One\n\nText\n\n## Two{two}\n\nText\n\n"
    "# Next\n\n## Three\n\nText\n"
)
"""Title, Intro, chapter 01, One, Two, chapter 02, Three."""


def deck(front: str = "", chapter: str = "", two: str = "") -> bytes:
    head = f"---\n{front}\n---\n" if front else ""
    return generate(head + DECK.format(chapter=chapter, two=two))


def slides_xml(data: bytes) -> list[etree._Element]:
    return [etree.fromstring(etree.tostring(s.element)) for s in open_pptx(data).slides]


def kind_of(slide: etree._Element) -> str | None:
    """The effect of the slide's transition (``fade``, ``push dir=u`` …), ``morph`` for the
    alternate content, None without one."""
    if slide.find(f"{{{MC}}}AlternateContent") is not None:
        return "morph"
    element = slide.find(f"{{{P}}}transition")
    if element is None:
        return None
    (effect,) = list(element)
    name = etree.QName(effect).localname
    attributes = " ".join(f"{k}={v}" for k, v in sorted(effect.attrib.items()))
    return f"{name} {attributes}".strip()


def kinds(data: bytes) -> list[str | None]:
    return [kind_of(s) for s in slides_xml(data)]


def test_without_a_transition_no_slide_has_one() -> None:
    assert kinds(deck()) == [None] * 7
    assert kinds(deck(front="uebergang: none")) == [None] * 7


def test_the_front_matter_fades_every_slide(review_dir: Path) -> None:
    data = deck(front="uebergang: fade")
    (review_dir / "deck-transition-fade.pptx").write_bytes(data)
    assert kinds(data) == ["fade"] * 7
    (element,) = slides_xml(data)[0].findall(f"{{{P}}}transition")
    assert element.get("spd") == "med"


def test_the_options_set_the_transition_and_the_front_matter_overrides_them() -> None:
    data = generate(DECK.format(chapter="", two=""), PptxOptions(transition=SlideTransition.WIPE))
    assert kinds(data) == ["wipe"] * 7
    data = generate(
        "---\nuebergang: Push\n---\n" + DECK.format(chapter="", two=""),
        PptxOptions(transition=SlideTransition.WIPE),
    )
    assert kinds(data) == ["push"] * 7


def test_an_attribute_on_a_slide_heading_is_for_that_slide_only() -> None:
    data = deck(front="uebergang: fade", two=' {uebergang="push"}')
    assert kinds(data) == ["fade", "fade", "fade", "fade", "push", "fade", "fade"]
    data = deck(front="uebergang: fade", two=' {uebergang="none"}')
    assert kinds(data) == ["fade", "fade", "fade", "fade", None, "fade", "fade"]


def test_an_attribute_on_a_chapter_heading_is_for_the_chapter(review_dir: Path) -> None:
    data = deck(chapter=' {uebergang="push-up"}', two=' {uebergang="morph"}')
    (review_dir / "deck-transition-chapter.pptx").write_bytes(data)
    up = "push dir=u"
    assert kinds(data) == [None, None, up, up, "morph", None, None]


def test_the_title_heading_sets_the_slides_before_the_first_chapter() -> None:
    data = generate('# Deck {uebergang="zoom"}\n\n## Intro\n\nText\n\n# Chapter\n\n## One\n\nT\n')
    assert kinds(data) == ["zoom", "zoom", None, None]


def test_continued_slides_keep_the_transition() -> None:
    points = "\n".join(f"- Point number {n} with some words to fill the line" for n in range(40))
    data = generate(f'# Deck\n\n## Long {{uebergang="cover"}}\n\n{points}\n\n## After\n\nText\n')
    found = kinds(data)
    assert len(found) > 3
    assert found[1:-1] == ["cover"] * (len(found) - 2)
    assert found[-1] is None


def test_the_closing_slide_takes_an_attribute_with_closing() -> None:
    data = generate('# Deck\n\n## S\n\nText\n\n# Danke {.closing uebergang="fade"}\n')
    assert kinds(data) == [None, None, "fade"]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("fade", "fade"),
        ("push", "push"),
        ("push-left", "push dir=l"),
        ("push-right", "push dir=r"),
        ("push-up", "push dir=u"),
        ("push-down", "push dir=d"),
        ("wipe", "wipe"),
        ("wipe-left", "wipe dir=l"),
        ("wipe-right", "wipe dir=r"),
        ("wipe-up", "wipe dir=u"),
        ("wipe-down", "wipe dir=d"),
        ("split", "split dir=out orient=vert"),
        ("cover", "cover"),
        ("uncover", "pull"),
        ("zoom", "zoom"),
        ("cut", "cut"),
        ("morph", "morph"),
    ],
)
def test_every_transition_writes_its_element(value: str, expected: str) -> None:
    data = generate(f'# Deck\n\n## S {{uebergang="{value}"}}\n\nText\n')
    assert kinds(data) == [None, expected]


def test_every_transition_is_tested() -> None:
    assert len(SlideTransition) == 18  # none and the 17 of the test above


def test_morph_falls_back_to_a_fade() -> None:
    data = generate('# Deck\n\n## S {uebergang="morph"}\n\nText\n')
    slide = slides_xml(data)[1]
    (content,) = slide.findall("mc:AlternateContent", NS)
    choice, fallback = list(content)
    assert etree.QName(choice).localname == "Choice"
    assert choice.get("Requires") == "p159"
    morph = choice.find("p:transition/p159:morph", NS)
    assert morph is not None and morph.get("option") == "byObject"
    assert etree.QName(fallback).localname == "Fallback"
    assert fallback.find("p:transition/p:fade", NS) is not None
    assert [t.get("spd") for t in content.iter(f"{{{P}}}transition")] == ["slow", "slow"]


def test_morph_is_valid_xml_with_the_prefix_it_requires() -> None:
    element = transition(SlideTransition.MORPH)
    assert element is not None
    choice = element[0]
    assert choice.nsmap.get("p159") == P159
    assert transition(SlideTransition.NONE) is None


@pytest.mark.parametrize("value", ["fade", "morph"])
def test_the_transition_comes_before_the_timing(value: str) -> None:
    data = generate(f'# Deck\n\n## S {{uebergang="{value}"}}\n\n{{.build}}\n- a\n- b\n')
    names = [etree.QName(c).localname for c in slides_xml(data)[1]]
    transition_at = names.index("AlternateContent" if value == "morph" else "transition")
    assert names[:2] == ["cSld", "clrMapOvr"]
    assert transition_at == 2
    assert transition_at < names.index("timing")


@pytest.mark.parametrize(
    ("source", "line"),
    [
        ('# Deck\n\n## S {uebergang="slide"}\n\nText\n', 3),
        ('---\ntitel: T\n---\n# Deck {uebergang="fades"}\n', 4),
    ],
)
def test_an_unknown_transition_raises_with_its_line_and_the_valid_ones(
    source: str, line: int
) -> None:
    with pytest.raises(DocumentConversionError) as caught:
        generate(source)
    assert caught.value.reason.startswith(f"Line {line}: Unknown slide transition ")
    assert VALID in caught.value.reason
    assert "push-left" in VALID and "morph" in VALID


def test_an_unknown_transition_in_the_front_matter_raises_with_the_valid_ones() -> None:
    with pytest.raises(DocumentConversionError) as caught:
        deck(front="uebergang: slide")
    assert "'uebergang'" in caught.value.reason
    assert "'push-left'" in caught.value.reason and "'morph'" in caught.value.reason


def test_the_attribute_named_twice_raises() -> None:
    with pytest.raises(DocumentConversionError) as caught:
        generate('# Deck\n\n## S {uebergang="fade" uebergang="push"}\n\nText\n')
    assert "name uebergang twice" in caught.value.reason


def test_the_converter_reads_no_transitions() -> None:
    plain = "# Deck\n\n## S\n\nText\n\n## T\n\nMore\n"
    moving = "---\nuebergang: fade\n---\n" + plain.replace("## S", '## S {uebergang="morph"}')
    converter = PptxConverter()
    assert converter.convert(generate(moving)).text == converter.convert(generate(plain)).text


# ---------------------------------------------------------------------- Word and PDF


def test_word_and_pdf_take_the_attribute_without_effect() -> None:
    plain = "---\ntitel: Deck\n---\n# Deck\n\n## Points\n\nText\n"
    moving = plain.replace("## Points", '## Points {uebergang="push-up"}')
    word = [docx_parts(docx_generate(s))["word/document.xml"] for s in (moving, plain)]
    assert word[0] == word[1]
    pdf = pytest.importorskip("pta_documents.generation.pdf")
    created = dt.datetime(2026, 11, 8, 9, 0, tzinfo=dt.UTC)
    options = pdf.PdfOptions(created=created, system_fonts=False)
    outputs: list[bytes] = []
    for source in (moving, plain):
        output = io.BytesIO()
        pdf.PdfGenerator().generate(MarkdownDocument(source), output, options)
        outputs.append(output.getvalue())
    assert outputs[0] == outputs[1]


def test_word_rejects_the_front_matter_key() -> None:
    with pytest.raises(DocumentConversionError) as caught:
        docx_generate("---\ntitel: Deck\nuebergang: fade\n---\n# Deck\n")
    assert "uebergang" in caught.value.reason
