"""E05-S02: the Word styles read from the templates match the design analysis
(``spec/10-analysen/2026-11-06 pta-designstandards.md``, *Formatvorlagen* and *Seite*)."""

from __future__ import annotations

import pytest

from pta_documents.design import colors, word
from pta_documents.design.variants import WordVariant
from pta_documents.design.word_styles import POINTS_PER_CM, LineRule, read

ANALYSIS = {
    # style: (size, bold, caps, colour, before, after, line "mindestens")
    "Normal": (10, False, False, colors.TEXT_WORD, 6, 6, 14),
    "Title": (34, True, False, colors.PTA_BLUE, 0, 14, 38),
    "Subtitle": (22, False, False, colors.PTA_BLUE, 14, 0, 26),
    "Autor": (14, False, False, colors.TEXT_WORD, 14, 0, 18),
    "heading 1": (14, True, False, colors.PTA_BLUE, 14, 9, 18),
    "heading 2": (12, True, False, colors.TEXT_WORD, 14, 9, 16),
    "heading 3": (12, False, False, colors.TEXT_WORD, 14, 9, 16),
    "Standard fett": (10, True, False, colors.TEXT_WORD, 14, 6, 14),
    "List Bullet": (10, False, False, colors.TEXT_WORD, 6, 6, 14),
    "List Paragraph": (10, False, False, colors.TEXT_WORD, 6, 6, 14),
    "caption": (8, False, False, colors.PTA_BLUE, 6, 14, 12),
    "footnote text": (8, False, False, colors.TEXT_WORD, 6, 6, 9.6),
}


def cm(value: float) -> float:
    return value * POINTS_PER_CM


@pytest.mark.parametrize("variant", list(WordVariant))
@pytest.mark.parametrize("name", sorted(ANALYSIS))
def test_paragraph_styles_match_the_design_analysis(variant: WordVariant, name: str) -> None:
    size, bold, caps, color, before, after, line = ANALYSIS[name]
    style = read(variant).paragraph(name)
    assert style.size_pt == size
    assert style.bold is bold
    assert style.caps is caps
    assert style.color == color
    assert (style.space_before_pt, style.space_after_pt) == (before, after)
    assert style.line_rule is LineRule.AT_LEAST
    assert style.line_pt == line


@pytest.mark.parametrize(
    ("variant", "before"),
    [
        (WordVariant.PORTRAIT, 14),
        (WordVariant.PORTRAIT_NO_COVER, 0),
        (WordVariant.LANDSCAPE, 14),
        (WordVariant.LANDSCAPE_NO_COVER, 14),
    ],
)
def test_the_sub_heading_differs_by_variant(variant: WordVariant, before: float) -> None:
    style = read(variant).paragraph(word.STYLES.sub_heading)
    assert style.caps
    assert style.space_before_pt == before


def test_headings_and_lists_take_their_indents_from_the_numbering() -> None:
    design = read(WordVariant.PORTRAIT)
    for name, indent in (("heading 1", 1.25), ("heading 2", 1.25), ("heading 3", 1.70)):
        style = design.paragraph(name)
        assert style.left_indent_pt == pytest.approx(cm(indent), abs=0.1)
        assert style.hanging_pt == pytest.approx(cm(indent), abs=0.1)
        assert style.numbering is not None
    texts = [design.level(design.paragraph(n)) for n in word.STYLES.headings]
    assert [t.text if t else None for t in texts] == ["%1", "%1.%2", "%1.%2.%3"]
    bullet = design.paragraph(word.STYLES.list_bullet)
    levels = [design.level(bullet, n) for n in range(3)]
    assert [round(lv.left_pt / POINTS_PER_CM, 1) for lv in levels if lv] == [0.6, 1.2, 1.8]
    assert [lv.color for lv in levels if lv] == [
        colors.PTA_BLUE,
        colors.TEXT_WORD,
        colors.TEXT_WORD,
    ]
    assert [lv.format for lv in levels if lv] == ["bullet"] * 3
    number = design.level(design.paragraph(word.STYLES.list_number))
    assert number is not None
    assert (number.format, number.text) == ("decimal", "%1.")


def test_headings_one_and_two_keep_with_the_next_paragraph() -> None:
    design = read(WordVariant.PORTRAIT)
    assert design.paragraph("heading 1").keep_next
    assert design.paragraph("heading 2").keep_next


def test_the_pta_table_style() -> None:
    table = read(WordVariant.PORTRAIT).table
    assert table.header_fill == colors.PTA_BLUE
    assert table.header_color == colors.WHITE
    assert table.rule_color == colors.GREY_MID
    assert table.rule_pt == 0.5
    assert (table.cell_left_pt, table.cell_right_pt) == (0, 0)
    assert table.space_after_pt == 0
    assert (table.line_rule, table.line_pt) == (LineRule.AUTO, 12)


@pytest.mark.parametrize("variant", list(WordVariant))
def test_the_hyperlink_style_is_borrowed_where_missing(variant: WordVariant) -> None:
    link = read(variant).character(word.STYLES.hyperlink)
    assert link.color == colors.DARK_BLUE
    assert link.underline


@pytest.mark.parametrize(
    ("variant", "margins"),
    [
        (WordVariant.PORTRAIT, (3.50, 2.00, 2.20, 2.20)),
        (WordVariant.PORTRAIT_NO_COVER, (3.50, 2.00, 2.20, 2.20)),
        (WordVariant.LANDSCAPE, (4.20, 2.50, 2.20, 2.20)),
        (WordVariant.LANDSCAPE_NO_COVER, (4.20, 2.50, 2.20, 2.20)),
    ],
)
def test_page_and_margins(variant: WordVariant, margins: tuple[float, ...]) -> None:
    page = read(variant).page
    found = (page.top_pt, page.bottom_pt, page.left_pt, page.right_pt)
    assert [round(v / POINTS_PER_CM, 2) for v in found] == list(margins)
    portrait = variant.orientation.value == "portrait"
    size = (21.0, 29.7) if portrait else (29.7, 21.0)
    assert (
        round(page.width_pt / POINTS_PER_CM, 1),
        round(page.height_pt / POINTS_PER_CM, 1),
    ) == size
    assert round(read(variant).default_tab_pt / POINTS_PER_CM, 2) == 1.25


def test_leading_is_at_least_the_line_of_the_style() -> None:
    normal = read(WordVariant.PORTRAIT).paragraph("Normal")
    assert normal.leading(1.0) == 14
    assert normal.leading(1.6) == 16
