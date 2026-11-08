"""E05-S02: ``report.md`` and ``long.md`` of DocLibs (``report.md`` with PTA cases added) as PDF.

The PDFs go to ``.tmp/review/``; text, pages and bookmarks are checked here, and the round trip
through the PDF converter (E07-S04) with the PTA page frame is ``*.roundtrip.expected.md``.
"""

from __future__ import annotations

import datetime as dt
import io
from pathlib import Path
from typing import Final

import pikepdf
import pytest

from pta_documents.conversions.pdf import PdfConverter
from pta_documents.generation.common.result import NoteCodes, Notes
from pta_documents.generation.pdf import PdfGenerator, PdfOptions
from pta_documents.generation.pdf.layout import LayoutSettings, PdfInfo, layout
from pta_documents.markdown.document import DocumentResource, MarkdownDocument
from pta_documents.markdown.parser import create_parser
from tests.expected import assert_matches_expected, assert_resources_match_references
from tests.generation.pdf.layout.support import Pdf

SAMPLES = Path(__file__).parent / "samples"
FRONT_MATTER: Final = "---\ntitel: Quartalsbericht\nautor: PTA Documents\ndatum: 08.11.2026\n---\n"
ROUND_TRIP: Final = PdfOptions(
    created=dt.datetime(2026, 11, 8, 9, 0, tzinfo=dt.UTC),
    system_fonts=False,
    code_block_renderers=(),  # the same on every machine: Mermaid stays code
)


def generate(name: str, review_dir: Path, notes: Notes | None = None) -> Pdf:
    text = (SAMPLES / name).read_text(encoding="utf-8")
    diagram = DocumentResource("diagram.png", "image/png", (SAMPLES / "diagram.png").read_bytes())
    document = MarkdownDocument(text, (diagram,))
    tokens = create_parser().parse(text)
    result = layout(tokens, document, LayoutSettings(), notes, PdfInfo(title=name))
    (review_dir / f"pdf-layout-{Path(name).stem}.pdf").write_bytes(result.content)
    pdf = Pdf(result.content)
    assert pdf.pages == result.pages
    return pdf


def bookmarks(content: bytes) -> list[str]:
    with pikepdf.open(io.BytesIO(content)) as pdf, pdf.open_outline() as outline:
        titles: list[str] = []

        def walk(items: list[pikepdf.OutlineItem]) -> None:
            for item in items:
                titles.append(str(item.title))
                walk(list(item.children))

        walk(list(outline.root))
        return titles


def test_report(review_dir: Path) -> None:
    notes = Notes()
    pdf = generate("report.md", review_dir, notes)
    text = "\n".join(pdf.page_texts)
    for expected in (
        "1 Quarterly review",
        "1.1 Summary",
        "Zażółć gęślą jaźń",
        "Příliš žluťoučký kůň",
        "1.1.1 A sub-heading",
        "Console.WriteLine",
        "Abbildung 1: Bar chart",
        "FOURTH LEVEL",
        "2 Outlook",
        "Kennzahlen je Region",
        "Tabelle 1: Umsatz je Region",
        "Quelle: Controlling, Stand März.",
        "Hinweis: Ein Hinweis in der Box.",
    ):
        assert expected in text
    assert bookmarks(pdf.content) == [
        "1 Quarterly review",
        "1.1 Summary",
        "1.1.1 A sub-heading",
        "1.2 Results",
        "2 Outlook",
        "2.1 PTA-Fälle",
    ]
    # Without mermaid-cli the diagram stays code, with a note.
    assert {n.code for n in notes.to_tuple()} <= {NoteCodes.CODE_NOT_DRAWN}


def test_long(review_dir: Path) -> None:
    pdf = generate("long.md", review_dir)
    assert pdf.pages >= 4
    rows = [line for line in pdf.lines if line.text.startswith("#Name")]
    assert len(rows) >= 2  # the header on every page of the long table
    items = [line.text for line in pdf.lines if " Item number " in line.text]
    assert [item.split(".")[0] for item in items] == [str(n) for n in range(1, 61)]


@pytest.mark.parametrize("name", ["report.md", "long.md"])
def test_the_round_trip_through_the_pdf_converter(name: str, review_dir: Path) -> None:
    """With cover, header and footer of the PTA template: the converter leaves the running
    header and footer out (E07-S04)."""
    text = FRONT_MATTER + (SAMPLES / name).read_text(encoding="utf-8")
    diagram = DocumentResource("diagram.png", "image/png", (SAMPLES / "diagram.png").read_bytes())
    output = io.BytesIO()
    PdfGenerator().generate(MarkdownDocument(text, (diagram,)), output, ROUND_TRIP)
    (review_dir / f"pdf-roundtrip-{Path(name).stem}.pdf").write_bytes(output.getvalue())
    document = PdfConverter().convert(output.getvalue())
    stem = Path(name).stem
    assert_matches_expected(SAMPLES / f"{stem}.roundtrip.expected.md", document.text)
    assert_resources_match_references(document)
    for frame in ("Seite", "Stand:", "PTA IT-Beratung", "Quartalsbericht"):
        assert frame not in document.text
