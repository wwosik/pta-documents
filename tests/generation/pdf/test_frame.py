"""E05-S03: the PTA page frame of the PDF — cover, table of contents, header and footer in all
four template variants, read back with pdfplumber and pikepdf. The PDFs go to
``.tmp/review/frame-<variante>.pdf``."""

from __future__ import annotations

import datetime as dt
import io
from typing import Any, Final

import pdfplumber
import pikepdf
import pytest

from pta_documents.design import colors, word_frame
from pta_documents.design.fonts import FontFace, bundled
from pta_documents.design.variants import WordVariant
from pta_documents.design.word_styles import POINTS_PER_CM
from pta_documents.generation.pdf import PdfGenerator, PdfOptions
from pta_documents.generation.pdf.frame import ELLIPSIS, LOGO_FORM, fit
from pta_documents.generation.pdf.layout.fonts import register
from pta_documents.markdown import MarkdownDocument
from tests.conftest import REVIEW_DIR
from tests.generation.pdf.support import type_area

CREATED: Final = dt.datetime(2026, 11, 8, 9, 0, tzinfo=dt.UTC)
OPTIONS: Final = PdfOptions(created=CREATED, system_fonts=False)
FILLER: Final = "Wort " * 230
BODY: Final = "\n\n".join(
    f"# Kapitel {n}\n\n{FILLER}\n\n## Abschnitt {n}.1\n\nText\n\n### Tiefer {n}\n\nMehr"
    for n in (1, 2, 3)
)
PORTRAIT: Final = (WordVariant.PORTRAIT, WordVariant.PORTRAIT_NO_COVER)


def front(variant: WordVariant, **extra: str) -> str:
    keys = {
        "vorlage": variant.value,
        "titel": "Jahresbericht",
        "untertitel": "Ergebnisse 2026",
        "autor": "Anna Nowak",
        "ort": "Mannheim",
        "datum": "06.11.2026",
        **extra,
    }
    return "---\n" + "".join(f"{k}: {v}\n" for k, v in keys.items()) + "---\n"


def generate(markdown: str) -> tuple[bytes, int]:
    output = io.BytesIO()
    result = PdfGenerator().generate(MarkdownDocument(markdown), output, OPTIONS)
    assert result.pages is not None
    return output.getvalue(), result.pages


def cm(points: float) -> float:
    return round(points / POINTS_PER_CM, 2)


def lines(page: Any, top: float, bottom: float) -> list[str]:
    """The text lines of ``page`` between ``top`` and ``bottom`` (points from the top)."""
    text = page.crop((0, top, page.width, bottom)).extract_text() or ""
    return [line for line in text.split("\n") if line]


def header_lines(page: Any) -> list[str]:
    return lines(page, 0, word_frame.read(variant_of(page)).page.top_pt)


def footer_lines(page: Any) -> list[str]:
    setup = word_frame.read(variant_of(page)).page
    return lines(page, page.height - setup.bottom_pt, page.height)


def variant_of(page: Any) -> WordVariant:
    portrait = float(page.height) > float(page.width)
    return WordVariant.PORTRAIT_NO_COVER if portrait else WordVariant.LANDSCAPE_NO_COVER


def rules(pdf: pikepdf.Pdf, index: int) -> list[tuple[float, float, float]]:
    """``(x, y from the top, width)`` in cm of every gradient rule (a clipped shading)."""
    page = pdf.pages[index]
    height = float(page.mediabox[3])
    result: list[tuple[float, float, float]] = []
    rect: list[float] = []
    for operands, operator in pikepdf.parse_content_stream(page):
        if str(operator) == "re":
            rect = [float(v) for v in operands]
        elif str(operator) == "sh":
            x, y, width, stroke = rect
            result.append((cm(x), cm(height - y - stroke / 2), cm(width)))
    return result


@pytest.fixture(scope="module", params=list(WordVariant), ids=lambda v: v.value)
def variant(request: pytest.FixtureRequest) -> WordVariant:
    return request.param


@pytest.fixture(scope="module")
def document(variant: WordVariant) -> tuple[bytes, int]:
    data, pages = generate(front(variant, inhaltsverzeichnis="ja") + BODY)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    (REVIEW_DIR / f"frame-{variant.value}.pdf").write_bytes(data)
    return data, pages


def test_every_page_has_the_size_and_orientation_of_the_template(
    variant: WordVariant, document: tuple[bytes, int]
) -> None:
    data, pages = document
    expected = (21.0, 29.7) if variant in PORTRAIT else (29.7, 21.0)
    with pikepdf.open(io.BytesIO(data)) as pdf:
        assert len(pdf.pages) == pages
        for page in pdf.pages:
            assert (cm(float(page.mediabox[2])), cm(float(page.mediabox[3]))) == expected


def test_the_logo_is_one_form_at_the_anchor_of_the_template(
    variant: WordVariant, document: tuple[bytes, int]
) -> None:
    data, pages = document
    (logo,) = word_frame.read(variant).other.header.pictures
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            shapes = [c for c in page.curves if c["top"] < logo.y_pt + logo.height_pt + 1]
            box = (
                min(c["x0"] for c in shapes),
                min(c["top"] for c in shapes),
                max(c["x1"] for c in shapes),
                max(c["bottom"] for c in shapes),
            )
            # The paths of the word mark fill the box of the picture.
            assert box[0] == pytest.approx(logo.x_pt, abs=2)
            assert box[1] == pytest.approx(logo.y_pt, abs=2)
            assert box[2] <= logo.x_pt + logo.width_pt + 0.5
            assert box[3] <= logo.y_pt + logo.height_pt + 0.5
    with pikepdf.open(io.BytesIO(data)) as pdf:
        forms = {
            obj.objgen
            for page in pdf.pages
            for name, obj in page.Resources.XObject.items()
            if name.endswith(LOGO_FORM)
        }
    assert len(forms) == 1 and pages > 1


def test_the_rules_sit_where_the_template_anchors_them(
    variant: WordVariant, document: tuple[bytes, int]
) -> None:
    data, pages = document
    width = 16.6 if variant in PORTRAIT else 25.3
    header, footer = (2.80, 28.20) if variant in PORTRAIT else (3.40, 19.20)
    with pikepdf.open(io.BytesIO(data)) as pdf:
        first = rules(pdf, 0)
        if variant is WordVariant.PORTRAIT:
            assert first == [(2.2, 2.80, width)]
        elif variant is WordVariant.LANDSCAPE:
            assert first == [(2.2, 6.00, width)]
        else:
            assert first == [(2.2, header, width), (2.2, footer, width)]
        for index in range(1, pages):
            assert rules(pdf, index) == [(2.2, header, width), (2.2, footer, width)]
        shading = next(iter(pdf.pages[1].Resources.Shading.values()))
        function = shading.Function
        assert [float(v) for v in function.Functions[0].C0] == pytest.approx(
            [0x00 / 255, 0x6F / 255, 0xB9 / 255]
        )
        assert [float(v) for v in function.Functions[-1].C1] == [1.0, 1.0, 1.0]
        assert [float(v) for v in function.Bounds] == [0.53]


def test_the_header_shows_title_and_subtitle_from_the_second_page(
    variant: WordVariant, document: tuple[bytes, int]
) -> None:
    data, _ = document
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        start = 1 if variant.has_cover else 0
        for page in pdf.pages[start:]:
            assert header_lines(page) == ["Jahresbericht", "Ergebnisse 2026"]
        if variant.has_cover:
            assert header_lines(pdf.pages[0]) == []
        page = pdf.pages[start]
        title = next(c for c in page.chars if c["top"] < 60 and c["text"] == "J")
        assert title["size"] == pytest.approx(10)
        assert "Bold" in title["fontname"] or title["fontname"].endswith(bold_font())
        assert tuple(round(v, 3) for v in title["non_stroking_color"]) == blue()


def bold_font() -> str:
    return register(bundled()).name(FontFace.BOLD)


def blue() -> tuple[float, ...]:
    value = int(colors.PTA_BLUE, 16)
    return tuple(round(((value >> s) & 0xFF) / 255, 3) for s in (16, 8, 0))


def test_the_footer_shows_company_date_and_page_but_not_on_the_cover(
    variant: WordVariant, document: tuple[bytes, int]
) -> None:
    data, pages = document
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for n, page in enumerate(pdf.pages, start=1):
            if n == 1 and variant.has_cover:
                assert footer_lines(page) == []
                continue
            assert footer_lines(page) == [f"PTA IT-Beratung Stand: 06.11.2026 Seite {n} | {pages}"]
        page = pdf.pages[1]
        sizes = {round(c["size"], 1) for c in page.chars if c["top"] > page.height - 50}
        assert sizes == {6.5}


def test_the_cover_shows_title_subtitle_and_byline_below_the_first_header(
    variant: WordVariant, document: tuple[bytes, int]
) -> None:
    data, _ = document
    frame = word_frame.read(variant)
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        page = type_area(pdf.pages[0])
        text = (page.extract_text() or "").split("\n")
        top = min(c["top"] for c in page.chars)
        first = page.chars[0]
    if not variant.has_cover:
        # No cover: the first page starts with the contents at the top margin.
        assert text[0] == "INHALT"
        assert frame.page.top_pt < top < frame.page.top_pt + 20
        return
    assert text == ["Jahresbericht", "Ergebnisse 2026", "Anna Nowak, Mannheim, 06.11.2026"]
    body_top = word_frame.body_top(frame, 1, bundled().file(FontFace.REGULAR).info.line_height)
    assert body_top > frame.page.top_pt + 2 * POINTS_PER_CM
    assert body_top < top < body_top + 40
    assert first["size"] == pytest.approx(34)


def test_the_table_of_contents_names_the_pages_and_links_them(
    variant: WordVariant, document: tuple[bytes, int]
) -> None:
    data, _ = document
    contents = 1 if variant.has_cover else 0
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        text = (type_area(pdf.pages[contents]).extract_text() or "").split("\n")
        found: dict[str, int] = {}
        for n, page in enumerate(pdf.pages, start=1):
            for line in (type_area(page).extract_text() or "").split("\n"):
                if n != contents + 1 and line.startswith(
                    ("1 Kapitel", "2 Kapitel", "3 Kapitel", "1.1 ", "2.1 ", "3.1 ")
                ):
                    found.setdefault(line, n)
        links = pdf.pages[contents].annots
    assert text[0] == "INHALT"
    entries = text[1:]
    assert len(entries) == 6  # levels 1 and 2 only, as TOC \o "1-2"
    assert not any("Tiefer" in e for e in entries)
    expected: list[int] = []
    for entry in entries:
        heading, page = entry.rsplit(" ", 1)
        heading = heading.rstrip(". ")
        assert found[heading] == int(page), entry
        expected.append(int(page))
    assert any(entry.count(".") > 10 for entry in entries if entry.startswith("1.1"))
    assert not any(entry.count(".") > 10 for entry in entries if entry.startswith("1 "))
    assert len(links) == 6
    with pikepdf.open(io.BytesIO(data)) as pdf:
        numbers: dict[Any, int] = {p.objgen: n for n, p in enumerate(pdf.pages, start=1)}
        annotations: Any = pdf.pages[contents].Annots
        targets = [numbers[a.Dest[0].objgen] for a in annotations]
    assert targets == expected


def test_company_and_language_change_the_footer() -> None:
    data, pages = generate(
        front(WordVariant.PORTRAIT_NO_COVER, firma="Muster GmbH", sprache="en") + "Text\n"
    )
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        assert footer_lines(pdf.pages[0]) == ["Muster GmbH As of: 06.11.2026 Page 1 | 1"]
    assert pages == 1


def test_without_a_date_the_footer_shows_the_day_of_creation() -> None:
    markdown = "---\nvorlage: quer-ohne-deckblatt\ntitel: T\n---\nText\n"
    data, _ = generate(markdown)
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        assert footer_lines(pdf.pages[0]) == ["PTA IT-Beratung Stand: 08.11.2026 Seite 1 | 1"]
        # Without a subtitle the title stands alone in the middle of the header table.
        assert header_lines(pdf.pages[0]) == ["T"]


def test_without_a_table_of_contents_the_body_follows_the_cover() -> None:
    data, pages = generate(front(WordVariant.PORTRAIT) + "# Einleitung\n\nText\n")
    assert pages == 2
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        assert (type_area(pdf.pages[1]).extract_text() or "").split("\n") == [
            "1 Einleitung",
            "Text",
        ]


def test_a_cover_without_subtitle_and_author_shows_the_title_only() -> None:
    data, _ = generate("---\ntitel: Nur der Titel\n---\nText\n")
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        page = pdf.pages[0]
        assert lines(page, 0, page.height) == ["Nur der Titel"]
        assert header_lines(pdf.pages[1]) == ["Nur der Titel"]


def test_too_long_header_texts_end_with_an_ellipsis() -> None:
    fonts = register(bundled())
    font = fonts.name(FontFace.BOLD)
    assert fit("kurz", font, 10, 100) == "kurz"
    cut = fit("ein sehr langer Titel " * 10, font, 10, 100)
    assert cut.endswith(ELLIPSIS) and fonts.width(cut, FontFace.BOLD, 10) <= 100
    title = "Ein Titel, der viel zu lang für die Kopfzeile ist " * 3
    data, _ = generate(front(WordVariant.PORTRAIT_NO_COVER, titel=title.strip()) + "Text\n")
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        first = header_lines(pdf.pages[0])[0]
        chars = [c for c in pdf.pages[0].chars if c["top"] < 60]
    assert first.endswith(ELLIPSIS)
    assert cm(max(c["x1"] for c in chars)) <= 2.2 + 11.5
