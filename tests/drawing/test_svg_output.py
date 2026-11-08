"""The SVG output of drawings (E02-S03): port of DocLibs ``DrawingSvgTests.cs`` and more."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

import pytest

from pta_documents.design import colors, fonts
from pta_documents.drawing import (
    ClosePath,
    CubicTo,
    Drawing,
    DrawingHotspot,
    DrawingHover,
    DrawingItem,
    DrawingPath,
    DrawingShape,
    DrawingSpan,
    DrawingText,
    LineTo,
    MoveTo,
    ShapeKind,
    SvgOptions,
    TextAnchor,
    estimate_width,
    to_svg,
)
from pta_documents.drawing.svg_output import number
from tests.conftest import REPO_ROOT


def test_shapes_become_their_svg_elements_with_paint_dash_and_joins() -> None:
    svg = to_svg(
        Drawing(
            200,
            100,
            (
                DrawingShape(
                    DrawingPath.rectangle(10, 10, 50, 20),
                    "FF0000",
                    "000000",
                    1.5,
                    kind=ShapeKind.RECTANGLE,
                    dash=(3, 2),
                ),
                DrawingShape(
                    DrawingPath.rectangle(70, 10, 40, 40), None, "00FF00", 1, kind=ShapeKind.ELLIPSE
                ),
                DrawingShape(
                    DrawingPath(
                        (MoveTo(0, 0), LineTo(5, 5), CubicTo(6, 6, 7, 7, 8, 8), ClosePath())
                    ),
                    "0000FF",
                    None,
                    0,
                    round_joins=True,
                ),
                DrawingShape(
                    DrawingPath.rectangle(0, 60, 30, 20),
                    "00FF00",
                    "000000",
                    2,
                    kind=ShapeKind.ROUNDED_RECTANGLE,
                    corner_radius=4,
                    round_joins=True,
                ),
            ),
        )
    )
    assert svg.startswith(
        '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100" viewBox="0 0 200 100"'
    )
    assert (
        '<rect x="10" y="10" width="50" height="20" fill="#FF0000" stroke="#000000"'
        ' stroke-width="1.5" stroke-dasharray="3,2"/>'
    ) in svg
    assert (
        '<ellipse cx="90" cy="30" rx="20" ry="20" fill="none" stroke="#00FF00" stroke-width="1"/>'
    ) in svg
    assert '<path d="M0,0 L5,5 C6,6 7,7 8,8 Z" fill="#0000FF"/>' in svg  # no stroke: no joins
    assert (
        '<rect x="0" y="60" width="30" height="20" rx="4" fill="#00FF00" stroke="#000000"'
        ' stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
    ) in svg
    assert "<style>" not in svg  # nothing to hover
    ElementTree.fromstring(svg)


def test_even_odd_sets_the_fill_rule() -> None:
    path = DrawingPath.rectangle(0, 0, 10, 10)
    assert 'fill="#000000" fill-rule="evenodd"/>' in to_svg(
        Drawing(10, 10, (DrawingShape(path, "000000", None, 0, even_odd=True),))
    )
    assert "fill-rule" not in to_svg(Drawing(10, 10, (DrawingShape(path, "000000", None, 0),)))


def test_text_keeps_anchor_weight_and_span_colours_escaped() -> None:
    text = DrawingText(
        100,
        20,
        (
            DrawingSpan("a < b & "),
            DrawingSpan("bold", bold=True),
            DrawingSpan(" red", color="DC2626"),
        ),
        12,
        "111111",
        anchor=TextAnchor.MIDDLE,
    )
    svg = to_svg(Drawing(200, 50, (text,)))
    assert (
        '<text x="100" y="20" font-size="12" fill="#111111" text-anchor="middle"'
        ' xml:space="preserve">a &lt; b &amp; <tspan font-weight="bold">bold</tspan>'
        '<tspan fill="#DC2626"> red</tspan></text>'
    ) in svg


def test_mono_text_uses_the_mono_family() -> None:
    svg = to_svg(Drawing(10, 10, (DrawingText.line(0, 5, "x", 8, "000000", mono=True),)))
    assert f'font-family="{fonts.CSS_FAMILY}"' in svg
    assert 'text-anchor="end"' not in svg
    assert f'font-family="{fonts.CSS_MONO_FAMILY}" xml:space="preserve">x</text>' in svg


def font_size(svg: str) -> str:
    match = re.search(r'font-size="([0-9.]+)"', svg)
    assert match
    return match.group(1)


def test_a_line_too_wide_for_its_room_is_set_smaller_down_to_70_percent() -> None:
    def line(text: str, room: float) -> str:
        return to_svg(
            Drawing(100, 20, (DrawingText.line(0, 10, text, 10, "000000", max_width=room),))
        )

    assert font_size(line("short", 100)) == "10"
    assert font_size(line("x" * 60, 10)) == "7"
    assert font_size(line("x" * 20, 87)) == "7.5"  # 116 px estimated into 87


def test_hover_text_is_a_pre_placed_tooltip_clamped_to_the_canvas_without_script() -> None:
    svg = to_svg(
        Drawing(
            100,
            60,
            (
                DrawingShape(
                    DrawingPath.rectangle(90, 30, 10, 10),
                    "FF0000",
                    None,
                    0,
                    kind=ShapeKind.RECTANGLE,
                    hover=DrawingHover("A long tooltip text", 95, 30),
                ),
                DrawingHotspot(20, 40, 10, dot="1D4ED8", hover=DrawingHover("Jan: 5", 20, 40)),
            ),
        ),
        SvgOptions(tooltip_fill="222222", background="FAFAFA"),
    )
    assert "<style>" in svg
    assert ".chart-tooltip-bg{fill:#222222;fill-opacity:.94}" in svg
    assert '<rect x="0" y="0" width="100" height="60" fill="#FAFAFA"/>' in svg
    assert svg.count('<g class="chart-hoverable">') == 2
    assert (
        '<circle cx="20" cy="40" r="10" fill="transparent"/><circle class="chart-hover-dot"' in svg
    )
    # 19 characters at 10 px plus padding is about 122 px: wider than the canvas, so it starts at
    # the left edge.
    assert '<rect class="chart-tooltip-bg" x="2" y="7"' in svg
    assert "<script" not in svg
    ElementTree.fromstring(svg)


def test_a_tooltip_is_centred_over_its_point() -> None:
    svg = to_svg(
        Drawing(200, 60, (DrawingHotspot(100, 40, 5, hover=DrawingHover("abc", 100, 40)),))
    )
    width = estimate_width("abc", 10) + 12
    assert f'<rect class="chart-tooltip-bg" x="{number(100 - width / 2)}" y="17"' in svg
    assert '<text class="chart-tooltip-text" x="100" y="29" text-anchor="middle">abc</text>' in svg
    assert "chart-hover-dot" not in svg.split("</style>")[1]  # no dot asked for


def test_the_defaults_take_their_colours_and_fonts_from_the_design() -> None:
    options = SvgOptions()
    assert (options.font_family, options.mono_family) == (fonts.CSS_FAMILY, fonts.CSS_MONO_FAMILY)
    assert (options.tooltip_fill, options.tooltip_text, options.background) == (
        colors.TEXT_SLIDES,
        colors.WHITE,
        None,
    )
    hotspot = DrawingHotspot(5, 5, 3, dot=colors.PTA_BLUE, hover=DrawingHover("x", 5, 5))
    svg = to_svg(Drawing(10, 10, (hotspot,)))
    used = {value.upper() for value in re.findall(r"#([0-9A-Fa-f]{6})", svg)}
    assert used == {colors.TEXT_SLIDES, colors.WHITE, colors.PTA_BLUE}


def test_the_module_spells_out_no_colours() -> None:
    """Stricter than the repo-wide test: no six hex digits at all, quoted or not."""
    source = (REPO_ROOT / "src" / "pta_documents" / "drawing").rglob("*.py")
    hex_word = re.compile(r"\b(?=[A-Fa-f]*\d)[0-9A-Fa-f]{6}\b")
    assert not [p for p in source if hex_word.search(p.read_text("utf-8"))]


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (0, "0"),
        (1.5, "1.5"),
        (1.005, "1"),
        (2.345678, "2.35"),
        (-0.001, "0"),
        (-3.1, "-3.1"),
        (10.0, "10"),
    ],
)
def test_numbers_have_at_most_two_decimals_and_never_minus_zero(value: float, text: str) -> None:
    assert number(value) == text


def test_numbers_must_be_finite() -> None:
    with pytest.raises(ValueError, match="finite"):
        to_svg(Drawing(float("nan"), 1, ()))


def test_control_characters_are_removed_and_quotes_escaped() -> None:
    text = DrawingText.line(0, 5, 'a\x01b\tc"', 8, "000000", hover=DrawingHover("<\x0b>", 0, 9))
    svg = to_svg(
        Drawing(
            10,
            10,
            (text,),
        ),
        SvgOptions(font_family='"Odd" Font'),
    )
    assert 'xml:space="preserve">ab\tc&quot;</text>' in svg
    assert 'text-anchor="middle">&lt;&gt;</text>' in svg
    assert 'font-family="&quot;Odd&quot; Font"' in svg
    ElementTree.fromstring(svg)


@pytest.mark.parametrize("colour", ["#FF0000", "red", "FF00", 'FF0000"'])
def test_colours_must_be_rrggbb(colour: str) -> None:
    item: DrawingItem = DrawingShape(DrawingPath.rectangle(0, 0, 1, 1), colour, None, 0)
    with pytest.raises(ValueError, match="RRGGBB"):
        to_svg(Drawing(1, 1, (item,)))


def test_the_drawing_package_needs_no_extra_and_no_font_module() -> None:
    script = (
        "import sys\n"
        "for name in ('fontTools', 'resvg_py', 'reportlab', 'pikepdf', 'pdfplumber'):\n"
        "    sys.modules[name] = None\n"
        "from pta_documents.drawing import Drawing, DrawingText, to_svg\n"
        "assert not [m for m in sys.modules if m.startswith('pta_documents.design.fonts')]\n"
        "svg = to_svg(Drawing(10, 10, (DrawingText.line(0, 5, 'x', 8, '000000'),)))\n"
        "print(svg.startswith('<svg'))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True, cwd=REPO_ROOT
    )
    assert result.stdout.strip() == "True"


def test_review_page(review_dir: Path) -> None:
    """``.tmp/review/drawing.html``: bars and points with tooltips, to hover in a browser."""
    items: list[DrawingItem] = []
    values = (40.0, 75.0, 55.0, 90.0)
    for index, value in enumerate(values):
        x = 40 + index * 70
        label = f"Q{index + 1}: {value:g} Mio. €"
        items.append(
            DrawingShape(
                DrawingPath.rectangle(x, 160 - value, 40, value),
                colors.ACCENTS[index],
                None,
                0,
                kind=ShapeKind.RECTANGLE,
                hover=DrawingHover(label, x + 20, 160 - value),
            )
        )
        items.append(
            DrawingText.line(
                x + 20, 178, f"Q{index + 1}", 12, colors.TEXT_SLIDES, anchor=TextAnchor.MIDDLE
            )
        )
    points = [(40 + i * 70 + 20, 150 - v * 0.8) for i, v in enumerate(values)]
    segments = [MoveTo(*points[0]), *(LineTo(*p) for p in points[1:])]
    items.append(
        DrawingShape(DrawingPath(tuple(segments)), None, colors.SIGNAL_RED, 2, round_joins=True)
    )
    items.extend(
        DrawingHotspot(x, y, 10, dot=colors.SIGNAL_RED, hover=DrawingHover(f"Ziel {i + 1}", x, y))
        for i, (x, y) in enumerate(points)
    )
    items.append(
        DrawingText(
            10,
            20,
            (DrawingSpan("Umsatz ", bold=True), DrawingSpan("je Quartal", color=colors.PTA_BLUE)),
            14,
            colors.TEXT_SLIDES,
        )
    )
    svg = to_svg(Drawing(320, 190, tuple(items)), SvgOptions(background=colors.WHITE))
    (review_dir / "drawing.svg").write_text(svg, encoding="utf-8")
    page = (
        "<!doctype html><meta charset=utf-8><title>Zeichenmodell</title>"
        "<p>Balken und Punkte überfahren: die Tooltips erscheinen ohne Skript.</p>"
        f"{svg}"
    )
    (review_dir / "drawing.html").write_text(page, encoding="utf-8")
    assert "<script" not in page
