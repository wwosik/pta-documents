"""E15-S01: ``::: timeline`` and ``::: gantt`` as groups of editable shapes on flow slides."""

from __future__ import annotations

import datetime as dt
from typing import Final

import pytest
from lxml import etree

from pta_documents.conversions.pptx import PptxConverter
from pta_documents.design import colors
from pta_documents.design import slides as design
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.pptx.options import PptxOptions
from tests.generation.common.test_schedule import GANTT, TIMELINE, table
from tests.generation.pptx.conftest import generate, open_pptx

A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
OPTIONS: Final = PptxOptions(date=dt.date(2026, 3, 15))


def deck(body: str) -> str:
    return f"# Deck\n\n## Plan\n\n{body}"


def groups(data: bytes, slide: int = 1) -> list[etree._Element]:
    tree: etree._Element = open_pptx(data).slides[slide].shapes._spTree  # type: ignore[attr-defined]
    return tree.findall(f"{{{P}}}grpSp")


def fills(group: etree._Element) -> list[str]:
    return [
        str(e.get("val"))
        for e in group.iter(f"{{{A}}}srgbClr")
        if e.getparent() is not None and e.getparent().getparent().tag == f"{{{P}}}spPr"  # type: ignore[union-attr]
    ]


def frame(group: etree._Element) -> tuple[int, int, int, int]:
    transform = group.find(f"{{{P}}}grpSpPr/{{{A}}}xfrm")
    assert transform is not None
    off, ext = transform.find(f"{{{A}}}off"), transform.find(f"{{{A}}}ext")
    assert off is not None and ext is not None
    return int(off.get("x", 0)), int(off.get("y", 0)), int(ext.get("cx", 0)), int(ext.get("cy", 0))


@pytest.mark.parametrize("body", [TIMELINE, GANTT], ids=["timeline", "gantt"])
def test_the_block_is_a_group_of_shapes_across_the_content_area(body: str) -> None:
    data = generate(deck(body), OPTIONS)
    presentation = open_pptx(data)
    assert presentation.slides[1].slide_layout.name == design.LAYOUTS.title_only
    (group,) = groups(data)
    x, y, width, height = frame(group)
    area = design.CONTENT_AREA
    assert (x, y) == (area.left, area.top)
    assert abs(width - area.width) <= 1
    assert height <= area.height
    shapes = group.findall(f"{{{P}}}sp")
    assert len(shapes) > 10  # every mark, bar, line and label on its own
    names = {str(s.find(f"{{{P}}}nvSpPr/{{{P}}}cNvPr").get("name")).split()[0] for s in shapes}  # type: ignore[union-attr]
    assert "Text" in names


def test_timeline_heights_follow_their_content() -> None:
    (timeline,) = groups(generate(deck(TIMELINE), OPTIONS))
    (gantt,) = groups(generate(deck(GANTT), OPTIONS))
    cm = 360000
    assert 2 * cm < frame(timeline)[3] < 5 * cm
    # 0.9 cm a task and a heading row.
    assert abs(frame(gantt)[3] - (4 * 0.9 * cm + 0.85 * cm)) < 0.1 * cm


def test_past_and_done_entries_are_grey() -> None:
    (group,) = groups(generate(deck(TIMELINE), OPTIONS))
    ellipses = [
        s
        for s in group.findall(f"{{{P}}}sp")
        if s.find(f"{{{P}}}spPr/{{{A}}}prstGeom[@prst='ellipse']") is not None
    ]
    colours = [
        str(e.find(f"{{{P}}}spPr/{{{A}}}solidFill/{{{A}}}srgbClr").get("val"))  # type: ignore[union-attr]
        for e in ellipses
    ]
    assert colours == [colors.GREY_DARK, colors.GREY_DARK, colors.PTA_BLUE, colors.PTA_BLUE]


def test_the_gantt_chart_has_its_bars_and_today() -> None:
    (group,) = groups(generate(deck(GANTT), OPTIONS))
    xml = etree.tostring(group).decode()
    assert xml.count('prst="rect"') >= 3
    assert "custDash" in xml
    assert colors.LIGHT_BLUE in xml and colors.DARK_BLUE in xml


def test_text_before_and_after_stacks_with_the_block() -> None:
    data = generate(deck(f"Vorher.\n\n{GANTT}\nNachher.\n"), OPTIONS)
    slide = open_pptx(data).slides[1]
    texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame and s.text_frame.text]  # type: ignore[attr-defined]
    assert "Vorher." in texts and "Nachher." in texts
    assert len(groups(data)) == 1


def test_a_full_slide_continues_on_the_next() -> None:
    rows = [(f"Vorgang {n}", "2026-01", "2026-02") for n in range(12)]
    body = "\n\n".join(["Ein Absatz mit Text."] * 6) + "\n\n" + table(rows)
    data = generate(deck(body), OPTIONS)
    assert len(open_pptx(data).slides) == 3


def test_mistakes_name_their_line() -> None:
    with pytest.raises(DocumentConversionError, match=r"Line 7: 'Q7' is no date"):
        generate(deck("::: timeline\n- 2026: A\n- Q7: B\n:::\n"), OPTIONS)


def test_the_converter_leaves_the_drawing_out() -> None:
    data = generate(deck(f"Text.\n\n{TIMELINE}"), OPTIONS)
    text = PptxConverter().convert(data).text
    assert "Kick-off" not in text and "Text." in text
