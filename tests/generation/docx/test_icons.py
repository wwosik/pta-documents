"""E15-S03: icons in Word — pictures in the text and as the bullets of a list."""

from __future__ import annotations

import io
from typing import Final

import pytest
from lxml import etree

from pta_documents.conversions.docx import DocxConverter
from pta_documents.design import colors, word
from pta_documents.design.icons import raster
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.common.openxml import W
from pta_documents.generation.common.result import NoteCodes
from pta_documents.generation.docx import writer
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.markdown import MarkdownDocument
from tests.generation.docx.conftest import generate, open_docx, parts

WP: Final = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
SVG_BLIP: Final = "{http://schemas.microsoft.com/office/drawing/2016/SVG/main}svgBlip"
EMU_PER_POINT: Final = 12700
FRONT: Final = "---\ntitel: Bericht\n---\n\n"
BULLETS: Final = (
    "- :icon-check: Erledigt\n- :icon-clock: Offen\n  - darunter\n- :icon-x: Verworfen\n"
)


def body(data: bytes) -> etree._Element:
    return etree.fromstring(parts(data)["word/document.xml"])


def w(name: str) -> str:
    return f"{{{W}}}{name}"


def icon_runs(data: bytes) -> list[etree._Element]:
    return [
        run
        for run in body(data).iter(w("r"))
        if any(str(d.get("descr", "")).startswith("icon:") for d in run.iter(f"{{{WP}}}docPr"))
    ]


def test_an_icon_in_text_is_a_picture_as_high_as_the_text() -> None:
    data = generate(FRONT + "Der Server :icon-server: läuft.\n")
    (run,) = icon_runs(data)
    doc_pr = next(run.iter(f"{{{WP}}}docPr"))
    assert doc_pr.get("descr") == "icon:server"
    extent = next(run.iter(f"{{{WP}}}extent"))
    assert int(str(extent.get("cy"))) == word.ICON_PT * EMU_PER_POINT
    paragraph = run.getparent()
    assert paragraph is not None
    texts = ["".join(t.text or "" for t in r.iter(w("t"))) for r in paragraph.iter(w("r"))]
    assert texts == ["Der Server ", "", " läuft."]


def test_the_picture_is_a_png_in_pta_blue_with_the_svg_beside_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(writer, "svg_available", lambda: True)
    data = generate(FRONT + "Der Server :icon-server: läuft.\n")
    pngs = [v for k, v in parts(data).items() if k.startswith("word/media/") and k.endswith(".png")]
    assert [raster.name_of(p) for p in pngs].count("server") == 1
    svgs = [v for k, v in parts(data).items() if k.endswith(".svg")]
    assert len(svgs) == 1 and f'stroke="#{colors.PTA_BLUE}"'.encode() in svgs[0]
    assert next(icon_runs(data)[0].iter(SVG_BLIP), None) is not None


def test_without_the_extra_svg_the_icon_is_only_a_png(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(writer, "svg_available", lambda: False)
    data = generate(FRONT + "Der Server :icon-server: läuft.\n")
    assert not [k for k in parts(data) if k.endswith(".svg")]
    (run,) = icon_runs(data)
    assert next(run.iter(SVG_BLIP), None) is None


def test_icons_before_every_item_replace_the_bullets() -> None:
    data = generate(FRONT + BULLETS)
    document = open_docx(data)
    items = [p for p in document.paragraphs if p.text.strip() in ("Erledigt", "Offen", "Verworfen")]
    assert len(items) == 3
    for paragraph in items:
        num_id = paragraph._p.find(f"{w('pPr')}/{w('numPr')}/{w('numId')}")
        assert num_id is not None and num_id.get(w("val")) == "0"
        assert paragraph.paragraph_format.first_line_indent is not None
        assert paragraph.paragraph_format.first_line_indent < 0
        first = paragraph._p.find(w("r"))
        assert first is not None and first.find(w("tab")) is not None
        assert next(first.iter(f"{{{WP}}}docPr")).get("descr", "").startswith("icon:")
    nested = next(p for p in document.paragraphs if p.text == "darunter")
    num_id = nested._p.find(f"{w('pPr')}/{w('numPr')}/{w('numId')}")
    assert num_id is not None and num_id.get(w("val")) != "0"


def test_a_list_where_not_every_item_starts_with_an_icon_keeps_its_bullets() -> None:
    data = generate(FRONT + "- :icon-check: Erledigt\n- Offen\n")
    assert len(icon_runs(data)) == 1
    numbers = body(data).iter(w("numId"))
    assert all(n.get(w("val")) != "0" for n in numbers)


def test_unknown_icons_are_an_error_with_suggestions() -> None:
    with pytest.raises(DocumentConversionError, match=r"Line 5: Unknown icon ':icon-sever:'"):
        generate(FRONT + "Der :icon-sever: läuft.\n")


def test_an_icon_in_a_footnote_is_left_out_with_a_note() -> None:
    output = io.BytesIO()
    markdown = FRONT + "Text[^1]\n\n[^1]: Siehe :icon-check:\n"
    result = DocxGenerator().generate(MarkdownDocument(markdown), output)
    assert [n.code for n in result.notes] == [NoteCodes.CODE_NOT_DRAWN]


def test_the_converter_writes_the_icons_again() -> None:
    markdown = FRONT + "Der Server :icon-server: läuft.\n\nAbsatz.\n\n" + BULLETS
    text = DocxConverter().convert(generate(markdown)).text
    assert "Der Server :icon-server: läuft." in text
    assert "- :icon-check: Erledigt\n- :icon-clock: Offen\n" in text
    assert "![" not in text
