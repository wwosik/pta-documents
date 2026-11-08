"""E06-S01: ``chart`` blocks become native Word charts with an embedded workbook."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Any, cast

import pytest
from lxml import etree

from pta_documents.design import colors
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.openxml import W
from pta_documents.generation.docx.options import DocxOptions
from tests.charts.test_parser import ORDERS
from tests.generation.docx.conftest import generate, open_docx, parts

C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
NS = {"c": C, "a": A, "r": R, "w": W, "wp": WP}
FRONT = "---\ntitel: Bericht\n---\n\n"


def report(body: str) -> bytes:
    return generate(FRONT + body)


def test_a_native_chart_part_with_an_embedded_workbook(review_dir: Path) -> None:
    line = "type: line\n---\nQuartal; Plan; Ist\nQ1; 1,5; 2\nQ2; 2,5;\n"
    data = report(f"# Zahlen\n\n```chart\n{ORDERS}```\n\n```chart\n{line}```\n")
    (review_dir / "chart.docx").write_bytes(data)
    files = parts(data)
    assert {"word/charts/chart1.xml", "word/charts/chart2.xml"} <= files.keys()
    workbooks = sorted(n for n in files if n.startswith("word/embeddings/"))
    assert workbooks == [
        "word/embeddings/Microsoft_Excel_Worksheet1.xlsx",
        "word/embeddings/Microsoft_Excel_Worksheet2.xlsx",
    ]
    with zipfile.ZipFile(io.BytesIO(files[workbooks[0]])) as workbook:
        assert "xl/worksheets/sheet1.xml" in workbook.namelist()
    rels = files["word/charts/_rels/chart1.xml.rels"].decode()
    assert "Microsoft_Excel_Worksheet1.xlsx" in rels and "relationships/package" in rels
    types = files["[Content_Types].xml"].decode()
    assert "drawingml.chart+xml" in types

    chart = etree.fromstring(files["word/charts/chart1.xml"])
    rid = chart.xpath("/c:chartSpace/c:externalData/@r:id", namespaces=NS)
    assert rid == ["rId1"]
    assert chart.xpath("//c:barChart/c:grouping/@val", namespaces=NS) == ["clustered"]
    assert chart.xpath("//c:ser/c:tx//c:v/text()", namespaces=NS) == ["plan", "actual"]
    assert chart.xpath("//c:ser[2]/c:val//c:pt/c:v/text()", namespaces=NS) == ["132.0", "121.0"]
    # Word: the title is the caption, not in the chart; the unit titles the value axis.
    assert chart.xpath("/c:chartSpace/c:chart/c:title", namespaces=NS) == []
    assert chart.xpath("//c:valAx/c:title//a:t/text()", namespaces=NS) == ["k"]
    assert chart.xpath("/c:chartSpace/c:txPr//a:defRPr/@sz", namespaces=NS) == ["1000"]
    assert chart.xpath("/c:chartSpace/c:txPr//a:srgbClr/@val", namespaces=NS) == [colors.TEXT_WORD]
    assert chart.xpath("/c:chartSpace/c:txPr//a:latin/@typeface", namespaces=NS) == ["Segoe UI"]
    second = etree.fromstring(files["word/charts/chart2.xml"])
    assert second.xpath("//c:ser[1]/c:val//c:pt/c:v/text()", namespaces=NS) == ["1.5", "2.5"]

    # It opens with python-docx, inline over the text width at 8:5 (E03-S04).
    document = open_docx(data)
    body: Any = cast(Any, document.element).body
    inlines = body.xpath(".//wp:inline[.//c:chart]")
    assert len(inlines) == 2
    extent = inlines[0].find(f"{{{WP}}}extent")
    section = document.sections[0]
    width = int(section.page_width or 0) - int(section.left_margin or 0)
    width -= int(section.right_margin or 0)
    assert int(extent.get("cx")) == width
    assert int(extent.get("cy")) == round(width * 5 / 8)
    ids = body.xpath(".//wp:docPr/@id")
    assert len(ids) == len(set(ids))
    chart_rid = inlines[0].xpath(".//c:chart/@r:id")[0]
    assert document.part.rels[chart_rid].target_part.partname == "/word/charts/chart1.xml"


def test_title_and_source_below_the_chart() -> None:
    texts = [p.text for p in open_docx(report(f"# Zahlen\n\n```chart\n{ORDERS}```\n")).paragraphs]
    i = texts.index("Abbildung 1: Orders by month")
    assert texts[i + 1] == "Quelle: erfunden"
    paragraphs = open_docx(report(f"# Zahlen\n\n```chart\n{ORDERS}```\n")).paragraphs
    styles = [p.style.name if p.style is not None else None for p in paragraphs[i : i + 2]]
    assert styles[0] == styles[1] is not None


def test_without_title_there_is_no_caption() -> None:
    texts = [p.text for p in open_docx(report("```chart\nx, a\n1, 2\n```\n")).paragraphs]
    assert not any(t.startswith("Abbildung") for t in texts)


def test_a_data_mistake_is_a_document_conversion_error_with_its_line() -> None:
    with pytest.raises(DocumentConversionError) as error:
        report("```chart\nx, a\n1, lots\n```\n")
    assert error.value.format is DocumentFormat.DOCX
    assert error.value.reason.startswith("Line 7: The chart block cannot be drawn: 'lots'")


def test_without_the_renderer_the_block_stays_code() -> None:
    data = generate(FRONT + "```chart\nx, a\n1, 2\n```\n", DocxOptions(code_block_renderers=()))
    assert not any(n.startswith("word/charts/") for n in parts(data))
