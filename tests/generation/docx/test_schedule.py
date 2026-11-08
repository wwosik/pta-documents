"""E15-S01: in Word a timeline is a picture as wide as the text, a Gantt chart a table."""

from __future__ import annotations

import datetime as dt
from typing import Final

import pytest
from lxml import etree

from pta_documents.conversions.docx import DocxConverter
from pta_documents.design import colors, word
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.common.openxml import W
from pta_documents.generation.docx.options import DocxOptions
from tests.generation.common.test_schedule import GANTT, TIMELINE, table
from tests.generation.docx.conftest import generate, open_docx

OPTIONS: Final = DocxOptions(date=dt.date(2026, 3, 15))
FRONT: Final = "---\ntitel: Plan\n---\n"


def w(name: str) -> str:
    return f"{{{W}}}{name}"


def body(markdown: str, options: DocxOptions = OPTIONS) -> etree._Element:
    return open_docx(generate(FRONT + markdown, options)).element.body  # type: ignore[no-any-return]


def gantt_table(markdown: str = GANTT) -> etree._Element:
    tables = body(markdown).findall(w("tbl"))
    assert len(tables) == 1
    return tables[0]


def cell_fill(cell: etree._Element) -> str | None:
    shading = cell.find(f"{w('tcPr')}/{w('shd')}")
    return None if shading is None else str(shading.get(w("fill")))


def cell_text(cell: etree._Element) -> str:
    return "".join(t.text or "" for t in cell.iter(w("t")))


def test_the_gantt_chart_is_a_table_in_the_pta_style() -> None:
    document = open_docx(generate(FRONT + GANTT, OPTIONS))
    (tbl,) = document.tables
    assert tbl.style is not None and tbl.style.name == word.STYLES.table
    rows = tbl._tbl.findall(w("tr"))
    assert len(rows) == 5
    assert all(len(r.findall(w("tc"))) == 2 + 7 for r in rows)
    assert [cell_text(c) for c in rows[0].findall(w("tc"))] == [
        "Vorgang",
        "Wer",
        "Jan 26",
        "Feb",
        "Mär",
        "Apr",
        "Mai",
        "Jun",
        "Jul",
    ]
    assert rows[0].find(f"{w('trPr')}/{w('tblHeader')}") is not None


def test_the_columns_a_task_runs_in_are_shaded() -> None:
    rows = gantt_table().findall(w("tr"))
    fills = [[cell_fill(c) for c in r.findall(w("tc"))[2:]] for r in rows[1:]]
    blue, light = colors.PTA_BLUE, colors.LIGHT_BLUE
    assert fills == [
        [blue, blue, None, None, None, None, None],
        [None, None, blue, blue, blue, blue, None],
        [None, None, None, None, None, None, light],
        [None] * 7,
    ]
    milestone = rows[4].findall(w("tc"))[-1]
    assert cell_text(milestone) == word.GANTT_MILESTONE
    assert milestone.find(f".//{w('color')}").get(w("val")) == colors.DARK_BLUE  # type: ignore[union-attr]


def test_the_column_of_today_has_a_dark_blue_rule_on_its_right() -> None:
    rows = gantt_table().findall(w("tr"))
    for row in rows:
        cells = row.findall(w("tc"))
        march = cells[2 + 2]
        rule = march.find(f"{w('tcPr')}/{w('tcBorders')}/{w('right')}")
        assert rule is not None and rule.get(w("color")) == colors.DARK_BLUE
        assert all(c.find(f"{w('tcPr')}/{w('tcBorders')}") is None for c in cells if c is not march)
        # Schema order: width, borders, shading.
        names = [etree.QName(e).localname for e in march.find(w("tcPr"))]  # type: ignore[union-attr]
        assert names.index("tcBorders") > names.index("tcW")
        if "shd" in names:
            assert names.index("shd") > names.index("tcBorders")


def test_three_columns_make_no_owner_column_and_the_widths_fill_the_text() -> None:
    tbl = gantt_table(table([("A", "2026-01-07", "2026-01-20")]))
    grid = [int(str(g.get(w("w")))) for g in tbl.iter(w("gridCol"))]
    assert len(grid) == 1 + 3
    assert abs(sum(grid) - int(str(tbl.find(f"{w('tblPr')}/{w('tblW')}").get(w("w"))))) <= 5  # type: ignore[union-attr]
    header = [cell_text(c) for c in tbl.find(w("tr")).findall(w("tc"))]  # type: ignore[union-attr]
    assert header == ["Vorgang", "KW 02", "KW 03", "KW 04"]


def test_the_timeline_is_a_picture_as_wide_as_the_text() -> None:
    document = open_docx(generate(FRONT + TIMELINE, OPTIONS))
    (shape,) = document.inline_shapes
    section = document.sections[0]
    text_width = (
        int(section.page_width or 0)
        - int(section.left_margin or 0)
        - int(section.right_margin or 0)
    )
    assert abs(int(shape.width) - text_width) < 9525
    xml = etree.tostring(document.element).decode()
    assert "svgBlip" in xml
    assert 'descr="2026-01: Kick-off; 2026-Q2: Analyse abgeschlossen' in xml


def test_without_an_svg_converter_the_timeline_is_an_error() -> None:
    with pytest.raises(DocumentConversionError, match="no image converter takes SVG"):
        generate(FRONT + TIMELINE, DocxOptions(image_converters=()))


@pytest.mark.parametrize(
    ("markdown", "message"),
    [
        (table([("A", "2026-01", "2026-12")], "raster=woche"), "Line 4: The grid of the"),
        (table([("A", "2026-01", "2026-02")] * 13), "Line 4: A '::: gantt' has 1 to 12 tasks"),
        ("::: timeline\n- 2026: A\n- x: B\n:::\n", "Line 6: 'x' is no date"),
    ],
)
def test_mistakes_name_their_line(markdown: str, message: str) -> None:
    with pytest.raises(DocumentConversionError, match=message):
        generate(FRONT + markdown, OPTIONS)


def test_the_converter_reads_the_table_back_with_filled_cells() -> None:
    text = DocxConverter().convert(generate(FRONT + GANTT, OPTIONS)).text
    assert "| Analyse | PTA | ■ | ■ |  |  |  |  |  |" in text
    assert "| Go-live |  |  |  |  |  |  |  | ◆ |" in text
