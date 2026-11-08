"""E15-S02: steps and the risk matrix as pictures in Word, Harvey balls as characters."""

from __future__ import annotations

from typing import Final

from lxml import etree

from pta_documents.conversions.docx import DocxConverter
from pta_documents.design import colors, word
from pta_documents.drawing import steps as steps_drawing
from tests.generation.common.visual_blocks import RATING, RISKS, STEPS
from tests.generation.docx.conftest import generate, open_docx
from tests.generation.docx.test_schedule import FRONT, body, w

LONG: Final = "Ein sehr langer Text mit vielen Wörtern, der unter keinen Pfeil passt " * 3


def test_steps_are_a_picture_as_wide_as_the_text() -> None:
    document = open_docx(generate(FRONT + STEPS))
    (shape,) = document.inline_shapes
    section = document.sections[0]
    text_width = (
        int(section.page_width or 0)
        - int(section.left_margin or 0)
        - int(section.right_margin or 0)
    )
    assert abs(int(shape.width) - text_width) < 9525
    xml = etree.tostring(document.element).decode()
    assert 'descr="1. Analyse: Interviews und Ist-Aufnahme; 2. Konzept: Soll-Bild' in xml
    assert not [
        p for p in document.paragraphs if p.style is not None and p.style.name == "List Bullet"
    ]


def test_texts_that_do_not_fit_follow_as_a_list() -> None:
    markdown = STEPS.replace("In Sprints", LONG)
    document = open_docx(generate(FRONT + markdown))
    assert len(document.inline_shapes) == 1
    items = [
        p for p in document.paragraphs if p.style is not None and p.style.name == "List Bullet"
    ]
    assert [p.runs[0].text for p in items] == [
        "Analyse",
        "Konzept",
        "Umsetzung",
        "Abnahme",
        "Betrieb",
    ]
    assert items[0].runs[0].bold and items[0].text == "Analyse: Interviews und Ist-Aufnahme"
    assert items[3].text == "Abnahme"


def test_texts_are_tried_at_12_then_10_pt() -> None:
    assert word.STEPS_TEXT_PT == (12, 10)
    assert steps_drawing.STEPS.min_text_pt == 10


def test_harvey_balls_are_characters_in_pta_blue() -> None:
    tbl = body(RATING).find(w("tbl"))
    assert tbl is not None
    cell = tbl.findall(w("tr"))[1].findall(w("tc"))[1]
    run = cell.find(f".//{w('r')}")
    assert run is not None
    assert run.findtext(w("t")) == "\u25d5"
    fonts = run.find(f"{w('rPr')}/{w('rFonts')}")
    assert fonts is not None and fonts.get(w("ascii")) == word.HARVEY_FONT == "Segoe UI Symbol"
    color = run.find(f"{w('rPr')}/{w('color')}")
    assert color is not None and color.get(w("val")) == colors.PTA_BLUE
    jc = cell.find(f".//{w('jc')}")
    assert jc is not None and jc.get(w("val")) == "center"
    text = DocxConverter().convert(generate(FRONT + RATING)).text
    assert "| Kosten | ◕ | ◔ |" in text and "| Zeit | ○ | ● |" in text


def test_the_risk_matrix_is_a_picture_with_its_legend_below() -> None:
    document = open_docx(generate(FRONT + RISKS))
    (shape,) = document.inline_shapes
    assert abs(int(shape.width) - (5 * 1.6 + 0.48) * 360000) < 0.1 * 360000
    (table,) = document.tables
    assert [c.text for c in table.rows[0].cells] == ["Nr", "Risiko", "Maßnahme"]
    assert [c.text for c in table.rows[1].cells] == ["1", "Ausfall", "Vertretung"]
    assert table.style is not None and table.style.name == word.STYLES.table
    text = DocxConverter().convert(generate(FRONT + RISKS)).text
    assert text.index("![1 Ausfall") < text.index("| 1 | Ausfall | Vertretung |")
