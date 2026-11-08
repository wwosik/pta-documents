"""E06-S01: the chart as a ``Drawing`` (cases of DocLibs ``ChartTests.cs``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pta_documents.charts import ChartColors, draw, format_number, parse, scale
from pta_documents.design import colors
from pta_documents.design.variants import Language
from pta_documents.drawing import DrawingShape, DrawingText, ShapeKind, to_svg
from tests.charts.test_parser import ORDERS


def test_the_scale_runs_from_zero_to_a_round_top() -> None:
    assert scale(parse(ORDERS)) == (0, 150, 25)
    assert scale(parse("x, a\n1, -15\n2, 55\n")) == (-20, 60, 20)
    # Stacked: the sum, 252.
    assert scale(parse("stacked: true\n---\nx, a, b\n1, 120, 132\n")).high == 300
    assert scale(parse("x, a\n1, 0\n")) == (0, 1, 0.2)


def test_a_bar_per_value_the_title_and_a_legend() -> None:
    drawing = draw(parse(ORDERS))
    fills = {colors.PTA_BLUE, colors.DARK_BLUE}
    bars = [
        item
        for item in drawing.items
        if isinstance(item, DrawingShape)
        and item.kind is ShapeKind.RECTANGLE
        and item.fill in fills
    ]
    assert len(bars) == 5 + 2  # five values (one empty) and two legend swatches
    texts = [item.text for item in drawing.items if isinstance(item, DrawingText)]
    for text in ("Orders by month", "k", "Quelle: erfunden", "plan", "actual", "Mar", "150"):
        assert text in texts
    assert (drawing.width, drawing.height) == (640, 380)


def test_every_colour_is_a_pta_colour() -> None:
    palette = {*colors.ACCENTS, colors.TEXT_WORD, colors.GREY_LIGHT, colors.GREY_MID}
    palette |= {colors.tint(c, 0.55) for c in colors.ACCENTS}
    for code in (
        ORDERS,
        "type: line\n---\nx, a, b\n1, 2, 3\n2, , 1\n",
        "type: area\n---\nx, a, b\n1, 2, 3\n2, 4, 1\n",
    ):
        for item in draw(parse(code)).items:
            if isinstance(item, DrawingShape):
                assert {item.fill, item.stroke} - {None} <= palette
            elif isinstance(item, DrawingText):
                assert item.color == colors.TEXT_WORD


def test_series_follow_the_accent_order() -> None:
    code = "x, " + ", ".join(f"s{n}" for n in range(7)) + "\n1, " + ", ".join(["1"] * 7) + "\n"
    swatches = [
        item.fill
        for item in draw(parse(code)).items
        if isinstance(item, DrawingShape) and item.kind is ShapeKind.RECTANGLE
    ]
    assert swatches[-7:] == [*colors.ACCENTS, colors.ACCENTS[0]]


def test_lines_break_at_gaps_and_dot_every_value() -> None:
    drawing = draw(parse("type: line\n---\nx, a\n1, 2\n2,\n3, 4\n4, 5\n"))
    (line,) = [
        item
        for item in drawing.items
        if isinstance(item, DrawingShape)
        and item.stroke == colors.PTA_BLUE
        and item.stroke_width == 2.5
    ]
    kinds = [type(segment).__name__ for segment in line.path.segments]
    assert kinds == ["MoveTo", "MoveTo", "LineTo"]
    dots = [i for i in drawing.items if isinstance(i, DrawingShape) and i.kind is ShapeKind.ELLIPSE]
    assert len(dots) == 3


def test_overlapping_areas_are_lighter_stacked_ones_are_not() -> None:
    def fills(code: str) -> set[str | None]:
        return {
            item.fill
            for item in draw(parse(code)).items
            if isinstance(item, DrawingShape) and item.kind is ShapeKind.PATH and item.fill
        }

    assert fills("type: area\n---\nx, a\n1, 2\n2, 3\n") == {colors.tint(colors.PTA_BLUE, 0.55)}
    assert fills("type: area\nstacked: true\n---\nx, a\n1, 2\n2, 3\n") == {colors.PTA_BLUE}


@pytest.mark.parametrize(
    ("value", "language", "text"),
    [
        (1250.5, Language.DE, "1.250,5"),
        (1250.5, Language.EN, "1,250.5"),
        (-0.0000001, Language.DE, "0"),
        (25, Language.DE, "25"),
        (0.1 + 0.2, Language.EN, "0.3"),
    ],
)
def test_numbers_are_written_in_the_document_language(
    value: float, language: Language, text: str
) -> None:
    assert format_number(value, language) == text


def test_the_text_colour_can_be_the_slides(review_dir: Path) -> None:
    drawing = draw(parse(ORDERS), Language.DE, ChartColors(text=colors.TEXT_SLIDES))
    assert {i.color for i in drawing.items if isinstance(i, DrawingText)} == {colors.TEXT_SLIDES}
    # The PDF draws the drawing (E05-S04); the SVG shows the title as text too.
    svg = to_svg(drawing)
    assert "Orders by month" in svg
    pages = [
        to_svg(draw(parse(code)))
        for code in (
            ORDERS,
            "type: line\ntitle: Linien\n---\nx, a, b\n1, 2, 3\n2, , 1\n3, 4, 2\n",
            "type: area\ntitle: Flächen\n---\nx, a, b\n1, 2, 3\n2, 4, 1\n3, 3, 2\n",
            "type: area\nstacked: true\ntitle: Gestapelt\n---\nx, a, b\n1, 2, 3\n2, 4, 1\n",
            "type: bar\nstacked: true\ntitle: Gestapelt\n---\nx, a, b\n1, 2, 3\n2, -4, 1\n",
            "title: Negativ\n---\nx, a, b\n1, -15, 3\n2, 55, 1\n",
        )
    ]
    (review_dir / "charts.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Charts</title>" + "".join(pages),
        encoding="utf-8",
    )


def test_tint_mixes_a_pta_colour_with_white() -> None:
    assert colors.tint(colors.PTA_BLUE, 1) == colors.PTA_BLUE
    assert colors.tint(colors.PTA_BLUE, 0) == colors.WHITE
    with pytest.raises(ValueError, match="between 0 and 1"):
        colors.tint(colors.PTA_BLUE, 1.5)
