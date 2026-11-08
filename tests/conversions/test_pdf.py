"""E07-S04: PDF → Markdown (DocLibs ``SampleConversionTests`` for PDF and the heuristics)."""

from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

import pikepdf
import pytest
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from pta_documents import DocumentConversionError, DocumentFormat
from pta_documents.conversions import ConverterRegistry
from pta_documents.conversions.options import ConversionOptions
from pta_documents.conversions.pdf import (
    DONE_TASK,
    ENCRYPTED,
    ITEM,
    OPEN_TASK,
    Line,
    PdfConverter,
    code_block,
    join,
    paragraph_markdown,
    paragraphs,
    running_paragraphs,
    strip_bullet,
)
from pta_documents.markdown import MetadataKeys
from tests.expected import assert_matches_expected, assert_resources_match_references

SAMPLES = Path(__file__).parent / "samples"
A4 = (595.0, 842.0)


def sample() -> bytes:
    return (SAMPLES / "sample.pdf").read_bytes()


def canvas_pdf(draw: object) -> bytes:
    """A one-page PDF drawn by ``draw(canvas)`` (y from the bottom, as in PDF)."""
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=A4)
    assert callable(draw)
    draw(canvas)
    canvas.showPage()
    canvas.save()
    return output.getvalue()


# --- the sample of DocLibs ------------------------------------------------------------------


def test_sample_converts_to_the_expected_markdown() -> None:
    """``sample.pdf.expected.md`` is the file of DocLibs, unchanged."""
    document = PdfConverter().convert(sample())
    assert_matches_expected(SAMPLES / "sample.pdf.expected.md", document.text)
    assert_resources_match_references(document)
    assert document.resources


def test_the_logo_on_every_page_is_dropped_and_the_chart_kept() -> None:
    document = PdfConverter().convert(sample())
    (image,) = document.resources
    assert image.path == "images/page2-image1.png"
    assert image.content_type == "image/png"
    assert document.metadata[MetadataKeys.PAGE_COUNT] == "3"
    assert document.metadata[MetadataKeys.TITLE] == "Sample document"
    assert document.metadata[MetadataKeys.AUTHOR] == "PTA-Docs"
    assert MetadataKeys.SKIPPED_IMAGES not in document.metadata
    assert "Sample document" not in document.text  # the running header
    assert "of 3" not in document.text  # the running footer


def test_the_registry_converts_pdf() -> None:
    document = ConverterRegistry.default().convert(sample(), "sample.pdf")
    assert document.text == (SAMPLES / "sample.pdf.expected.md").read_text(encoding="utf-8")


def test_without_images_nothing_is_extracted_or_referenced() -> None:
    document = PdfConverter().convert(sample(), ConversionOptions(include_images=False))
    assert document.resources == ()
    assert "![" not in document.text


def test_a_resource_prefix_names_the_images() -> None:
    document = PdfConverter().convert(sample(), ConversionOptions(resource_path_prefix="media/"))
    assert [r.path for r in document.resources] == ["media/page2-image1.png"]
    assert "![](media/page2-image1.png)" in document.text


class _ForwardOnly(io.RawIOBase):
    def __init__(self, data: bytes) -> None:
        self._data = io.BytesIO(data)

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return False

    def readinto(self, buffer: bytearray | memoryview) -> int:  # type: ignore[override]
        chunk = self._data.read(len(buffer))
        buffer[: len(chunk)] = chunk
        return len(chunk)


def test_a_stream_that_cannot_seek_is_accepted() -> None:
    stream: BinaryIO = io.BufferedReader(_ForwardOnly(sample()))  # type: ignore[arg-type]
    assert "## Page 1" in PdfConverter().convert(stream).text


@pytest.mark.parametrize("content", [b"%PDF-1.7 broken", b""])
def test_damaged_input_raises(content: bytes) -> None:
    with pytest.raises(DocumentConversionError) as error:
        PdfConverter().convert(content)
    assert error.value.format is DocumentFormat.PDF
    assert error.value.reason.startswith("The PDF could not be read: ")


def test_a_password_protected_pdf_is_named_as_such() -> None:
    output = io.BytesIO()
    with pikepdf.open(io.BytesIO(sample())) as pdf:
        pdf.save(output, encryption=pikepdf.Encryption(user="secret", owner="owner"))
    with pytest.raises(DocumentConversionError) as error:
        PdfConverter().convert(output.getvalue())
    assert error.value.format is DocumentFormat.PDF
    assert error.value.reason == ENCRYPTED


def test_an_undecodable_image_is_counted_as_skipped() -> None:
    output = io.BytesIO()
    with pikepdf.open(io.BytesIO(sample())) as pdf:
        chart = pdf.pages[1].Resources.XObject["/I1"]
        chart.write(b"not an image", filter=pikepdf.Name.JBIG2Decode)
        pdf.save(output)
    document = PdfConverter().convert(output.getvalue())
    assert document.resources == ()
    assert document.metadata[MetadataKeys.SKIPPED_IMAGES] == "1"


def test_jpeg_data_is_kept_as_it_is() -> None:
    jpeg = io.BytesIO()
    Image.new("RGB", (40, 20), (0, 111, 185)).save(jpeg, format="JPEG")

    def draw(canvas: Canvas) -> None:
        canvas.drawString(72, 770, "A photo:")
        canvas.drawImage(ImageReader(io.BytesIO(jpeg.getvalue())), 72, 600, 80, 40)

    document = PdfConverter().convert(canvas_pdf(draw))
    (image,) = document.resources
    assert image.path == "images/page1-image1.jpg"
    assert image.content_type == "image/jpeg"
    assert image.content == jpeg.getvalue()
    assert document.text == "## Page 1\n\nA photo:\n\n![](images/page1-image1.jpg)\n"


def test_rotated_text_such_as_a_watermark_is_left_out() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.drawString(72, 700, "Body text.")
        canvas.saveState()
        canvas.translate(300, 400)
        canvas.rotate(45)
        canvas.setFontSize(60)
        canvas.drawString(0, 0, "ENTWURF")
        canvas.restoreState()

    assert PdfConverter().convert(canvas_pdf(draw)).text == "## Page 1\n\nBody text.\n"


def test_a_grid_table_becomes_a_pipe_table() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.drawString(72, 760, "Before the table.")
        top, height, columns = 740.0, 20.0, (72.0, 200.0, 330.0)
        rows = (("Region", "Revenue"), ("North", "1,200"), ("South", "950 | net"))
        for index in range(len(rows) + 1):
            canvas.line(columns[0], top - index * height, columns[-1], top - index * height)
        for x in columns:
            canvas.line(x, top, x, top - len(rows) * height)
        for index, row in enumerate(rows):
            for x, text in zip(columns, row, strict=False):
                canvas.drawString(x + 4, top - (index + 1) * height + 6, text)
        canvas.drawString(72, 640, "After the table.")

    assert PdfConverter().convert(canvas_pdf(draw)).text == (
        "## Page 1\n\n"
        "Before the table.\n\n"
        "| Region | Revenue |\n| --- | --- |\n| North | 1,200 |\n| South | 950 \\| net |\n\n"
        "After the table.\n"
    )


def test_plain_quotes_straighten_typographic_characters() -> None:
    def draw(canvas: Canvas) -> None:
        canvas.drawString(72, 700, "„Quoted“ – text…")

    text = PdfConverter().convert(canvas_pdf(draw), ConversionOptions(plain_quotes=True)).text
    assert text == '## Page 1\n\n"Quoted" - text...\n'


def test_a_pdf_without_text_and_images_gives_nothing() -> None:
    assert PdfConverter().convert(canvas_pdf(lambda canvas: None)).text == ""


# --- heuristics on made-up lines ------------------------------------------------------------


def line(text: str, top: float, *, left: float = 72, right: float = 520, size: float = 10,
         bold: bool = False, marker: str | None = None, code: bool = False) -> Line:  # fmt: skip
    return Line(text, left, right, top, top + size, size, bold, marker, code, 0.5 * size)


@pytest.mark.parametrize(
    ("parts", "expected"),
    [
        (["Die Netz-", "nutzung"], "Die Netznutzung"),  # hyphenated across lines
        (["Die GELI-", "Anmeldung"], "Die GELI-Anmeldung"),  # a hyphen word keeps it
        (["Die Netz-", "Nutzung"], "Die Netz-Nutzung"),
        (["Zahl 12-", "fach"], "Zahl 12- fach"),  # only after a letter
        (["eins", "zwei"], "eins zwei"),
    ],
)
def test_lines_are_joined_and_hyphenation_is_repaired(parts: list[str], expected: str) -> None:
    current: list[str] = []
    for part in parts:
        join(current, part)
    assert "".join(current) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("• Punkt", "Punkt"),
        ("▪Punkt", "Punkt"),
        (" Wingdings", "Wingdings"),
        ("- Strich", "Strich"),
        ("o Kreis", "Kreis"),
        ("-Strich", None),  # a weak bullet needs a space
        ("ohne", None),
        ("•", None),
    ],
)
def test_bullets_are_recognised(text: str, expected: str | None) -> None:
    assert strip_bullet(text) == expected


@pytest.mark.parametrize(
    ("text", "size", "bold", "expected"),
    [
        ("1.2 Ergebnisse", 10, True, "### 1.2 Ergebnisse"),  # bold and numbered
        ("Ergebnisse", 12, False, "### Ergebnisse"),  # larger than the body
        ("Ergebnisse", 10, True, "Ergebnisse"),  # bold alone is no heading
        ("Ein ganzer Satz.", 14, False, "Ein ganzer Satz."),
        ("Zahlen:", 14, False, "Zahlen:"),
        ("2 Ausblick:", 14, False, "### 2 Ausblick:"),  # numbered may end in a colon
        ("1 Einleitung ........ 3", 14, True, "1 Einleitung ........ 3"),  # contents line
        ("1. Schritt", 10, False, "1\\. Schritt"),
        ("*Stern* und `Code`", 10, False, "\\*Stern\\* und \\`Code\\`"),
    ],
)
def test_headings_need_size_or_a_bold_number(
    text: str, size: float, bold: bool, expected: str
) -> None:
    assert paragraph_markdown(text, size, bold, 10) == expected


def test_a_paragraph_wrapping_over_lines_is_one() -> None:
    lines = [line("Ein Absatz, der über", 100), line("zwei Zeilen läuft.", 114, right=200)]
    assert [b.markdown for b in paragraphs(lines, 10, 842)] == [
        "Ein Absatz, der über zwei Zeilen läuft."
    ]


def test_paragraphs_break_at_gaps_short_lines_and_items() -> None:
    lines = [
        line("Erster Absatz endet früh.", 100, right=200),
        line("Zweiter Absatz,", 114),
        line("weit unten.", 150, right=200),
        line("• Punkt eins", 164, right=200),
        line("Punkt zwei", 178, right=200, marker=ITEM),
        line("offen", 192, right=200, marker=OPEN_TASK),
        line("erledigt", 206, right=200, marker=DONE_TASK),
    ]
    assert [b.markdown for b in paragraphs(lines, 10, 842)] == [
        "Erster Absatz endet früh.",
        "Zweiter Absatz,",
        "weit unten.",
        "- Punkt eins",
        "- Punkt zwei",
        "- [ ] offen",
        "- [x] erledigt",
    ]


def test_lines_at_the_page_edges_are_paragraphs_of_their_own() -> None:
    lines = [line("Kopfzeile", 30), line("Text", 70), line("Fußzeile", 790)]
    assert [b.markdown for b in paragraphs(lines, 10, 842)] == ["Kopfzeile", "Text", "Fußzeile"]


def test_no_paragraph_spans_a_table() -> None:
    lines = [line("Davor", 100), line("Danach", 114)]
    assert [b.markdown for b in paragraphs(lines, 10, 842, breaks=[112])] == ["Davor", "Danach"]


def test_code_lines_become_a_fenced_block_with_indentation_and_empty_lines() -> None:
    lines = [
        line("def f():", 100, code=True),
        line("return 1", 113, left=92, code=True),
        line("f()", 139, code=True),
    ]
    assert code_block(lines) == "```\ndef f():\n    return 1\n\nf()\n```"
    assert code_block([line("a ``` b", 100, code=True)]) == "````\na ``` b\n````"


def test_running_headers_and_footers_are_found_but_not_list_items() -> None:
    pages = [
        ["Bericht", f"Text {word}", f"{n}. Punkt", f"{n + 1}. Punkt", f"Seite {n} von 3"]
        for n, word in ((1, "eins"), (2, "zwei"), (3, "drei"))
    ]
    assert running_paragraphs(pages) == {"bericht", "seitevon"}
    assert running_paragraphs(pages[:2]) == set()  # three pages at least
