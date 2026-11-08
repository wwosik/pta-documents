"""E05-S03: the page frame read from the Word templates matches the design analysis
(``spec/10-analysen/2026-11-06 pta-designstandards.md``, *Kopf- und Fußzeile*, *Deckblatt*)."""

from __future__ import annotations

from typing import Final

import pytest

from pta_documents.design import colors, word_frame, word_styles
from pta_documents.design.variants import WordVariant
from pta_documents.design.word_frame import (
    Alignment,
    Band,
    FrameField,
    FrameParagraph,
    FrameTable,
    GradientStop,
    VerticalAlignment,
)
from pta_documents.design.word_styles import POINTS_PER_CM, LineRule

PORTRAIT: Final = (WordVariant.PORTRAIT, WordVariant.PORTRAIT_NO_COVER)
LANDSCAPE: Final = (WordVariant.LANDSCAPE, WordVariant.LANDSCAPE_NO_COVER)
NATURAL: Final = 1.33
"""About the single line of Segoe UI and Selawik."""


def cm(points: float) -> float:
    return round(points / POINTS_PER_CM, 2)


def table(band: Band) -> FrameTable:
    (result,) = [b for b in band.blocks if isinstance(b, FrameTable)]
    return result


@pytest.mark.parametrize("variant", list(WordVariant))
def test_the_logo_sits_where_the_template_anchors_it(variant: WordVariant) -> None:
    frame = word_frame.read(variant)
    expected = (16.58, 1.09, 2.22, 1.28) if variant in PORTRAIT else (24.49, 1.05, 3.01, 1.73)
    kinds = [frame.other] + ([frame.first] if frame.first else [])
    for kind in kinds:
        (logo,) = kind.header.pictures
        assert (cm(logo.x_pt), cm(logo.y_pt), cm(logo.width_pt), cm(logo.height_pt)) == expected
        assert not kind.footer.pictures
    # Right on the type area in portrait.
    if variant in PORTRAIT:
        (logo,) = frame.other.header.pictures
        assert logo.x_pt + logo.width_pt == pytest.approx(frame.page.width_pt - frame.page.right_pt)


@pytest.mark.parametrize("variant", list(WordVariant))
def test_the_rules_run_over_the_type_area_with_the_gradient(variant: WordVariant) -> None:
    frame = word_frame.read(variant)
    width, header, footer = (16.6, 2.80, 28.20) if variant in PORTRAIT else (25.3, 3.40, 19.20)
    ((top,), (bottom,)) = frame.other.header.rules, frame.other.footer.rules
    assert (cm(top.x_pt), cm(top.y_pt), cm(top.width_pt)) == (2.2, header, width)
    assert (cm(bottom.x_pt), cm(bottom.y_pt), cm(bottom.width_pt)) == (2.2, footer, width)
    for rule in (top, bottom):
        assert rule.stroke_pt == 0.5  # lnRef idx="1": the first line style of the theme
        assert rule.stops == (
            GradientStop(0.0, colors.PTA_BLUE),
            GradientStop(0.53, colors.LIGHT_BLUE),
            GradientStop(1.0, colors.LIGHT_BLUE, 0.0),
        )


@pytest.mark.parametrize("variant", list(WordVariant))
def test_only_the_cover_templates_have_a_first_page(variant: WordVariant) -> None:
    frame = word_frame.read(variant)
    if not variant.has_cover:
        assert frame.first is None
        assert frame.kind(1) is frame.other
        return
    assert frame.first is not None and frame.kind(1) is frame.first
    assert frame.kind(2) is frame.other
    # Logo and rule only: no header texts, no footer.
    (rule,) = frame.first.header.rules
    assert cm(rule.y_pt) == (2.80 if variant in PORTRAIT else 6.00)
    assert frame.first.footer == Band()
    assert all(
        isinstance(b, FrameParagraph) and b.field is FrameField.NONE
        for b in frame.first.header.blocks
    )


@pytest.mark.parametrize("variant", list(WordVariant))
def test_the_header_table_holds_title_and_subtitle(variant: WordVariant) -> None:
    frame = word_frame.read(variant)
    header = table(frame.other.header)
    (row,) = header.rows
    (cell,) = row.cells
    assert cm(header.x_pt) == 2.2
    assert cm(header.width_pt) == (11.5 if variant in PORTRAIT else 17.5)
    assert row.height_rule is LineRule.EXACT
    assert cell.v_align is VerticalAlignment.CENTER
    title, subtitle = cell.paragraphs
    assert (title.field, subtitle.field) == (FrameField.TITLE, FrameField.SUBTITLE)
    assert title.format.name == subtitle.format.name == "header"
    assert (title.format.size_pt, title.format.bold, title.format.color) == (
        10,
        True,
        colors.PTA_BLUE,
    )
    assert (subtitle.format.bold, subtitle.format.color) == (False, colors.TEXT_WORD)


@pytest.mark.parametrize("variant", list(WordVariant))
def test_the_footer_table_holds_company_date_and_page(variant: WordVariant) -> None:
    frame = word_frame.read(variant)
    footer = table(frame.other.footer)
    (row,) = footer.rows
    cells = [(cm(c.width_pt), [(p.field, p.align) for p in c.paragraphs]) for c in row.cells]
    if variant in PORTRAIT:
        assert cells == [
            (5.53, [(FrameField.COMPANY, Alignment.LEFT)]),
            (5.53, [(FrameField.AS_OF, Alignment.CENTER)]),
            (5.54, [(FrameField.PAGE, Alignment.RIGHT)]),
        ]
    else:
        assert cells == [
            (6.99, [(FrameField.COMPANY, Alignment.LEFT)]),
            (6.99, [(FrameField.AS_OF, Alignment.LEFT)]),
            (6.99, [(FrameField.NONE, Alignment.LEFT)]),
            (4.34, [(FrameField.PAGE, Alignment.RIGHT)]),
        ]
    assert cm(footer.width_pt) == cm(frame.page.text_width_pt)
    company, as_of, page = (row.cells[i].paragraphs[0].format for i in (0, 1, -1))
    for fmt in (company, as_of, page):
        assert fmt.size_pt == 6.5
        assert (fmt.line_pt, fmt.line_rule) == (9.5, LineRule.AT_LEAST)
    assert (company.bold, company.color) == (True, colors.PTA_BLUE)
    assert (as_of.bold, as_of.color) == (False, colors.TEXT_WORD)
    assert (page.bold, page.color) == (True, colors.PTA_BLUE)


@pytest.mark.parametrize("variant", list(WordVariant))
def test_the_page_is_the_page_of_the_styles(variant: WordVariant) -> None:
    assert word_frame.read(variant).page == word_styles.read(variant).page


@pytest.mark.parametrize(
    ("variant", "first", "other"),
    [
        (WordVariant.PORTRAIT, 8.50, 3.50),
        (WordVariant.PORTRAIT_NO_COVER, 3.50, 3.50),
        (WordVariant.LANDSCAPE, 6.79, 4.20),
        (WordVariant.LANDSCAPE_NO_COVER, 4.20, 4.20),
    ],
)
def test_the_cover_header_moves_the_text_down_as_in_word(
    variant: WordVariant, first: float, other: float
) -> None:
    """The first header of ``hoch``/``quer`` is an empty paragraph with 200/150 pt after it:
    Word starts the text of the cover below it."""
    frame = word_frame.read(variant)
    assert cm(word_frame.body_top(frame, 1, NATURAL)) == first
    assert cm(word_frame.body_top(frame, 2, NATURAL)) == other
    # The footer (19 pt) ends at the footer distance above the bottom of the page.
    assert word_frame.band_height(frame.other.footer, NATURAL) == pytest.approx(19.0)
    assert word_frame.footer_bottom(frame) == frame.page.height_pt - frame.page.footer_pt
