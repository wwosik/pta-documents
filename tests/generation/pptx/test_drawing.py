"""E06-S02: drawings (financial charts) become a group of editable shapes on a slide."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest
from lxml import etree

from pta_documents.charts import financial
from pta_documents.conversions.pptx import DRAWING_GROUP, PptxConverter
from pta_documents.design import colors
from pta_documents.design import slides as design
from pta_documents.drawing import (
    Drawing,
    DrawingHotspot,
    DrawingHover,
    DrawingPath,
    DrawingShape,
    DrawingSpan,
    DrawingText,
    LineTo,
    MoveTo,
    ShapeKind,
    TextAnchor,
)
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.pptx import drawing as writer
from tests.charts.financial import figures
from tests.generation.pptx.conftest import generate, open_pptx

A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS: Final = {"a": A, "p": P}


def block(chart: financial.FinancialChart) -> str:
    return f"```financial-chart\n{financial.to_json(chart)}\n```\n"


def groups(slide: object) -> list[etree._Element]:
    tree: etree._Element = slide.shapes._spTree  # type: ignore[attr-defined]
    return tree.findall(f"{{{P}}}grpSp")


def strings(element: etree._Element, path: str) -> list[str]:
    """The results of ``path`` (python-pptx elements know the prefixes ``a`` and ``p``)."""
    found = element.xpath(path)
    assert isinstance(found, list)
    return [str(item) for item in found]


def run_texts(element: etree._Element) -> list[str]:
    return [
        "".join(t.text or "" for t in paragraph.iter(f"{{{A}}}t"))
        for paragraph in element.iter(f"{{{A}}}p")
    ]


def test_a_financial_chart_is_a_group_of_editable_shapes(review_dir: Path) -> None:
    data = generate(f"# D\n\n## Wachstum\n\n{block(figures.growth_trend())}")
    (review_dir / "financial-chart.pptx").write_bytes(data)
    slide = open_pptx(data).slides[1]
    assert slide.slide_layout.name == design.LAYOUTS.title_only
    (group,) = groups(slide)
    properties = group.find("p:nvGrpSpPr/p:cNvPr", NS)
    assert properties is not None
    assert properties.get("name", "").startswith(DRAWING_GROUP + " ")
    assert properties.get("descr") == "financial-chart"
    found = run_texts(group)
    assert "Wachstum der Aufträge (Juli 2026)" in found
    assert "Plan 5 %" in found  # German by default
    presets = set(strings(group, ".//a:prstGeom/@prst"))
    assert {"rect", "ellipse"} >= presets and "rect" in presets
    assert group.xpath(".//a:custGeom")  # lines and polygons
    assert group.xpath(".//a:custDash")  # the dashed projection
    assert set(strings(group, ".//a:latin/@typeface")) == {design.HEADING_FONT}
    ids = strings(slide.shapes._spTree, ".//p:cNvPr/@id")
    assert len(ids) == len(set(ids))


def test_the_group_stays_in_the_content_area_and_is_never_enlarged() -> None:
    data = generate(f"# D\n\n## Übersicht\n\nText davor.\n\n{block(figures.development())}")
    slide = open_pptx(data).slides[1]
    assert slide.slide_layout.name == design.LAYOUTS.title_and_text
    (group,) = groups(slide)
    offset = group.find("p:grpSpPr/a:xfrm/a:off", NS)
    extent = group.find("p:grpSpPr/a:xfrm/a:ext", NS)
    assert offset is not None and extent is not None
    x, y = int(offset.get("x", "0")), int(offset.get("y", "0"))
    cx, cy = int(extent.get("cx", "0")), int(extent.get("cy", "0"))
    area = design.CONTENT_AREA
    assert area.left <= x and x + cx <= area.left + area.width
    assert area.top < y and y + cy <= area.bottom
    natural = financial.draw(figures.development())
    assert cy < natural.height * writer.EMU_PER_PIXEL  # scaled down to fit under the text
    small = generate(f"# D\n\n## Klein\n\n{block(figures.growth_by_row())}")
    (small_group,) = groups(open_pptx(small).slides[1])
    small_extent = small_group.find("p:grpSpPr/a:xfrm/a:ext", NS)
    assert small_extent is not None
    width = financial.draw(figures.growth_by_row()).width
    assert int(small_extent.get("cx", "0")) == int(width * writer.EMU_PER_PIXEL)


def test_the_writer_uses_powerpoints_shapes_and_leaves_hotspots_out() -> None:
    hover = DrawingHover("Spitze", 5, 5)
    drawing = Drawing(
        100,
        50,
        (
            DrawingShape(
                DrawingPath.rectangle(0, 0, 40, 20),
                colors.PTA_BLUE,
                colors.DARK_BLUE,
                1,
                kind=ShapeKind.ROUNDED_RECTANGLE,
                corner_radius=5,
            ),
            DrawingShape(
                DrawingPath((MoveTo(0, 40), LineTo(100, 40))),
                None,
                colors.GREY_MID,
                2,
                dash=(4, 2),
                round_joins=True,
            ),
            DrawingText(
                50,
                30,
                (DrawingSpan("fett", bold=True), DrawingSpan(" rot", color=colors.SIGNAL_RED)),
                12,
                colors.TEXT_SLIDES,
                anchor=TextAnchor.MIDDLE,
            ),
            DrawingText.line(0, 48, "code\x01", 8, colors.TEXT_SLIDES, mono=True),
            DrawingHotspot(5, 5, 10, hover=hover),
        ),
    )
    ids = iter(range(10, 100))
    group = writer.group(drawing, 1000, 2000, 9525, lambda: next(ids), "alt", "de-DE")
    children = group.findall("p:sp", NS)
    assert len(children) == 4  # no hotspot
    rounded = children[0].find(".//a:prstGeom", NS)
    assert rounded is not None and rounded.get("prst") == "roundRect"
    assert rounded.xpath("a:avLst/a:gd/@fmla", namespaces=NS) == ["val 25000"]
    line = children[1].find(".//a:ln", NS)
    assert line is not None and line.get("cap") == "rnd" and line.get("w") == "19050"
    assert line.xpath("a:custDash/a:ds/@d", namespaces=NS) == ["200000"]
    path = children[1].find(".//a:path", NS)
    assert path is not None and path.get("fill") == "none"
    runs = children[2].findall(".//a:r", NS)
    assert [r.findtext("a:t", namespaces=NS) for r in runs] == ["fett", " rot"]
    assert runs[0].find("a:rPr", NS).get("b") == "1"  # type: ignore[union-attr]
    assert runs[1].xpath("a:rPr/a:solidFill/a:srgbClr/@val", namespaces=NS) == ["D91E18"]
    assert runs[0].find("a:rPr", NS).get("sz") == "900"  # type: ignore[union-attr]
    assert children[2].xpath(".//a:pPr/@algn", namespaces=NS) == ["ctr"]
    mono = children[3]
    assert mono.xpath(".//a:latin/@typeface", namespaces=NS) == [design.CODE_FONT]
    assert mono.findtext(".//a:t", namespaces=NS) == "code"


def test_the_converter_leaves_the_drawing_out() -> None:
    data = generate(f"# D\n\n## Wachstum\n\nDavor.\n\n{block(figures.growth_trend())}")
    markdown = PptxConverter().convert(data).text
    assert "Davor." in markdown
    assert "Wachstum der Aufträge" not in markdown


def test_a_flow_slide_has_no_place_for_a_drawing() -> None:
    with pytest.raises(DocumentConversionError, match="financial-chart` drawing goes on a slide"):
        generate(f"# D\n\n## Dunkel {{.dark}}\n\n{block(figures.growth_trend())}")
