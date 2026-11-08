"""E05-S01: PDF/A-2b, fonts, metadata, bookmarks and links of what the generator writes.

Ported from DocLibs ``PdfGeneratorTests.cs``: ``Output_IsPdfA2b_WithEmbeddedFonts``,
``Characters_BeyondWinAnsi_SurviveTheRoundTrip``, ``MoreThan255DistinctCharacters_Work``,
``LongNonAsciiTitleAndAuthor_StillFitTheMetadata``, bookmarks and links. Since the merge with
E05-S02 the PDFs come from Markdown through the layout engine.
"""

from __future__ import annotations

import datetime as dt
import io
import shutil
import subprocess
from pathlib import Path
from typing import Final

import pdfplumber
import pikepdf
import pytest
from PIL import Image

from pta_documents.design.fonts import FontFace, bundled
from pta_documents.generation.pdf import PdfGenerator, PdfOptions
from pta_documents.generation.pdf.metadata import PRODUCER
from pta_documents.generation.pdf.pdfa import PRINT_FLAG, srgb_profile
from pta_documents.markdown.document import DocumentResource, MarkdownDocument
from tests.generation.pdf.support import body_texts

CREATED: Final = dt.datetime(2026, 11, 8, 12, 30, tzinfo=dt.UTC)
OPTIONS: Final = PdfOptions(created=CREATED, system_fonts=False)
TITLE: Final = "Grundgerüst"
AUTHOR: Final = "Wojciech Wosik"
STANDARD_14: Final = {
    "Courier",
    "Courier-Bold",
    "Courier-BoldOblique",
    "Courier-Oblique",
    "Helvetica",
    "Helvetica-Bold",
    "Helvetica-BoldOblique",
    "Helvetica-Oblique",
    "Symbol",
    "Times-Roman",
    "Times-Bold",
    "Times-BoldItalic",
    "Times-Italic",
    "ZapfDingbats",
}
MIXED: Final = "Größe Maß Zażółć gęślą jaźń „Anführung“ – Ende…"
"""German and Polish: beyond WinAnsi, all in Selawik."""
FILLER: Final = "Fülltext, der die Seite füllt. " * 40


def png(color: tuple[int, int, int]) -> bytes:
    stream = io.BytesIO()
    Image.new("RGB", (80, 40), color).save(stream, "PNG")
    return stream.getvalue()


def sample_markdown() -> str:
    """Two pages and more: bookmarks on three levels, both kinds of link, one image twice."""
    return "\n\n".join(
        [
            f"---\nvorlage: hoch-ohne-deckblatt\ntitel: {TITLE}\nautor: {AUTHOR}\n"
            "untertitel: PDF/A-2b\n---",
            "# Kapitel 1",
            MIXED,
            "*schräg gestellt*",
            "```\nprint('code')\n```",
            "[PTA im Netz](https://www.pta.de/) und [zu Abschnitt 1.1](#abschnitt-11)",
            "![](bild.png)",
            "![](bild.png)",
            *[FILLER] * 8,
            "## Abschnitt 1.1",
            "### Unterabschnitt 1.1.1",
            "# Kapitel 2",
        ]
    )


def build(markdown: str, options: PdfOptions = OPTIONS) -> bytes:
    resources = (DocumentResource("bild.png", "image/png", png((0, 111, 185))),)
    output = io.BytesIO()
    PdfGenerator().generate(MarkdownDocument(markdown, resources), output, options)
    return output.getvalue()


@pytest.fixture(scope="module")
def sample() -> bytes:
    return build(sample_markdown())


def text_of(data: bytes) -> list[str]:
    return body_texts(data)


def font_dictionaries(pdf: pikepdf.Pdf) -> list[pikepdf.Dictionary]:
    return [
        obj
        for obj in pdf.objects
        if isinstance(obj, pikepdf.Dictionary) and obj.get("/Type") == pikepdf.Name.Font
    ]


def test_the_sample_is_written_for_review(sample: bytes, review_dir: Path) -> None:
    (review_dir / "pdf-grundgeruest.pdf").write_bytes(sample)
    assert sample.startswith(b"%PDF-1.7")


def test_the_output_is_pdfa_2b_in_its_metadata(sample: bytes) -> None:
    with pikepdf.open(io.BytesIO(sample)) as pdf:
        meta = pdf.open_metadata()
        assert meta["pdfaid:part"] == "2"
        assert meta["pdfaid:conformance"] == "B"
        assert meta["dc:title"] == TITLE == str(pdf.docinfo["/Title"])
        assert meta["dc:creator"] == [AUTHOR] == [str(pdf.docinfo["/Author"])]
        assert meta["dc:description"] == "PDF/A-2b" == str(pdf.docinfo["/Subject"])
        assert meta["dc:language"] == {"de-DE"}
        assert meta["pdf:Producer"] == PRODUCER == str(pdf.docinfo["/Producer"])
        assert meta["xmp:CreatorTool"] == PRODUCER == str(pdf.docinfo["/Creator"])
        assert meta["xmp:CreateDate"] == "2026-11-08T12:30:00+00:00"
        assert str(pdf.docinfo["/CreationDate"]) == "D:20261108123000Z"
        assert str(pdf.docinfo["/ModDate"]) == "D:20261108123000Z"
        assert str(pdf.Root.Lang) == "de-DE"
        assert "/Filter" not in pdf.Root.Metadata
        assert pdf.pdf_version == "1.7"


def test_the_output_intent_embeds_an_srgb_profile(sample: bytes) -> None:
    with pikepdf.open(io.BytesIO(sample)) as pdf:
        (intent,) = pdf.Root.OutputIntents
        assert intent.S == pikepdf.Name.GTS_PDFA1
        profile = intent.DestOutputProfile
        assert profile.N == 3
        content = profile.read_bytes()
        assert content[36:40] == b"acsp" and content[16:20] == b"RGB "
        assert content == srgb_profile()


def test_every_font_is_embedded_and_no_standard_font_appears(sample: bytes) -> None:
    with pikepdf.open(io.BytesIO(sample)) as pdf:
        fonts = font_dictionaries(pdf)
        assert fonts
        for font in fonts:
            name = str(font.BaseFont).lstrip("/")
            assert name.split("+")[-1] not in STANDARD_14
            assert font.Subtype == pikepdf.Name.TrueType
            assert "/FontFile2" in font.FontDescriptor
            assert "/ToUnicode" in font
    assert b"Helvetica" not in sample


def test_annotations_print_and_the_file_is_unencrypted_with_an_id(sample: bytes) -> None:
    with pikepdf.open(io.BytesIO(sample)) as pdf:
        annotations = [a for page in pdf.pages for a in page.obj.get("/Annots", pikepdf.Array())]
        assert len(annotations) == 2
        assert all(int(a.F) == PRINT_FLAG for a in annotations)
        assert not pdf.is_encrypted
        assert len(pdf.trailer.ID) == 2


def test_characters_beyond_winansi_survive_the_round_trip(sample: bytes) -> None:
    pages = text_of(sample)
    assert MIXED in pages[0]
    assert "schräg gestellt" in pages[0]
    assert "print('code')" in pages[0]
    assert "1.1.1 Unterabschnitt 1.1.1" in pages[-1]


def test_more_than_255_distinct_characters_work() -> None:
    advances = bundled().file(FontFace.REGULAR).info.advances
    # Not ASCII punctuation, which Markdown might read as syntax.
    chars = [
        chr(c)
        for c in sorted(advances)
        if chr(c).isprintable() and not chr(c).isspace() and (chr(c).isalnum() or c > 0x7F)
    ]
    assert len(chars) > 255
    lines = ["".join(chars[i : i + 40]) for i in range(0, len(chars), 40)]
    markdown = "---\nvorlage: hoch-ohne-deckblatt\ntypografie: nein\n---\n" + "\n\n".join(lines)
    text = "\n".join(text_of(build(markdown)))
    assert text.split("\n") == lines


def test_a_long_non_ascii_title_and_author_still_fit_the_metadata() -> None:
    title = "Überprüfung der Ölförderanlagen – Zażółć gęślą jaźń " * 12
    author = "Łucja Żółkiewska-Grünwald, Ægir Ørsted " * 6
    markdown = (
        f"---\nvorlage: hoch-ohne-deckblatt\nsprache: en\ntitel: {title.strip()}\n"
        f"autor: {author.strip()}\n---\n"
    )
    data = build(markdown)
    with pikepdf.open(io.BytesIO(data)) as pdf:
        meta = pdf.open_metadata()
        assert meta["dc:title"] == title.strip() == str(pdf.docinfo["/Title"])
        assert meta["dc:creator"] == [author.strip()]
        assert str(pdf.Root.Lang) == "en"
        assert "/Subject" not in pdf.docinfo
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        assert pdf.metadata["Title"] == title.strip()


def test_bookmarks_nest_by_level(sample: bytes) -> None:
    with pikepdf.open(io.BytesIO(sample)) as pdf, pdf.open_outline() as outline:
        (first, second) = outline.root
        assert first.title == "1 Kapitel 1" and second.title == "2 Kapitel 2"
        (section,) = first.children
        assert section.title == "1.1 Abschnitt 1.1"
        assert [c.title for c in section.children] == ["1.1.1 Unterabschnitt 1.1.1"]


def test_nesting_never_skips_a_level() -> None:
    data = build("---\nvorlage: hoch-ohne-deckblatt\n---\n# Eins\n\n### Tief\n\n# Zwei\n")
    with pikepdf.open(io.BytesIO(data)) as pdf, pdf.open_outline() as outline:
        (first, second) = outline.root
        assert [c.title for c in first.children] == ["1.0.1 Tief"]
        assert second.title == "2 Zwei"


def test_external_and_internal_links_work(sample: bytes) -> None:
    with pikepdf.open(io.BytesIO(sample)) as pdf:
        annotations = list(pdf.pages[0].obj.Annots)
        uri = next(a for a in annotations if "/URI" in a.get("/A", {}))
        assert uri.A.S == pikepdf.Name.URI and str(uri.A.URI) == "https://www.pta.de/"
        internal = next(a for a in annotations if a is not uri)
        destination = internal.get("/Dest")
        if destination is None:  # a GoTo action
            destination = internal.A.D
        if not isinstance(destination, pikepdf.Array):  # a named destination
            names = pdf.Root.Names.Dests.Names
            keys = [str(names[i]) for i in range(0, len(names), 2)]
            destination = names[keys.index(str(destination)) + 1]
            if isinstance(destination, pikepdf.Dictionary):
                destination = destination.D
        assert destination[0].objgen == pdf.pages[len(pdf.pages) - 1].obj.objgen


def test_equal_images_are_embedded_once(sample: bytes) -> None:
    with pikepdf.open(io.BytesIO(sample)) as pdf:
        images = [
            obj
            for obj in pdf.objects
            if isinstance(obj, pikepdf.Stream) and obj.get("/Subtype") == pikepdf.Name.Image
        ]
    assert len(images) == 1


def test_equal_input_gives_equal_bytes(sample: bytes) -> None:
    assert build(sample_markdown()) == sample
    later = PdfOptions(created=CREATED.replace(hour=13), system_fonts=False)
    assert build(sample_markdown(), later) != sample


@pytest.mark.skipif(shutil.which("verapdf") is None, reason="veraPDF is not installed")
def test_verapdf_confirms_pdfa_2b(sample: bytes, tmp_path: Path) -> None:
    target = tmp_path / "pdf-grundgeruest.pdf"
    target.write_bytes(sample)
    result = subprocess.run(
        ["verapdf", "--flavour", "2b", "--format", "text", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0 and "PASS" in result.stdout, result.stdout + result.stderr
