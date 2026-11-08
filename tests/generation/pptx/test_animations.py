"""E09-S02: builds — what ``{.build}``, ``{.frag}``, ``{.exit}`` and ``{.emphasize}`` mark appears
(goes, turns blue) click by click, as PowerPoint writes it (port of vt-tools-libs
``AnimationTests``)."""

from __future__ import annotations

import datetime as dt
import io
from pathlib import Path
from typing import Final

import pytest
from lxml import etree
from PIL import Image as PilImage

from pta_documents.conversions.pptx import PptxConverter
from pta_documents.design import colors
from pta_documents.design import slides as design
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.pptx.animations import Build, Target, timing
from pta_documents.generation.pptx.model import Click, Effect
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import DocumentResource, MarkdownDocument
from tests.charts.test_parser import ORDERS
from tests.generation.docx.conftest import generate as docx_generate
from tests.generation.docx.conftest import parts as docx_parts
from tests.generation.pptx.conftest import generate, open_pptx

A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS: Final = {"a": A, "p": P}
NO_RENDERERS: Final = PptxOptions(code_block_renderers=())
CREATED: Final = dt.datetime(2026, 11, 8, 9, 0, tzinfo=dt.UTC)


def png(name: str, width: int = 800, height: int = 600) -> DocumentResource:
    buffer = io.BytesIO()
    PilImage.new("RGB", (width, height), (0, 111, 185)).save(buffer, "PNG")
    return DocumentResource(name, "image/png", buffer.getvalue())


IMAGES: Final = (png("a.png"), png("b.png"), png("c.png"))


def slides_xml(data: bytes) -> list[etree._Element]:
    return [etree.fromstring(etree.tostring(s.element)) for s in open_pptx(data).slides]


def xpath(root: etree._Element, path: str) -> list[etree._Element]:
    result = root.xpath(path, namespaces=NS)
    assert isinstance(result, list)
    return [e for e in result if isinstance(e, etree._Element)]


def values(root: etree._Element, path: str) -> list[str]:
    result = root.xpath(path, namespaces=NS)
    assert isinstance(result, list)
    return [str(v) for v in result]


def clicks(slide: etree._Element) -> list[list[etree._Element]]:
    """The effects (``p:cTn`` with a preset) of each click of the main sequence."""
    groups = xpath(slide, ".//p:cTn[@nodeType='mainSeq']/p:childTnLst/p:par")
    return [xpath(group, ".//p:cTn[@presetClass]") for group in groups]


def targets(effect: etree._Element) -> list[tuple[str, str | None]]:
    """(spid, paragraph) of the first behaviour of an effect."""
    target = xpath(effect, ".//p:spTgt")[0]
    paragraph = xpath(target, "p:txEl/p:pRg")
    return [(str(target.get("spid")), paragraph[0].get("st") if paragraph else None)]


def shape_ids(slide: etree._Element) -> set[str]:
    return set(values(slide, "p:cSld/p:spTree/*/*/p:cNvPr/@id"))


def body_id(slide: etree._Element, idx: int = design.PLACEHOLDERS.body) -> str:
    return values(slide, f".//p:sp[p:nvSpPr/p:nvPr/p:ph[@idx='{idx}']]/p:nvSpPr/p:cNvPr/@id")[0]


def assert_consistent(slide: etree._Element) -> None:
    """Every animated shape is on the slide, ids of the time nodes are unique, and every effect
    has its build list entry (pictures and groups need none)."""
    ids = values(slide, ".//p:timing//p:cTn/@id")
    assert len(ids) == len(set(ids))
    spids = set(values(slide, ".//p:timing//p:spTgt/@spid"))
    assert spids <= shape_ids(slide)
    listed = set(values(slide, ".//p:bldLst/*/@spid"))
    assert listed <= spids


# ---------------------------------------------------------------------- lists


def test_a_built_list_appears_point_by_point_with_a_fade(review_dir: Path) -> None:
    data = generate("# Deck\n\n## Points\n\n{.build}\n- One\n- Two\n- Three\n")
    (review_dir / "deck-builds-list.pptx").write_bytes(data)
    slide = slides_xml(data)[1]
    body = body_id(slide)
    steps = clicks(slide)
    assert [[targets(e) for e in click] for click in steps] == [
        [[(body, "0")]],
        [[(body, "1")]],
        [[(body, "2")]],
    ]
    for (effect,) in steps:
        assert effect.get("presetID") == "10" and effect.get("presetClass") == "entr"
        assert effect.get("nodeType") == "clickEffect"
        assert values(effect, ".//p:animEffect/@filter") == ["fade"]
        assert values(effect, ".//p:animEffect/p:cBhvr/p:cTn/@dur") == ["500"]
        assert values(effect, ".//p:set//p:attrName/text()") == ["style.visibility"]
    assert values(slide, ".//p:bldLst/p:bldP/@build") == ["p"]
    assert_consistent(slide)
    # The list stays the text of the body placeholder, at the levels of the master.
    assert values(slide, f".//p:sp[p:nvSpPr/p:cNvPr/@id='{body}']//a:pPr/@lvl") == ["2"] * 3


def test_every_paragraph_of_every_level_gets_a_click_and_text_before_stays() -> None:
    source = "# Deck\n\n## Points\n\nIntro\n\n{.build}\n- One\n  - One a\n- Two\n"
    slide = slides_xml(generate(source))[1]
    body = body_id(slide)
    assert [targets(e) for click in clicks(slide) for e in click] == [
        [(body, "1")],
        [(body, "2")],
        [(body, "3")],
    ]


def test_a_fragment_shows_its_block_on_one_click() -> None:
    source = "# Deck\n\n## Points\n\nFirst\n\n{.frag}\n- One\n- Two\n\nLast\n"
    slide = slides_xml(generate(source))[1]
    body = body_id(slide)
    (click,) = clicks(slide)
    assert [targets(e) for e in click] == [[(body, "1")], [(body, "2")]]
    assert [e.get("nodeType") for e in click] == ["clickEffect", "withEffect"]


def test_aufbau_listen_builds_every_outer_list_once() -> None:
    source = (
        "---\naufbau: listen\n---\n# Deck\n\n## Points\n\n- One\n  - One a\n- Two\n\nText\n\n"
        "## Cards\n\n::: cards\n### Card\n\n- x\n- y\n:::\n"
    )
    first, second = slides_xml(generate(source))[1:3]
    body = body_id(first)
    assert [targets(e) for click in clicks(first) for e in click] == [
        [(body, "0")],
        [(body, "1")],
        [(body, "2")],
    ]
    # In a card too: the list of a container is no list inside another.
    assert len(clicks(second)) == 2
    assert_consistent(second)


def test_aufbau_nein_and_no_markers_write_no_timing() -> None:
    for source in (
        "# Deck\n\n## Points\n\n- One\n",
        "---\naufbau: nein\n---\n# D\n\n## P\n\n- x\n",
    ):
        for slide in slides_xml(generate(source)):
            assert xpath(slide, "p:timing") == []


def test_a_wrong_aufbau_value_raises() -> None:
    with pytest.raises(DocumentConversionError, match=r"'aufbau'.*'listen' or 'nein'"):
        generate("---\naufbau: alle\n---\n# Deck\n")


# ---------------------------------------------------------------------- visuals


def test_a_built_table_appears_as_one_graphic() -> None:
    source = "# Deck\n\n## Table\n\n{.build}\n| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n"
    slide = slides_xml(generate(source))[1]
    frame = values(slide, ".//p:graphicFrame/p:nvGraphicFramePr/p:cNvPr/@id")[0]
    (click,) = clicks(slide)
    assert [targets(e) for e in click] == [[(frame, None)]]
    (entry,) = xpath(slide, ".//p:bldLst/*")
    assert entry.tag == f"{{{P}}}bldGraphic" and entry.get("spid") == frame
    assert xpath(entry, "p:bldAsOne")
    assert_consistent(slide)


def test_a_picture_is_animated_but_not_listed() -> None:
    source = "# Deck\n\n## Picture\n\n{.frag}\n![A](a.png)\n"
    slide = slides_xml(generate(source, resources=IMAGES))[1]
    picture = values(slide, ".//p:pic/p:nvPicPr/p:cNvPr/@id")[0]
    (click,) = clicks(slide)
    assert [targets(e) for e in click] == [[(picture, None)]]
    assert xpath(slide, ".//p:bldLst") == []


def test_a_built_image_row_shows_one_picture_per_click() -> None:
    source = "# Deck\n\n## Pictures\n\n{.build}\n![A](a.png) ![B](b.png) ![C](c.png)\n"
    slide = slides_xml(generate(source, resources=IMAGES))[1]
    pictures = values(slide, ".//p:pic/p:nvPicPr/p:cNvPr/@id")
    assert [targets(e)[0][0] for click in clicks(slide) for e in click] == pictures
    assert len(clicks(slide)) == 3


def test_code_and_text_after_a_fragment_appear_in_markdown_order() -> None:
    source = "# Deck\n\n## Code\n\n{.frag}\n```\nx = 1\n```\n\n{.frag=appear}\nAfter the code\n"
    slide = slides_xml(generate(source, NO_RENDERERS))[1]
    first, second = clicks(slide)
    assert {e.get("presetID") for e in first} == {"10"}
    assert [e.get("presetID") for e in second] == ["1"]
    assert_consistent(slide)


# ---------------------------------------------------------------------- flow slides


CARDS: Final = (
    "# Deck\n\n## Cards\n\n{.build}\n::: cards\n### One\n\nText one\n\n### Two\n\nText two\n\n"
    "### Three\n\nText three\n:::\n"
)


def test_built_cards_appear_card_by_card(review_dir: Path) -> None:
    data = generate(CARDS)
    (review_dir / "deck-builds-cards.pptx").write_bytes(data)
    slide = slides_xml(data)[1]
    steps = clicks(slide)
    assert len(steps) == 3
    for click in steps:
        # The frame, the title and the text of a card come together.
        assert len(click) == 3
        assert [e.get("nodeType") for e in click] == ["clickEffect", "withEffect", "withEffect"]
    assert_consistent(slide)


def test_built_rows_and_columns_appear_one_by_one() -> None:
    source = (
        "# Deck\n\n## Rows\n\n{.build=wipe}\n::: rows\n- **One** – first\n- **Two** – second\n"
        ":::\n\n## Columns\n\n{.build}\n::: columns\n![A](a.png)\n\n---\n\nText\n:::\n"
    )
    rows, columns = slides_xml(generate(source, resources=IMAGES))[1:3]
    assert len(clicks(rows)) == 2
    assert {e.get("presetID") for click in clicks(rows) for e in click} == {"22"}
    assert len(clicks(columns)) == 2
    assert_consistent(rows)
    assert_consistent(columns)


def test_a_fragment_panel_brings_its_area_and_text_together() -> None:
    source = "# Deck\n\n## Panel\n\nIntro\n\n{.frag=fly}\n::: panel\nInside\n:::\n"
    slide = slides_xml(generate(source))[1]
    (click,) = clicks(slide)
    assert len(click) == 2
    assert {e.get("presetID") for e in click} == {"2"}
    assert values(click[0], ".//p:anim//p:attrName/text()") == ["ppt_x", "ppt_y"]
    assert_consistent(slide)


def test_a_built_list_in_a_flow_slide_builds_its_text_box() -> None:
    source = "# Deck\n\n## Flow {.dark}\n\n{.build}\n- One\n- Two\n"
    slide = slides_xml(generate(source))[1]
    steps = clicks(slide)
    assert [targets(e)[0][1] for click in steps for e in click] == ["0", "1"]
    assert values(slide, ".//p:bldLst/p:bldP/@build") == ["p"]


# ---------------------------------------------------------------------- exit and emphasis


def test_exit_and_emphasis_on_text() -> None:
    source = "# Deck\n\n## Text\n\n{.exit}\nGoes\n\n{.emphasize}\n- Turns blue\n\nStays\n"
    slide = slides_xml(generate(source))[1]
    out, blue = clicks(slide)
    assert out[0].get("presetClass") == "exit"
    assert values(out[0], ".//p:animEffect/@transition") == ["out"]
    assert values(out[0], ".//p:set/p:to/p:strVal/@val") == ["hidden"]
    assert blue[0].get("presetClass") == "emph" and blue[0].get("presetID") == "3"
    assert values(blue[0], ".//p:animClr//a:srgbClr/@val") == [colors.PTA_BLUE]
    # One text shape, two build groups: the exit and the emphasis.
    assert values(slide, ".//p:bldLst/p:bldP/@grpId") == ["0", "1"]
    assert [e.get("grpId") for e in (out[0], blue[0])] == ["0", "1"]


# ---------------------------------------------------------------------- splitting, errors


def test_a_split_slide_builds_on_every_part() -> None:
    items = "".join(f"- Point {n} with a few more words to fill the line\n" for n in range(40))
    data = generate(f"# Deck\n\n## Many\n\n{{.build}}\n{items}")
    parts = slides_xml(data)[1:]
    assert len(parts) >= 2
    for part in parts:
        steps = clicks(part)
        assert steps and targets(steps[0][0])[0][1] == "0"
        assert_consistent(part)


@pytest.mark.parametrize(
    ("source", "line", "reason"),
    [
        ("# Deck\n\n## S\n\n{.wide}\n- a\n", 5, "Unknown block marker '{.wide}'"),
        ("# Deck\n\n## S\n\nText\n\n{.build}\n", 7, "marks nothing"),
        ("# Deck\n\n{.frag}\nSubtitle\n", 3, "go on '##' slides of content"),
        ("# Deck\n\n## Agenda {.agenda}\n\n{.build}\n- a\n- b\n", 5, "slide kinds"),
        ("# Deck\n\n## S\n\n::: cards\n{.frag}\n### One\n\nText\n:::\n", 6, "built as a whole"),
    ],
)
def test_wrong_markers_raise_with_their_line(source: str, line: int, reason: str) -> None:
    with pytest.raises(DocumentConversionError) as caught:
        generate(source)
    assert caught.value.reason.startswith(f"Line {line}: ")
    assert reason in caught.value.reason


def test_the_converter_reads_no_builds() -> None:
    plain = "# Deck\n\n## Points\n\n- One\n- Two\n\n| A |\n|---|\n| 1 |\n"
    built = "# Deck\n\n## Points\n\n{.build}\n- One\n- Two\n\n{.frag}\n| A |\n|---|\n| 1 |\n"
    converter = PptxConverter()
    assert converter.convert(generate(built)).text == converter.convert(generate(plain)).text


# ---------------------------------------------------------------------- the timing tree


def test_timing_groups_by_click_and_lists_each_shape_once() -> None:
    fade, exit_ = Click(1), Click(2, Effect.EXIT)
    builds = [
        Build(fade, 4, 0, Target.TEXT),
        Build(fade, 5, -1, Target.GRAPHIC),
        Build(exit_, 4, 1, Target.TEXT),
        Build(Click(3, Effect.APPEAR), 6, -1, Target.OTHER),
    ]
    element = timing(builds)
    assert element is not None
    root = etree.fromstring(etree.tostring(element))
    assert [len(c) for c in clicks(root)] == [2, 1, 1]
    entries = [
        (e.tag.split("}")[1], e.get("spid"), e.get("grpId")) for e in xpath(root, "p:bldLst/*")
    ]
    assert entries == [("bldP", "4", "0"), ("bldGraphic", "5", "0"), ("bldP", "4", "1")]
    assert timing([]) is None


def test_a_fragment_chart_is_one_graphic_with_its_title() -> None:
    slide = slides_xml(generate(f"# Deck\n\n## Chart\n\n{{.frag}}\n```chart\n{ORDERS}```\n"))[1]
    frame = values(slide, ".//p:graphicFrame/p:nvGraphicFramePr/p:cNvPr/@id")[0]
    (click,) = clicks(slide)
    assert (frame, None) in [targets(e)[0] for e in click]
    assert values(slide, ".//p:bldLst/p:bldGraphic/@spid") == [frame]
    assert_consistent(slide)


# ---------------------------------------------------------------------- Word and PDF


BUILT: Final = (
    "---\ntitel: Deck\n---\n# Deck\n\n## Points\n\n{.build}\n- One\n- Two\n\n"
    "{.frag=fly}\n| A |\n|---|\n| 1 |\n\n"
    "{.exit}\nGoes\n\n{.emphasize}\nBlue\n"
)


def test_word_and_pdf_give_the_same_without_the_markers() -> None:
    plain = BUILT
    for marker in ("{.build}\n", "{.frag=fly}\n", "{.exit}\n", "{.emphasize}\n"):
        plain = plain.replace(marker, "")
    built_docx, plain_docx = docx_generate(BUILT), docx_generate(plain)
    assert (
        docx_parts(built_docx)["word/document.xml"] == docx_parts(plain_docx)["word/document.xml"]
    )
    pdf = pytest.importorskip("pta_documents.generation.pdf")
    options = pdf.PdfOptions(created=CREATED, system_fonts=False)
    outputs: list[bytes] = []
    for source in (BUILT, plain):
        output = io.BytesIO()
        pdf.PdfGenerator().generate(MarkdownDocument(source), output, options)
        outputs.append(output.getvalue())
    assert outputs[0] == outputs[1]
