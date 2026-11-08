"""E05-S01: renderer and PDF/A-2b on a hand-built ``Layout``.

Ported from DocLibs ``PdfGeneratorTests.cs``: ``Output_IsPdfA2b_WithEmbeddedFonts``,
``Characters_BeyondWinAnsi_SurviveTheRoundTrip``, ``MoreThan255DistinctCharacters_Work``,
``LongNonAsciiTitleAndAuthor_StillFitTheMetadata``, bookmarks and links.
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

from pta_documents.design import colors
from pta_documents.design.fonts import FontFace, bundled
from pta_documents.design.variants import Language, Orientation
from pta_documents.drawing.model import ClosePath, CubicTo, LineTo, MoveTo
from pta_documents.generation.pdf.fonts import PdfFonts, registered_name
from pta_documents.generation.pdf.metadata import PRODUCER, PdfInfo
from pta_documents.generation.pdf.page_model import (
    Anchor,
    Bookmark,
    ImageItem,
    LaidOutPage,
    Layout,
    LineItem,
    LinkItem,
    PageGeometry,
    RectItem,
    ShapeItem,
    TextItem,
)
from pta_documents.generation.pdf.pdfa import PRINT_FLAG, srgb_profile, to_pdfa
from pta_documents.generation.pdf.renderer import nest, render

CREATED: Final = dt.datetime(2026, 11, 8, 12, 30, tzinfo=dt.UTC)
INFO: Final = PdfInfo("Grundgerüst", "Wojciech Wosik", "PDF/A-2b", Language.DE, CREATED)
GEOMETRY: Final = PageGeometry.a4(Orientation.PORTRAIT, 62, 99, 62, 57)
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
GREEK: Final = "ΔΣΩ πμ"
"""Selawik has neither Greek nor Cyrillic; the bundled Gelasio has some Greek
(no Cyrillic in any bundled face; Segoe UI from the system has both)."""


@pytest.fixture(scope="module")
def fonts() -> PdfFonts:
    return PdfFonts(bundled())


def png(color: tuple[int, int, int]) -> bytes:
    stream = io.BytesIO()
    Image.new("RGB", (8, 4), color).save(stream, "PNG")
    return stream.getvalue()


def sample_layout() -> Layout:
    """Two pages with every kind of item, bookmarks on three levels and both kinds of link."""
    picture = png((0, 111, 185))
    first = LaidOutPage(
        (
            TextItem(62, 120, "Kapitel 1", FontFace.BOLD, 16, color=colors.PTA_BLUE),
            TextItem(62, 150, MIXED, FontFace.REGULAR, 10),
            TextItem(62, 170, "schräg gestellt", FontFace.ITALIC, 10),
            TextItem(62, 190, "print('code')", FontFace.MONO, 9),
            TextItem(62, 210, GREEK, FontFace.QUOTE, 10),
            LineItem(62, 220, 300, 220, 0.5, colors.GREY_MID, dash=(2, 2)),
            RectItem(62, 230, 100, 20, colors.GREY_LIGHT, stroke=colors.PTA_BLUE, stroke_width=1),
            RectItem(170, 230, 100, 20, colors.LIGHT_BLUE, corner_radius=4),
            ImageItem(62, 260, 80, 40, picture),
            ImageItem(160, 260, 80, 40, picture),
            ShapeItem(
                (
                    MoveTo(300, 260),
                    LineTo(340, 260),
                    CubicTo(350, 270, 350, 290, 340, 300),
                    ClosePath(),
                ),
                colors.YELLOW,
                colors.TEXT_WORD,
                0.75,
                round_joins=True,
            ),
            TextItem(62, 330, "PTA im Netz", FontFace.REGULAR, 10, color=colors.DARK_BLUE),
            LinkItem(62, 320, 60, 12, url="https://www.pta.de/"),
            TextItem(62, 350, "zu Abschnitt 1.1", FontFace.REGULAR, 10),
            LinkItem(62, 340, 80, 12, target="abschnitt-1-1"),
        ),
        (Anchor("kapitel-1", 100),),
    )
    second = LaidOutPage(
        (
            TextItem(62, 120, "Abschnitt 1.1", FontFace.BOLD, 13),
            TextItem(62, 150, "Unterabschnitt 1.1.1", FontFace.BOLD, 11),
            TextItem(62, 180, "Kapitel 2", FontFace.BOLD, 16),
        ),
        (Anchor("abschnitt-1-1", 100),),
    )
    bookmarks = (
        Bookmark("1 Kapitel 1", 1, 0, 100),
        Bookmark("1.1 Abschnitt 1.1", 2, 1, 100),
        Bookmark("1.1.1 Unterabschnitt 1.1.1", 3, 1, 140),
        Bookmark("2 Kapitel 2", 1, 1, 170),
    )
    return Layout(GEOMETRY, (first, second), bookmarks)


def build(fonts: PdfFonts, layout: Layout | None = None, info: PdfInfo = INFO) -> bytes:
    layout = layout or sample_layout()
    return to_pdfa(render(layout, fonts, info), info)


@pytest.fixture(scope="module")
def sample(fonts: PdfFonts) -> bytes:
    return build(fonts)


def text_of(data: bytes) -> list[str]:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]


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
        assert meta["dc:title"] == INFO.title == str(pdf.docinfo["/Title"])
        assert meta["dc:creator"] == [INFO.author] == [str(pdf.docinfo["/Author"])]
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
    first, second = text_of(sample)
    assert MIXED in first
    assert "schräg gestellt" in first
    assert "print('code')" in first
    assert GREEK in first
    assert "Unterabschnitt 1.1.1" in second


def test_more_than_255_distinct_characters_work(fonts: PdfFonts) -> None:
    advances = fonts.fonts.file(FontFace.REGULAR).info.advances
    chars = [chr(c) for c in sorted(advances) if chr(c).isprintable() and not chr(c).isspace()]
    assert len(chars) > 255
    lines = ["".join(chars[i : i + 40]) for i in range(0, len(chars), 40)]
    page = LaidOutPage(
        tuple(TextItem(40, 60 + 20 * n, line, FontFace.REGULAR, 9) for n, line in enumerate(lines))
    )
    (text,) = text_of(build(fonts, Layout(GEOMETRY, (page,))))
    assert text.split("\n") == lines


def test_a_long_non_ascii_title_and_author_still_fit_the_metadata(fonts: PdfFonts) -> None:
    title = "Überprüfung der Ölförderanlagen – Zażółć gęślą jaźń " * 12
    author = "Łucja Żółkiewska-Grünwald, Ægir Ørsted " * 6
    info = PdfInfo(title, author, None, Language.EN, CREATED)
    data = build(fonts, Layout(GEOMETRY, (LaidOutPage(),)), info)
    with pikepdf.open(io.BytesIO(data)) as pdf:
        meta = pdf.open_metadata()
        assert meta["dc:title"] == title == str(pdf.docinfo["/Title"])
        assert meta["dc:creator"] == [author]
        assert str(pdf.Root.Lang) == "en"
        assert "/Subject" not in pdf.docinfo
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        assert pdf.metadata["Title"] == title


def test_bookmarks_nest_by_level(sample: bytes) -> None:
    with pikepdf.open(io.BytesIO(sample)) as pdf, pdf.open_outline() as outline:
        (first, second) = outline.root
        assert first.title == "1 Kapitel 1" and second.title == "2 Kapitel 2"
        (section,) = first.children
        assert section.title == "1.1 Abschnitt 1.1"
        assert [c.title for c in section.children] == ["1.1.1 Unterabschnitt 1.1.1"]


def test_nesting_never_skips_a_level() -> None:
    marks = [Bookmark(str(level), level, 0, 0) for level in (3, 1, 3, 2, 3, 1)]
    assert nest(marks) == [0, 0, 1, 1, 2, 0]


def test_external_and_internal_links_work(sample: bytes) -> None:
    with pikepdf.open(io.BytesIO(sample)) as pdf:
        annotations = list(pdf.pages[0].obj.Annots)
        uri = next(a for a in annotations if "/A" in a)
        assert uri.A.S == pikepdf.Name.URI and str(uri.A.URI) == "https://www.pta.de/"
        internal = next(a for a in annotations if "/Dest" in a)
        destination = internal.Dest
        if not isinstance(destination, pikepdf.Array):  # a named destination
            names = pdf.Root.Names.Dests.Names
            keys = [str(names[i]) for i in range(0, len(names), 2)]
            destination = names[keys.index(str(destination)) + 1]
            if isinstance(destination, pikepdf.Dictionary):
                destination = destination.D
        assert destination[0].objgen == pdf.pages[1].obj.objgen


def test_an_unknown_link_target_is_a_layout_bug(fonts: PdfFonts) -> None:
    page = LaidOutPage((LinkItem(0, 0, 10, 10, target="nirgends"),))
    with pytest.raises(ValueError, match="nirgends"):
        render(Layout(GEOMETRY, (page,)), fonts, INFO)


def test_equal_images_are_embedded_once(sample: bytes) -> None:
    with pikepdf.open(io.BytesIO(sample)) as pdf:
        images = [
            obj
            for obj in pdf.objects
            if isinstance(obj, pikepdf.Stream) and obj.get("/Subtype") == pikepdf.Name.Image
        ]
    assert len(images) == 1


def test_equal_input_gives_equal_bytes(fonts: PdfFonts, sample: bytes) -> None:
    assert build(PdfFonts(bundled())) == sample
    later = PdfInfo(INFO.title, INFO.author, INFO.subject, INFO.language, CREATED.replace(hour=13))
    assert build(fonts, info=later) != sample


def test_fonts_are_registered_by_content(fonts: PdfFonts) -> None:
    regular = fonts.fonts.file(FontFace.REGULAR)
    assert fonts.name(FontFace.REGULAR) == registered_name(regular)
    assert fonts.name(FontFace.ITALIC) == fonts.name(FontFace.REGULAR)
    assert fonts.synthetic_italic(FontFace.ITALIC)
    assert not fonts.synthetic_italic(FontFace.REGULAR)
    assert fonts.has_glyph("ż", FontFace.REGULAR)
    assert not fonts.has_glyph("ж", FontFace.REGULAR)
    assert fonts.width("ab", FontFace.REGULAR, 10) == pytest.approx(
        fonts.width("a", FontFace.REGULAR, 10) + fonts.width("b", FontFace.REGULAR, 10)
    )


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
