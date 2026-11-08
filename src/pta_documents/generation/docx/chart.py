"""Native Word charts from a ``ChartSpec`` (E06-S01).

python-docx has no charts, so the chart XML comes from python-pptx (``ChartXmlWriter`` through
``CategoryChartData.xml_bytes``) in the PTA style of ``generation/common/native_chart.py``: a part
``word/charts/chartN.xml`` related from the document, its data as a workbook under
``word/embeddings/`` (``c:externalData``, so that Word's "Daten bearbeiten" opens it), placed
inline as ``c:chart`` over the text width in the proportions of the chart drawing (640:380).
"""

from __future__ import annotations

from typing import Any, Final

from docx.opc.constants import CONTENT_TYPE as CT
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.part import Part
from docx.text.paragraph import Paragraph
from lxml import etree
from pptx.chart.chart import Chart
from pptx.oxml import parse_xml

from pta_documents.charts import drawing
from pta_documents.charts.spec import ChartSpec
from pta_documents.design import colors
from pta_documents.generation.common import native_chart
from pta_documents.generation.common.openxml import R, w

STYLE: Final = native_chart.ChartStyle("Segoe UI", 10, colors.TEXT_WORD)
"""Text 10 pt Segoe UI black, like the Word templates."""
CHART_PARTNAME: Final = "/word/charts/chart%d.xml"
WORKBOOK_PARTNAME: Final = "/word/embeddings/Microsoft_Excel_Worksheet%d.xlsx"

WP: Final = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
C: Final = "http://schemas.openxmlformats.org/drawingml/2006/chart"


def chart_xml(spec: ChartSpec) -> Any:
    """The ``c:chartSpace`` of ``spec`` in the PTA style for Word: no title in the chart (the
    caption below names it), the unit as the title of the value axis."""
    chart_space = parse_xml(native_chart.chart_data(spec).xml_bytes(native_chart.chart_type(spec)))
    native_chart.apply_style(
        Chart(chart_space, None),
        spec,
        STYLE,
        title=None,
        unit=spec.unit,
    )
    return chart_space


def add_chart(paragraph: Paragraph, spec: ChartSpec, width: int, alt: str) -> None:
    """``spec`` as a native chart in a new run of ``paragraph``, ``width`` EMU wide."""
    part = paragraph.part
    package = part.package
    assert package is not None
    chart_space = chart_xml(spec)

    workbook = Part(
        package.next_partname(WORKBOOK_PARTNAME),
        CT.SML_SHEET,
        native_chart.chart_data(spec).xlsx_blob,
        package,
    )
    chart_part = Part(package.next_partname(CHART_PARTNAME), CT.DML_CHART, b"", package)
    chart_rid = part.relate_to(chart_part, RT.CHART)
    workbook_rid = chart_part.relate_to(workbook, RT.PACKAGE)
    external = chart_space.get_or_add_externalData()
    external.rId = workbook_rid
    external.get_or_add_autoUpdate().set("val", "0")
    chart_part._blob = etree.tostring(
        chart_space, xml_declaration=True, encoding="UTF-8", standalone=True
    )

    height = round(width * drawing.HEIGHT / drawing.WIDTH)
    shape_id = part.next_id
    run = etree.SubElement(paragraph._p, w("r"))
    run.append(_inline(chart_rid, width, height, shape_id, alt))


def _inline(rid: str, width: int, height: int, shape_id: int, alt: str) -> etree._Element:
    drawing_element = etree.Element(w("drawing"))
    inline = etree.SubElement(drawing_element, f"{{{WP}}}inline", nsmap={"wp": WP})
    for side in ("distT", "distB", "distL", "distR"):
        inline.set(side, "0")
    extent = etree.SubElement(inline, f"{{{WP}}}extent")
    extent.set("cx", str(width))
    extent.set("cy", str(height))
    effect = etree.SubElement(inline, f"{{{WP}}}effectExtent")
    for side in ("l", "t", "r", "b"):
        effect.set(side, "0")
    doc_pr = etree.SubElement(inline, f"{{{WP}}}docPr")
    doc_pr.set("id", str(shape_id))
    doc_pr.set("name", f"Diagramm {shape_id}")
    if alt:
        doc_pr.set("descr", alt)
    etree.SubElement(inline, f"{{{WP}}}cNvGraphicFramePr")
    graphic = etree.SubElement(inline, f"{{{A}}}graphic", nsmap={"a": A})
    data = etree.SubElement(graphic, f"{{{A}}}graphicData")
    data.set("uri", C)
    chart = etree.SubElement(data, f"{{{C}}}chart", nsmap={"c": C, "r": R})
    chart.set(f"{{{R}}}id", rid)
    return drawing_element
