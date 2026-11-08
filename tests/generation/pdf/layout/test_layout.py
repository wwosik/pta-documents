"""E05-S02: the page breaking rules of DocLibs ``LayoutEngine`` (cases of ``LayoutTests.cs``
without the cover, glyph and drawing cases of E05-S03/E05-S04), checked on real PDFs."""

from __future__ import annotations

import pikepdf
import pytest

from pta_documents.design import colors, word, word_styles
from pta_documents.design.variants import WordVariant
from pta_documents.generation.pdf.layout import LayoutSettings
from tests.generation.pdf.layout.support import Pdf, filler, image, make_pdf, rgb, spacer

PORTRAIT = word_styles.read(WordVariant.PORTRAIT).page


def right_edge() -> float:
    return PORTRAIT.width_pt - PORTRAIT.right_pt + 0.5


def test_wrap_breaks_at_spaces_across_styles() -> None:
    words = ["wort", "**fett**", "*kursiv*", "`code`", "weiter"] * 60
    pdf = Pdf(make_pdf(" ".join(words)))
    allowed = {"wort", "fett", "kursiv", "code", "weiter"}
    lines = pdf.lines_on(0)
    assert len(lines) > 3
    for line in lines:
        assert set(line.text.split()) <= allowed


def test_wrap_breaks_a_word_wider_than_the_line_by_characters() -> None:
    pdf = Pdf(make_pdf("A" * 400))
    assert len(pdf.lines) > 1
    assert "".join(line.text for line in pdf.lines) == "A" * 400
    assert max(float(c["x1"]) for line in pdf.lines for c in line.chars) <= right_edge()


def test_wrap_honours_hard_breaks() -> None:
    pdf = Pdf(make_pdf("erste\\\nzweite"))
    assert [line.text for line in pdf.lines] == ["erste", "zweite"]


def test_code_breaks_long_lines_inside_the_area() -> None:
    pdf = Pdf(make_pdf("```\n" + "x = 1; " * 60 + "\n```"))
    assert len(pdf.lines) > 1
    assert max(float(c["x1"]) for line in pdf.lines for c in line.chars) <= right_edge()


FOLLOWING = {
    "paragraph": ("Erster Satz des Absatzes. " * 30, "Erster Satz"),
    "table": ("| Kopf | Wert |\n| --- | --- |\n| a | b |\n| c | d |", "Kopf"),
    "list": ("- Erster Punkt\n- Zweiter Punkt\n- Dritter Punkt", "Erster Punkt"),
    "code": ("```\nerste Zeile\nzweite Zeile\ndritte Zeile\n```", "erste Zeile"),
    "heading": ("### Darunter\n\nText darunter. " + "Mehr Text. " * 40, "Darunter"),
}


OFFSETS = range(330, 430, 5)
"""Points of spacer below ten paragraphs: the heading moves through the foot of page 1."""


@pytest.mark.parametrize("offset", OFFSETS)
@pytest.mark.parametrize("following", sorted(FOLLOWING))
def test_headings_stay_with_the_start_of_what_follows_wherever_the_page_breaks(
    offset: int, following: str
) -> None:
    markdown, first = FOLLOWING[following]
    push, resource = spacer(offset)
    pdf = Pdf(make_pdf(filler(10) + push + "## Überschrift\n\n" + markdown, [resource]))
    assert pdf.page_of("Überschrift") == pdf.page_of(first)
    if following == "heading":
        assert pdf.page_of("Darunter") == pdf.page_of("Text darunter")


@pytest.mark.parametrize("offset", OFFSETS)
def test_a_heading_stays_with_its_image(offset: int) -> None:
    push, resource = spacer(offset)
    markdown = filler(10) + push + "## Überschrift\n\n![](bild.png)\n"
    pdf = Pdf(make_pdf(markdown, [resource, image("bild.png", 400, 100)]))
    page = pdf.page_of("Überschrift")
    assert [i for i in pdf.images[page] if float(i["width"]) > 10]


@pytest.mark.parametrize("offset", OFFSETS)
def test_a_heading_stays_with_its_figure_and_caption(offset: int) -> None:
    # E05-S05: an image with a title is a KeepTogether of picture and caption, which once broke
    # the measuring of the heading before it.
    push, resource = spacer(offset)
    markdown = filler(10) + push + '## Überschrift\n\n![](bild.png "Der Plan")\n'
    pdf = Pdf(make_pdf(markdown, [resource, image("bild.png", 400, 100)]))
    page = pdf.page_of("Überschrift")
    assert page == pdf.page_of("Der Plan")
    assert [i for i in pdf.images[page] if float(i["width"]) > 10]


def test_later_top_headings_do_not_start_a_new_page() -> None:
    pdf = Pdf(make_pdf("# Eins\n\nText.\n\n# Zwei\n\nText."))
    assert pdf.pages == 1
    assert pdf.page_of("Zwei") == 0


@pytest.mark.parametrize("offset", range(330, 430, 4))
@pytest.mark.parametrize("count", [2, 3, 4, 5, 6])
def test_paragraphs_never_leave_a_single_line_on_a_page(offset: int, count: int) -> None:
    target = "\\\n".join(f"Zielzeile{n}" for n in range(count))
    push, resource = spacer(offset)
    pdf = Pdf(make_pdf(filler(10) + push + target + "\n", [resource]))
    pages = [pdf.page_of(f"Zielzeile{n}") for n in range(count)]
    for page in set(pages):
        assert pages.count(page) >= 2, pages


def blue_squares(pdf: Pdf, page: int) -> int:
    return sum(
        1
        for rect in pdf.rects[page]
        if float(rect["width"]) < 6
        and float(rect["height"]) < 6
        and tuple(round(float(c), 3) for c in rect["non_stroking_color"] or ())
        == rgb(colors.PTA_BLUE)
    )


@pytest.mark.parametrize("before", [20, 23, 25])
def test_list_markers_move_with_their_first_line(before: int) -> None:
    items = "\n".join(f"- Punkt{n}\\\n  Folgezeile\\\n  Schlusszeile" for n in range(12))
    pdf = Pdf(make_pdf(filler(before) + items + "\n"))
    assert pdf.pages >= 2
    for page in range(pdf.pages):
        first_lines = [line for line in pdf.lines_on(page) if line.text.startswith("Punkt")]
        assert blue_squares(pdf, page) == len(first_lines)


def test_numbers_of_ordered_lists_stand_on_their_first_line() -> None:
    pdf = Pdf(make_pdf("1. Erster\n2. Zweiter\n3. Dritter"))
    assert [line.text for line in pdf.lines] == ["1. Erster", "2. Zweiter", "3. Dritter"]


def table(rows: int) -> str:
    body = "\n".join(f"| Zeile{n} | Wert {n} |" for n in range(rows))
    return "| Kopf A | Kopf B |\n| --- | --- |\n" + body + "\n"


def test_a_long_table_repeats_its_header_on_every_page() -> None:
    pdf = Pdf(make_pdf(table(120)))
    assert pdf.pages >= 3
    for page in range(pdf.pages):
        assert pdf.lines_on(page)[0].text.startswith("Kopf A Kopf B")
    rows = [line.text.split()[0] for line in pdf.lines if line.text.startswith("Zeile")]
    assert rows == [f"Zeile{n}" for n in range(120)]


def test_a_table_row_taller_than_a_page_is_split() -> None:
    tall = "Wort " * 1500
    pdf = Pdf(make_pdf(f"| Schlüssel | Wert |\n| --- | --- |\n| lang | {tall} |\n"))
    assert pdf.pages >= 2
    for page in range(pdf.pages):
        assert pdf.lines_on(page)[0].text.startswith("Schlüssel")
        assert any("Wort" in line.text for line in pdf.lines_on(page))


def test_an_image_that_does_not_fit_moves_to_the_next_page() -> None:
    pdf = Pdf(make_pdf(filler(22) + "![](bild.png)\n", [image("bild.png", 400, 400)]))
    assert pdf.images[0] == []
    assert len(pdf.images[1]) == 1


def test_an_image_taller_than_the_page_is_scaled_down_never_up() -> None:
    pdf = Pdf(
        make_pdf(
            "![](hoch.png)\n\n![](klein.png)\n",
            [image("hoch.png", 400, 4000), image("klein.png", 40, 20)],
        )
    )
    tall, small = [i for page in pdf.images for i in page]
    assert float(tall["height"]) <= PORTRAIT.text_height_pt * word.FIGURE_HEIGHT_SHARE + 0.5
    assert float(tall["width"]) == pytest.approx(float(tall["height"]) / 10, rel=0.01)
    assert float(small["width"]) == pytest.approx(30, abs=0.1)  # 40 px at 96 dpi


def test_a_wide_image_is_shrunk_to_the_text_width() -> None:
    pdf = Pdf(make_pdf("![](breit.png)\n", [image("breit.png", 3000, 300)]))
    (picture,) = pdf.images[0]
    assert float(picture["width"]) == pytest.approx(PORTRAIT.text_width_pt, abs=0.5)
    assert float(picture["x0"]) == pytest.approx(PORTRAIT.left_pt, abs=0.5)


def test_scale_in_the_title_scales_the_image() -> None:
    pdf = Pdf(make_pdf('![](bild.png "scale=0.5")\n', [image("bild.png", 200, 100)]))
    (picture,) = pdf.images[0]
    assert float(picture["width"]) == pytest.approx(75, abs=0.1)
    assert "scale" not in pdf.page_texts[0]


def outline(content: bytes) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    with pikepdf.open(__import__("io").BytesIO(content)) as pdf, pdf.open_outline() as root:

        def walk(items: list[pikepdf.OutlineItem], level: int) -> None:
            for item in items:
                result.append((level, str(item.title)))
                walk(list(item.children), level + 1)

        walk(list(root.root), 0)
    return result


def test_bookmarks_follow_headings_one_to_three_with_their_numbers() -> None:
    markdown = "# Eins\n\n## Zwei\n\n### Drei\n\n#### Vier\n\n# Fünf\n\n### Sechs\n"
    assert outline(make_pdf(markdown)) == [
        (0, "1 Eins"),
        (1, "1.1 Zwei"),
        (2, "1.1.1 Drei"),
        (0, "2 Fünf"),
        (1, "2.0.1 Sechs"),
    ]


def test_landscape_takes_the_page_of_the_landscape_template() -> None:
    pdf = Pdf(make_pdf("Text.", settings=LayoutSettings(variant=WordVariant.LANDSCAPE)))
    page = word_styles.read(WordVariant.LANDSCAPE).page
    assert (pdf.width, pdf.height) == pytest.approx((page.width_pt, page.height_pt))
    line = pdf.line("Text.")
    assert float(line.chars[0]["x0"]) == pytest.approx(page.left_pt, abs=0.5)
