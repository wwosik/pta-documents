"""E06-S01: ``chart`` blocks become native PowerPoint charts in the PTA chart style."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Any, cast

import pytest
from lxml import etree

from pta_documents.design import colors
from pta_documents.design import slides as design
from pta_documents.errors import DocumentConversionError, DocumentFormat
from tests.charts.test_parser import ORDERS
from tests.generation.pptx.conftest import generate, open_pptx, texts

C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"c": C, "a": A}
LINE = "type: line\ntitle: Zweiter\n---\nx, a\n1, 2\n2, 3\n"


def deck(body: str) -> bytes:
    return generate(f"# D\n\n{body}")


def charts(slide: Any) -> list[Any]:
    return [shape for shape in slide.shapes if getattr(shape, "has_chart", False)]


def chart_xml(data: bytes, n: int = 1) -> etree._Element:
    with zipfile.ZipFile(io.BytesIO(data)) as package:
        return etree.fromstring(package.read(f"ppt/charts/chart{n}.xml"))


def test_a_native_chart_with_its_data_in_an_embedded_workbook(review_dir: Path) -> None:
    data = deck(f"## Aufträge\n\n```chart\n{ORDERS}```\n")
    (review_dir / "chart-orders.pptx").write_bytes(data)
    slide = open_pptx(data).slides[1]
    assert slide.slide_layout.name == design.LAYOUTS.chart
    (frame,) = charts(slide)
    chart = frame.chart
    workbook = chart.part.chart_workbook.xlsx_part
    assert workbook is not None and workbook.blob.startswith(b"PK")
    root = chart_xml(data)
    assert root.xpath("//c:barChart/c:grouping/@val", namespaces=NS) == ["clustered"]
    assert [s.name for s in chart.plots[0].series] == ["plan", "actual"]
    assert chart.plots[0].series[1].values == (132, 121, None)
    found = texts(slide)
    placeholders = design.PLACEHOLDERS
    assert found[placeholders.chart_title] == "Orders by month"
    assert found[placeholders.chart_unit] == "k"
    assert found[placeholders.chart_source] == "Quelle: erfunden"
    assert not chart.has_title


def test_the_pta_chart_style() -> None:
    root = chart_xml(deck(f"## A\n\n```chart\n{ORDERS}```\n"))

    def values(path: str) -> list[Any]:
        return cast(list[Any], root.xpath(path, namespaces=NS))

    assert values("//c:barChart/c:gapWidth/@val") == ["60"]
    assert values("/c:chartSpace/c:txPr//a:defRPr/@sz") == ["1400"]
    assert values("/c:chartSpace/c:txPr//a:latin/@typeface") == [design.BODY_FONT]
    assert values("/c:chartSpace/c:txPr//a:srgbClr/@val") == [colors.TEXT_SLIDES]
    assert set(values("//c:majorTickMark/@val") + values("//c:minorTickMark/@val")) == {"none"}
    assert values("//c:catAx/c:spPr/a:ln/@w") == [str(6350)]  # 0.5 pt
    assert values("//c:catAx/c:spPr/a:ln//a:srgbClr/@val") == [colors.GREY_MID]
    assert values("//c:valAx/c:majorGridlines//a:srgbClr/@val") == [colors.GREY_LIGHT]
    assert values("//c:valAx/c:spPr/a:ln/a:noFill") != []
    assert values("//c:legend/c:legendPos/@val") == ["b"]
    assert values("//c:ser/c:spPr/a:solidFill/a:srgbClr/@val") == list(colors.ACCENTS[:2])
    assert values("//c:valAx/c:scaling/c:min/@val") == ["0.0"]


@pytest.mark.parametrize(
    ("settings", "element", "grouping"),
    [
        ("type: bar\nstacked: true", "barChart", "stacked"),
        ("type: line", "lineChart", "standard"),
        ("type: area", "areaChart", "standard"),
        ("type: area\nstacked: true", "areaChart", "stacked"),
    ],
)
def test_the_kinds(settings: str, element: str, grouping: str) -> None:
    root = chart_xml(deck(f"## A\n\n```chart\n{settings}\n---\nx, a, b\n1, 2, 3\n2, 4, 1\n```\n"))
    assert root.xpath(f"//c:{element}/c:grouping/@val", namespaces=NS) == [grouping]


def test_two_charts_stand_side_by_side_in_columns() -> None:
    body = f"## Zwei\n\n::: columns\n```chart\n{ORDERS}```\n\n---\n\n```chart\n{LINE}```\n:::\n"
    slide = open_pptx(deck(body)).slides[1]
    assert slide.slide_layout.name == design.LAYOUTS.two_charts
    left, right = charts(slide)
    assert left.top == right.top
    assert right.left >= left.left + left.width
    assert texts(slide)[design.PLACEHOLDERS.second_chart[0]] == "Zweiter"


def test_a_named_layout_shows_title_and_unit_in_the_chart() -> None:
    data = deck(f'## A {{layout="{design.LAYOUTS.chart}"}}\n\n```chart\n{ORDERS}```\n')
    (frame,) = charts(open_pptx(data).slides[1])
    assert frame.chart.has_title
    assert frame.chart.chart_title.text_frame.text == "Orders by month"
    assert frame.chart.value_axis.axis_title.text_frame.text == "k"


def test_a_data_mistake_is_a_document_conversion_error_with_its_line() -> None:
    with pytest.raises(DocumentConversionError) as error:
        deck("## X\n\n```chart\n---\nx, a\n1, lots\n```\n")
    assert error.value.format is DocumentFormat.PPTX
    assert error.value.reason.startswith("Line 8: The chart block cannot be drawn: 'lots'")
    assert isinstance(error.value.__cause__, ValueError)
