"""E03-S02: the Markdown blocks in the PTA styles."""

from __future__ import annotations

import io
import re
from pathlib import Path

import pytest
from lxml import etree
from PIL import Image

from pta_documents import DocumentConversionError
from pta_documents.conversions.docx import DocxConverter
from pta_documents.design.variants import WordVariant
from pta_documents.generation.common.openxml import W, w
from pta_documents.markdown import DocumentResource
from tests.expected import assert_matches_expected
from tests.generation.docx.conftest import generate, open_docx, parts, style_name

SAMPLES = Path(__file__).parent / "samples"
NS = {"w": W}


def png(width: int = 800, height: int = 400) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (0, 111, 185)).save(buffer, "PNG", dpi=(96, 96))
    return buffer.getvalue()


IMAGES = (DocumentResource("images/diagramm.png", "image/png", png()),)


def report(variant: WordVariant = WordVariant.PORTRAIT, language: str = "de") -> bytes:
    markdown = (SAMPLES / "report.md").read_text(encoding="utf-8")
    markdown = markdown.replace(
        "---\n# ", f"vorlage: {variant.value}\nsprache: {language}\n---\n# ", 1
    )
    return generate(markdown, resources=IMAGES)


def body(data: bytes) -> etree._Element:
    return etree.fromstring(parts(data)["word/document.xml"])


def test_blocks_land_in_the_pta_styles(review_dir: Path) -> None:
    data = report()
    (review_dir / "report-hoch.docx").write_bytes(data)
    paragraphs = [(style_name(p), p.text) for p in open_docx(data).paragraphs]
    expected = [
        ("heading 1", "Ausgangslage"),
        ("Standard fett", "Wichtig:"),
        ("List Bullet", "Erster Punkt"),
        ("List Bullet", "Unterpunkt"),
        ("List Paragraph", "Schritt eins"),
        ("heading 2", "Kennzahlen"),
        ("Standard fett", "Kosten je Quartal"),
        ("caption", "Tabelle 1: Kosten der Quartale"),
        ("heading 3", "Architektur"),
        ("caption", "Abbildung 1: Übersicht der Systeme"),
        ("Zwischenüberschrift", "Hinweise"),
        ("Zitat", "Ein Zitat aus dem Lenkungskreis."),
        ("Code", 'print("Hallo PTA")'),
        ("Standard fett", "Begriff"),
    ]
    for item in expected:
        assert item in paragraphs, item
    first = next(p for s, p in paragraphs if s == "Normal" and p)
    assert first.startswith("Das Projekt hat gute Fortschritte")


def test_list_levels_and_restart() -> None:
    root = body(report())
    numbered = root.xpath(
        "//w:p[w:pPr/w:pStyle/@w:val='Listenabsatz']/w:pPr/w:numPr", namespaces=NS
    )
    assert isinstance(numbered, list)
    ids = [n.find(w("numId")).get(w("val")) for n in numbered]  # type: ignore[union-attr]
    assert len(ids) == 4
    assert ids[0] == ids[1] and ids[2] == ids[3] and ids[0] != ids[2]
    bullets = root.xpath(
        "//w:p[w:pPr/w:pStyle/@w:val='Aufzhlungszeichen']/w:pPr/w:numPr/w:ilvl/@w:val",
        namespaces=NS,
    )
    assert bullets == ["0", "1", "2", "0"]
    numbering = parts(report())["word/numbering.xml"].decode()
    assert f'<w:num w:numId="{ids[2]}">' in numbering
    assert '<w:startOverride w:val="1"/>' in numbering


def test_no_direct_font_size_or_colour_except_code() -> None:
    root = body(report())
    for r_pr in root.iter(w("rPr")):
        assert r_pr.find(w("sz")) is None
        paragraph = next(r_pr.iterancestors(w("p")))
        in_code = paragraph.find(f"{w('pPr')}/{w('pStyle')}[@{w('val')}='Code']") is not None
        # Highlighted code blocks colour their tokens (E17-S02), nothing else does.
        assert r_pr.find(w("color")) is None or in_code
        fonts = r_pr.find(w("rFonts"))
        if fonts is not None:
            assert fonts.get(w("ascii")) == "Consolas"


def test_table_uses_the_pta_style_over_the_text_width() -> None:
    data = report()
    root = body(data)
    table = root.find(f".//{w('tbl')}")
    assert table is not None
    style = table.find(f"{w('tblPr')}/{w('tblStyle')}")
    assert style is not None and style.get(w("val")) == "PTA"
    width = table.find(f"{w('tblPr')}/{w('tblW')}")
    assert width is not None
    assert abs(int(width.get(w("w"), "0")) - (11906 - 2 * 1247)) <= 3
    assert table.find(f"{w('tr')}/{w('trPr')}/{w('tblHeader')}") is not None
    alignments = [
        jc.get(w("val"))
        for jc in table.find(w("tr")).iter(w("jc"))  # type: ignore[union-attr]
    ]
    assert alignments == ["right", "center"]


def test_links_footnotes_and_fields() -> None:
    data = report()
    content = parts(data)
    document = content["word/document.xml"].decode()
    assert "w:hyperlink" in document
    assert "https://example.org/portal" in content["word/_rels/document.xml.rels"].decode()
    assert "<w:footnoteReference" in document
    footnotes = content["word/footnotes.xml"].decode()
    assert "Die Konfiguration liegt im Repository." in footnotes
    assert "SEQ Tabelle" in document and "SEQ Abbildung" in document


def test_english_captions() -> None:
    paragraphs = [p.text for p in open_docx(report(language="en")).paragraphs]
    assert "Table 1: Kosten der Quartale" in paragraphs
    assert "Figure 1: Übersicht der Systeme" in paragraphs


def test_image_fits_the_text_width() -> None:
    data = generate(
        "---\nvorlage: hoch-ohne-deckblatt\n---\n![x](images/wide.png)\n",
        resources=(DocumentResource("images/wide.png", "image/png", png(4000, 500)),),
    )
    extent = body(data).find(
        ".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent"
    )
    assert extent is not None
    assert int(extent.get("cx", "0")) <= (11906 - 2 * 1247) * 635


@pytest.mark.parametrize(
    ("markdown", "expected"),
    [
        ("![a](images/none.png)", "'images/none.png' (line 4) is not among"),
        ("![a](images/a.webp)", "is a image/webp"),
        ("![a](images/a.svg)", "'images/a.svg' cannot be converted: it has no size"),
    ],
)
def test_image_mistakes(markdown: str, expected: str) -> None:
    webp = DocumentResource("images/a.webp", "image/webp", b"RIFF")
    svg = DocumentResource("images/a.svg", "image/svg+xml", b"<svg/>")
    with pytest.raises(DocumentConversionError) as error:
        generate(f"---\ntitel: T\n---\n{markdown}\n", resources=(webp, svg))
    assert expected in error.value.reason


@pytest.mark.parametrize(
    "variant", [WordVariant.PORTRAIT, WordVariant.LANDSCAPE], ids=lambda v: v.value
)
def test_roundtrip(variant: WordVariant, review_dir: Path) -> None:
    data = report(variant)
    (review_dir / f"report-{variant.value}.docx").write_bytes(data)
    markdown = DocxConverter().convert(data).text
    assert_matches_expected(SAMPLES / f"report-{variant.value}.roundtrip.expected.md", markdown)


def test_schema_order_of_paragraph_properties() -> None:
    order = re.compile(r"<w:pPr>(.*?)</w:pPr>", re.S)
    document = parts(report())["word/document.xml"].decode()
    for match in order.finditer(document):
        tags = re.findall(r"<w:(\w+)", match.group(1))
        top = [
            t for t in tags if t in ("pStyle", "keepNext", "numPr", "pBdr", "spacing", "ind", "jc")
        ]
        ranks = [
            ("pStyle", "keepNext", "numPr", "pBdr", "spacing", "ind", "jc").index(t) for t in top
        ]
        assert ranks == sorted(ranks), match.group(0)


def jpeg_without_jfif() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (300, 200), (0, 111, 185)).save(buffer, "JPEG")
    data = buffer.getvalue()
    assert data[2:4] == b"\xff\xe0"  # APP0 (JFIF) right after SOI
    length = int.from_bytes(data[4:6], "big")
    return data[:2] + data[4 + length :]  # drop the APP0 segment


def test_jpeg_without_jfif_header_is_accepted() -> None:
    image = DocumentResource("images/a.jpg", "image/jpeg", jpeg_without_jfif())
    data = generate("---\ntitel: T\n---\n![Foto](images/a.jpg)\n", resources=(image,))
    assert any(name.startswith("word/media/") for name in parts(data))
