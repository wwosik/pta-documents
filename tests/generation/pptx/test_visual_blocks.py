"""E15-S02: steps, Harvey balls and the risk matrix on slides, as editable shapes."""

from __future__ import annotations

from typing import Any, Final

import pytest
from lxml import etree

from pta_documents.conversions.pptx import PptxConverter
from pta_documents.design import colors
from pta_documents.design import slides as design
from pta_documents.errors import DocumentConversionError
from tests.generation.common.visual_blocks import RATING, RISKS, STEPS
from tests.generation.pptx.conftest import generate, open_pptx
from tests.generation.pptx.test_schedule import deck, frame, groups

A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"


def presets(group: etree._Element) -> list[tuple[str, dict[str, str]]]:
    result: list[tuple[str, dict[str, str]]] = []
    for geometry in group.iter(f"{{{A}}}prstGeom"):
        guides = {str(g.get("name")): str(g.get("fmla")) for g in geometry.iter(f"{{{A}}}gd")}
        result.append((str(geometry.get("prst")), guides))
    return result


def name(group: etree._Element) -> str:
    return str(group.find(f"{{{P}}}nvGrpSpPr/{{{P}}}cNvPr").get("name"))  # type: ignore[union-attr]


def test_steps_are_chevrons_across_the_content_area() -> None:
    (group,) = groups(generate(deck(STEPS)))
    x, _, width, _ = frame(group)
    area = design.CONTENT_AREA
    assert x == area.left and abs(width - area.width) <= 1
    shapes = [p for p in presets(group) if p[0] in ("chevron", "homePlate")]
    assert [p[0] for p in shapes] == ["homePlate"] + ["chevron"] * 4
    assert all(p[1]["adj"].startswith("val ") for p in shapes)
    xml = etree.tostring(group).decode()
    assert xml.count(colors.GREY_LIGHT) == 2 and colors.PTA_BLUE in xml
    assert "Interviews und Ist-Aufnahme" in xml


def test_seven_steps_are_an_error() -> None:
    body = "::: steps\n" + "".join(f"### S{n}\n" for n in range(7)) + ":::\n"
    with pytest.raises(DocumentConversionError, match="Line 5: A '::: steps' has 3 to 6 steps"):
        generate(deck(body))


def test_harvey_balls_are_pie_shapes_over_their_cells() -> None:
    data = generate(deck(RATING))
    balls = [g for g in groups(data) if name(g).startswith("harvey-")]
    assert [name(g) for g in balls] == ["harvey-3", "harvey-1", "harvey-0", "harvey-4"]
    three = presets(balls[0])
    assert ("pie", {"adj1": "val 16200000", "adj2": "val 10800000"}) in three
    assert [p[0] for p in presets(balls[2])] == ["ellipse", "ellipse"]
    size = frame(balls[0])[2]
    assert abs(size - 0.45 * 360000) < 2000
    # The cells themselves are empty and centred.
    tree: etree._Element = open_pptx(data).slides[1].shapes._spTree  # type: ignore[attr-defined]
    table = tree.find(f".//{{{A}}}tbl")
    assert table is not None
    cells = table.findall(f"{{{A}}}tr")[1].findall(f"{{{A}}}tc")
    assert cells[1].findtext(f".//{{{A}}}t") is None
    alignment = cells[1].find(f".//{{{A}}}pPr")
    assert alignment is not None and alignment.get("algn") == "ctr"


def test_the_converter_reads_harvey_balls_back() -> None:
    text = PptxConverter().convert(generate(deck(RATING))).text
    assert "| Kosten | [3/4] | [1/4] |" in text
    assert "| Zeit | [0/4] | [4/4] |" in text


def test_the_risk_matrix_has_its_legend_to_its_right() -> None:
    data = generate(deck(RISKS))
    (group,) = groups(data)
    x, y, width, _ = frame(group)
    assert x == design.CONTENT_AREA.left and y == design.CONTENT_AREA.top
    assert abs(width - (5 * 1.6 + 0.48) * 360000) < 0.1 * 360000
    xml = etree.tostring(group).decode()
    for signal in colors.SIGNALS:
        assert colors.tint(signal, 0.35) in xml
    tables: list[Any] = [s for s in open_pptx(data).slides[1].shapes if s.has_table]  # type: ignore[attr-defined]
    (legend,) = tables
    assert legend.left >= x + width + design.COLUMN_GAP
    assert [c.text for c in legend.table.rows[0].cells] == ["Nr", "Risiko", "Maßnahme"]
    assert [c.text for c in legend.table.rows[3].cells] == ["3", "Schnittstelle", "Mock"]


def test_in_a_narrow_column_the_legend_goes_below() -> None:
    body = f":::: columns 1:1:1\n{RISKS}\n---\n\nText.\n\n---\n\nMehr.\n::::\n"
    data = generate(deck(body))
    (group,) = groups(data)
    _, y, _, height = frame(group)
    (legend,) = [s for s in open_pptx(data).slides[1].shapes if s.has_table]  # type: ignore[attr-defined]
    assert legend.top > y + height


def test_a_value_out_of_range_is_an_error() -> None:
    with pytest.raises(DocumentConversionError, match="Line 8: The Wahrscheinlichkeit of risk 1"):
        generate(deck(RISKS.replace("| 2                  | 4  ", "| 0                  | 4  ")))
