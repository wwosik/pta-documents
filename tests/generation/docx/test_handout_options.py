"""E16-S03: the two DOCX options the handout writes with (``figure_numbers``,
``side_by_side_columns``); both only through the API, the defaults unchanged."""

from __future__ import annotations

import io
from typing import Final

from lxml import etree
from PIL import Image

from pta_documents.generation.common.openxml import W
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.markdown import DocumentResource
from tests.generation.docx.conftest import generate, open_docx, style_name

COLUMNS: Final = """---
vorlage: hoch-ohne-deckblatt
---
::: columns 1:2

![Folie 3: Titel](bild.png)

---

Notiz zur Folie

***

| a | b |
| - | - |
| 1 | 2 |

:::

Danach
"""


def picture() -> tuple[DocumentResource, ...]:
    output = io.BytesIO()
    Image.new("RGB", (1600, 900), (0, 111, 185)).save(output, "PNG", dpi=(96, 96))
    return (DocumentResource("bild.png", "image/png", output.getvalue()),)


def body_xml(data: bytes) -> str:
    return etree.tostring(open_docx(data).element).decode()  # type: ignore[attr-defined]


def test_by_default_a_caption_has_its_number_and_columns_follow_each_other() -> None:
    data = generate(COLUMNS, resources=picture())
    document = open_docx(data)
    assert "SEQ Abbildung" in body_xml(data)
    texts = [p.text for p in document.paragraphs if p.text]
    assert texts == ["Abbildung 1: Folie 3: Titel", "Notiz zur Folie", "Danach"]
    assert [t.style.name for t in document.tables if t.style is not None] == ["PTA"]


def test_without_figure_numbers_the_caption_is_the_text_alone() -> None:
    data = generate(COLUMNS, DocxOptions(figure_numbers=False), picture())
    document = open_docx(data)
    captions = [p for p in document.paragraphs if style_name(p) == "caption"]
    assert [p.text for p in captions] == ["Folie 3: Titel"]
    assert "SEQ Abbildung" not in body_xml(data)


def test_side_by_side_columns_are_a_table_without_rules() -> None:
    data = generate(COLUMNS, DocxOptions(side_by_side_columns=True), picture())
    document = open_docx(data)
    table = document.tables[0]
    assert table.style is not None and table.style.name == "Bildreihe"
    assert len(table.rows) == 1 and len(table.columns) == 2
    left, right = table.rows[0].cells
    assert left.width is not None and right.width is not None
    assert abs(right.width - 2 * left.width) < 2000  # rounded to twips
    # the picture fits its cell, its caption below it
    assert [p.text for p in left.paragraphs] == ["", "Abbildung 1: Folie 3: Titel"]
    extent = left._tc.find(f".//{{{W}}}drawing//*[@cx]")
    assert extent is not None and int(extent.get("cx", "0")) <= left.width
    # '***' stays a rule in its column, the Markdown table goes into the cell
    assert right.paragraphs[0].text == "Notiz zur Folie"
    rule = right.paragraphs[1]._p.find(f"{{{W}}}pPr/{{{W}}}pBdr/{{{W}}}bottom")
    assert rule is not None
    assert len(right.tables) == 1 and right.tables[0].cell(1, 1).text == "2"
    # after the container the body goes on
    assert document.paragraphs[-1].text == "Danach"
    row = table.rows[0]._tr.find(f"{{{W}}}trPr/{{{W}}}cantSplit")
    assert row is not None
