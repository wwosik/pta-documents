"""E04-S02: slide content in the PTA style, and fitting."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from lxml import etree

from pta_documents.conversions.pptx import PptxConverter
from pta_documents.design import colors
from pta_documents.markdown import DocumentResource
from tests.expected import assert_matches_expected
from tests.generation.pptx.conftest import generate, layout_names, open_pptx

SAMPLES = Path(__file__).parent / "samples"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"a": A, "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
DIAGRAM = DocumentResource("diagram.png", "image/png", (SAMPLES / "diagram.png").read_bytes())


def deck() -> bytes:
    return generate((SAMPLES / "deck.md").read_text(encoding="utf-8"), resources=(DIAGRAM,))


def slide_xml(data: bytes, number: int) -> etree._Element:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return etree.fromstring(z.read(f"ppt/slides/slide{number}.xml"))


def find(root: etree._Element, path: str) -> list[etree._Element]:
    result = root.xpath(path, namespaces=NS)
    assert isinstance(result, list)
    return [e for e in result if isinstance(e, etree._Element)]


def test_deck_layouts(review_dir: Path) -> None:
    data = deck()
    (review_dir / "deck.pptx").write_bytes(data)
    assert layout_names(data) == [
        "Titelfolie mit Bild 02",
        "Trennfolie",
        "Titel und Text",
        "Nur Titel",
        "Titel und Text",
        "Titel, Text und Bild 01",
        "Nur Titel",
        "Titel und Text",
        "Titel und Text",
        "Trennfolie",
        "Titel und Text (zweispaltig)",
        "Abbschlussfolie",
    ]


def body_paragraphs(root: etree._Element) -> list[tuple[str, str]]:
    """(lvl, text) of the body placeholder."""
    result: list[tuple[str, str]] = []
    for p in find(root, "//p:sp[p:nvSpPr/p:nvPr/p:ph/@idx='12']//a:p"):
        text = "".join(t.text or "" for t in p.iter(f"{{{A}}}t"))
        level = p.find(f"{{{A}}}pPr")
        result.append((level.get("lvl", "0") if level is not None else "0", text))
    return result


def test_text_levels() -> None:
    root = slide_xml(deck(), 3)
    paragraphs = body_paragraphs(root)
    assert paragraphs[0][0] == "1" and paragraphs[0][1].startswith("Plain paragraph")
    assert ("2", "First bullet") in paragraphs
    assert ("3", "Nested bullet") in paragraphs
    assert ("4", "Third level") in paragraphs
    assert ("0", "A sub-heading") in paragraphs
    assert ("1", "A quoted remark.") in paragraphs
    numbers = find(root, "//a:pPr[a:buAutoNum]")
    assert numbers[0].get("lvl") == "2"
    assert find(root, "//a:buAutoNum")[0].get("startAt") == "3"


def test_bold_is_segoe_ui_and_links_are_links() -> None:
    root = slide_xml(deck(), 3)
    bold = find(root, "//a:r[a:t='bold']/a:rPr")[0]
    assert bold.get("b") == "1"
    latin = bold.find(f"{{{A}}}latin")
    assert latin is not None and latin.get("typeface") == "+mj-lt"
    assert find(root, "//a:r[a:t='link']/a:rPr/a:hlinkClick")
    code = find(root, "//a:r[a:t='code']/a:rPr/a:latin")[0]
    assert code.get("typeface") == "Consolas"


def test_table_follows_the_sample_table() -> None:
    root = slide_xml(deck(), 5)
    rows = find(root, "//a:tbl/a:tr")
    assert len(rows) == 4  # title row, header, two rows
    title = "".join(t.text or "" for t in rows[0].iter(f"{{{A}}}t"))
    assert title == "Revenue by region"
    header_cell = rows[1].find(f"{{{A}}}tc")
    assert header_cell is not None
    fill = header_cell.find(f"{{{A}}}tcPr/{{{A}}}solidFill/{{{A}}}srgbClr")
    assert fill is not None and fill.get("val") == colors.DARK_BLUE
    header_run = header_cell.find(f".//{{{A}}}rPr")
    assert header_run is not None and header_run.get("sz") == "1600"
    body_run = rows[2].find(f".//{{{A}}}rPr")
    assert body_run is not None and body_run.get("sz") == "1400"
    rules = [
        tc.find(f"{{{A}}}tcPr/{{{A}}}lnB//{{{A}}}srgbClr")
        for tc in (rows[2].find(f"{{{A}}}tc"), rows[3].find(f"{{{A}}}tc"))
        if tc is not None
    ]
    assert [r.get("val") for r in rules if r is not None] == [colors.GREY_LIGHT, colors.TEXT_SLIDES]
    alignment = rows[2].findall(f"{{{A}}}tc")[1].find(f".//{{{A}}}pPr")
    assert alignment is not None and alignment.get("algn") == "r"
    texts = "".join(t.text or "" for t in root.iter(f"{{{A}}}t"))
    assert "Numbers for the quarter:" in texts and "Figures are preliminary." in texts


def test_code_box() -> None:
    root = slide_xml(deck(), 4)
    fill = find(root, "//p:sp/p:spPr/a:solidFill/a:srgbClr")
    assert fill and fill[0].get("val") == colors.GREY_LIGHT
    lines = ["".join(t.text or "" for t in find(p, ".//a:t")) for p in find(root, "//a:p")]
    assert "var answer = 42;" in lines
    assert find(root, "//a:r[a:t='var ']/a:rPr/a:latin[@typeface='Consolas']")


def test_long_text_shrinks_then_continues() -> None:
    medium = "## Viel Text\n\n" + "\n".join(f"- Punkt {n} mit etwas Text" for n in range(15))
    data = generate("# D\n\n" + medium)
    assert len(open_pptx(data).slides) == 2
    autofit = find(slide_xml(data, 2), "//a:normAutofit")
    assert autofit and int(autofit[0].get("fontScale", "100000")) < 100000

    long = "## Sehr viel Text\n\n" + "\n".join(f"- Punkt {n} mit etwas Text" for n in range(60))
    presentation = open_pptx(generate("# D\n\n" + long))
    titles = [s.shapes.title.text if s.shapes.title else "" for s in presentation.slides][1:]
    assert len(titles) >= 2
    assert titles[0] == "Sehr viel Text"
    assert all(t == "Sehr viel Text (Forts.)" for t in titles[1:])


def test_long_table_splits_with_header() -> None:
    rows = "\n".join(f"| Zeile {n} | {n * 10} |" for n in range(40))
    data = generate(f"# D\n\n## Tabelle\n\n| Name | Wert |\n| --- | --- |\n{rows}\n")
    presentation = open_pptx(data)
    assert len(presentation.slides) >= 3
    for number in range(2, len(presentation.slides) + 1):
        header = find(slide_xml(data, number), "//a:tbl/a:tr[1]//a:t")
        assert [t.text for t in header] == ["Name", "Wert"]


def test_long_code_splits() -> None:
    code = "\n".join(f"line {n}" for n in range(80))
    data = generate(f"# D\n\n## Code\n\n```\n{code}\n```\n")
    assert len(open_pptx(data).slides) >= 3


def test_roundtrip(review_dir: Path) -> None:
    data = deck()
    markdown = PptxConverter().convert(data).text
    assert_matches_expected(SAMPLES / "deck.roundtrip.expected.md", markdown)
