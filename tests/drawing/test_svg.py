"""E06-S03: SVG → ``Drawing`` (port of DocLibs ``SvgDrawingTests.cs``, with what mermaid-cli
writes: rules in ``<style>``, marker viewBoxes, CSS transforms, ``dominant-baseline``)."""

from __future__ import annotations

import pytest

from pta_documents.drawing import (
    DrawingShape,
    DrawingSpan,
    DrawingText,
    LineTo,
    MoveTo,
    ShapeKind,
    TextAnchor,
)
from pta_documents.drawing.model import Drawing
from pta_documents.drawing.svg import SvgDrawingError, to_drawing


def convert(content: str, css: str = "") -> Drawing:
    return to_drawing(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 120" width="200" height="120"'
        ' style="--bg:#FFFFFF;--fg:#1F2937;--surface:#E6F4F5;--border:#0E7C86">'
        f"<style>svg {{ --_text: var(--fg); --fs-s: 0.875rem; }} {css}</style>{content}</svg>"
    )


def shapes(drawing: Drawing) -> list[DrawingShape]:
    return [i for i in drawing.items if isinstance(i, DrawingShape)]


def texts(drawing: Drawing) -> list[DrawingText]:
    return [i for i in drawing.items if isinstance(i, DrawingText)]


def test_shapes_keep_their_kind_and_resolve_their_colours() -> None:
    drawing = convert(
        '<rect x="1" y="2" width="30" height="20" fill="var(--surface)" stroke="#000" />'
        '<rect x="1" y="2" width="30" height="20" rx="4" fill="#fff" />'
        '<circle cx="10" cy="10" r="5" fill="none" stroke="var(--border)" stroke-width="2"'
        ' stroke-dasharray="3 2" />'
        '<ellipse cx="10" cy="10" rx="8" ry="3" fill="#123456" />'
    )
    assert drawing.width == 200
    found = shapes(drawing)
    assert [s.kind for s in found] == [
        ShapeKind.RECTANGLE,
        ShapeKind.ROUNDED_RECTANGLE,
        ShapeKind.ELLIPSE,
        ShapeKind.ELLIPSE,
    ]
    assert (found[0].fill, found[0].stroke) == ("E6F4F5", "0" * 6)
    assert tuple(found[0].path.bounds) == (1, 2, 30, 20)
    assert found[1].corner_radius == 4
    assert found[1].stroke is None
    assert (found[2].fill, found[2].stroke, found[2].stroke_width) == (None, "0E7C86", 2)
    assert found[2].dash == (3, 2)
    assert tuple(found[3].path.bounds) == (2, 7, 16, 6)


def test_markers_are_placed_at_the_end_turned_along_the_path() -> None:
    drawing = convert(
        '<path d="M10,10 L10,50" fill="none" stroke="#000" marker-end="url(#arrow)" />'
        '<defs><marker id="arrow" markerUnits="userSpaceOnUse" refX="10" refY="6" orient="auto">'
        '<polygon points="0,1.5 10,6 0,10.5" fill="#FF0000" /></marker></defs>'
    )
    arrow = shapes(drawing)[1]
    assert arrow.fill == "FF0000"
    points = [(round(x, 6), round(y, 6)) for s in arrow.path.segments for x, y in s.points]
    assert points == [(14.5, 40), (10, 50), (5.5, 40)]  # pointing down, tip on the end


def test_a_marker_view_box_is_fitted_into_the_marker_size() -> None:
    drawing = convert(
        '<path d="M0,10 L50,10" stroke="#000" marker-end="url(#m)" />'
        '<marker id="m" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="userSpaceOnUse"'
        ' markerWidth="8" markerHeight="8" orient="auto">'
        '<path d="M 0 0 L 10 5 L 0 10 z" class="tip"/></marker>',
        css=".tip{fill:#00FF00}",
    )
    tip = shapes(drawing)[1]
    assert tip.fill == "00FF00"
    points = [(round(x, 6), round(y, 6)) for s in tip.path.segments for x, y in s.points]
    assert points == [(42, 6), (50, 10), (42, 14)]


def test_marker_start_points_along_the_first_segment() -> None:
    drawing = convert(
        '<line x1="0" y1="0" x2="20" y2="0" stroke="#000" marker-start="url(#m)" />'
        '<defs><marker id="m" markerUnits="userSpaceOnUse" refX="0" refY="0" orient="auto">'
        '<path d="M0,0 L5,0" stroke="#000" /></marker></defs>'
    )
    assert shapes(drawing)[1].path.segments == (MoveTo(0, 0), LineTo(5, 0))


def test_text_splits_into_lines_with_bold_spans_and_collapsed_whitespace() -> None:
    drawing = convert(
        '<g class="node"><rect x="0" y="0" width="116" height="60" />'
        '<text x="58" y="30" text-anchor="middle" font-size="var(--fs-s)" font-weight="500"'
        ' fill="var(--_text)"><tspan x="58" dy="-4.2"><tspan font-weight="bold">x</tspan>'
        ' &amp;   y</tspan><tspan x="58" dy="18.2">second line</tspan></text></g>'
        '<text x="5" y="100" class="mono" font-weight="600" dy="4.9">  plain  </text>'
    )
    found = texts(drawing)
    assert len(found) == 3
    assert found[0].spans == (DrawingSpan("x", True), DrawingSpan(" & y"))
    assert (found[0].x, round(found[0].baseline, 6), found[0].size) == (58, 25.8, 14)
    assert (found[0].anchor, found[0].color) == (TextAnchor.MIDDLE, "1F2937")
    assert found[0].max_width == 100
    assert (found[1].text, round(found[1].baseline, 6)) == ("second line", 44)
    assert found[2].spans == (DrawingSpan("plain", True),)
    assert found[2].mono
    assert found[2].max_width is None
    assert found[2].baseline == pytest.approx(104.9)


def test_mermaid_lines_in_em_with_a_central_baseline_and_css_colours() -> None:
    drawing = convert(
        '<g class="label"><text y="-10.1" class="t"><tspan class="row" x="0" y="-0.1em"'
        ' dy="1.1em"><tspan font-weight="">Erste</tspan></tspan><tspan class="row" x="0"'
        ' y="1em" dy="1.1em"><tspan font-weight="normal">Zweite</tspan></tspan></text></g>',
        css="#x {} .label text{fill:#404040;font-size:10px;font-weight:bold;"
        "dominant-baseline:central}",
    )
    first, second = texts(drawing)
    assert (first.text, first.color, first.size) == ("Erste", "404040", 10)
    assert first.spans[0].bold  # an empty font-weight inherits
    assert not second.spans[0].bold
    assert first.baseline == pytest.approx(-1 + 11 + 3.5)
    assert second.baseline == pytest.approx(10 + 11 + 3.5)


def test_groups_move_their_content_and_pass_on_their_paint() -> None:
    drawing = convert(
        '<g transform="translate(100 50)" fill="none" stroke="#00FF00" stroke-linejoin="round">'
        '<circle cx="0" cy="0" r="2" /></g>'
    )
    [circle] = shapes(drawing)
    assert tuple(circle.path.bounds) == (98, 48, 4, 4)
    assert (circle.fill, circle.stroke, circle.round_joins) == (None, "00FF00", True)


def test_a_css_transform_turns_about_its_origin() -> None:
    drawing = convert(
        '<rect class="milestone" x="0" y="0" width="10" height="10" transform-origin="5px 5px"'
        ' fill="#000"/>',
        css=".milestone{transform:rotate(45deg) scale(0.8,0.8)}",
    )
    [diamond] = shapes(drawing)
    assert diamond.kind is ShapeKind.PATH
    x, y, w, h = diamond.path.bounds
    assert (round(x + w / 2, 6), round(y + h / 2, 6)) == (5, 5)
    assert w == pytest.approx(8 * 2**0.5)


def test_opacity_is_mixed_with_white() -> None:
    drawing = convert('<rect width="1" height="1" fill="#0000FF" fill-opacity="0.5" />')
    assert shapes(drawing)[0].fill == "8080FF"


def test_current_color_is_the_inherited_colour() -> None:
    drawing = convert('<g style="color:#123456"><line x2="5" stroke="currentColor"/></g>')
    assert shapes(drawing)[0].stroke == "123456"


def test_a_dash_without_gaps_is_a_solid_line_and_even_odd_is_kept() -> None:
    drawing = convert(
        '<path d="M0,0 L5,0 L5,5 Z" fill="#000" fill-rule="evenodd" stroke="#000"'
        ' style="stroke-dasharray: 1, 0;"/>'
    )
    [shape] = shapes(drawing)
    assert shape.dash is None
    assert shape.even_odd


def test_filters_symbols_and_hidden_elements_are_left_out() -> None:
    drawing = convert(
        '<filter id="f"><feDropShadow dx="2"/></filter><symbol id="s"><rect width="1"'
        ' height="1"/></symbol><rect width="1" height="1" style="display:none"/>'
        '<rect width="2" height="2" filter="url(#f)"/>'
    )
    assert len(drawing.items) == 1


def test_a_percentage_width_is_the_view_box() -> None:
    drawing = to_drawing(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="4 4 50 20">'
        '<rect x="4" y="4" width="10" height="10"/></svg>'
    )
    assert (drawing.width, drawing.height) == (50, 20)
    assert tuple(shapes(drawing)[0].path.bounds) == (0, 0, 10, 10)


@pytest.mark.parametrize(
    ("content", "named"),
    [
        ('<image href="x.png" width="1" height="1" />', "<image>"),
        (
            '<foreignObject width="1" height="1"><div xmlns="http://www.w3.org/1999/xhtml">x'
            "</div></foreignObject>",
            "<foreignObject>",
        ),
        ('<use href="#s"/>', "<use>"),
        ('<rect width="1" height="1" fill="nonsense(1,2,3)" />', "nonsense(1,2,3)"),
        ('<path d="M0,0 L1,1" stroke="#000" marker-mid="url(#m)" />', "marker-mid"),
        ('<text x="0" y="0" transform="rotate(90)">x</text>', "rotated text"),
        ('<rect width="1" height="1" clip-path="url(#c)" />', "clip-path"),
        ('<text dominant-baseline="weird">x</text>', "weird"),
    ],
)
def test_what_cannot_be_drawn_raises(content: str, named: str) -> None:
    with pytest.raises(SvgDrawingError) as error:
        convert(content)
    assert named in str(error.value)


def test_doctypes_are_refused() -> None:
    with pytest.raises(SvgDrawingError):
        to_drawing(
            '<!DOCTYPE svg [<!ENTITY x "y">]><svg xmlns="http://www.w3.org/2000/svg" width="1"'
            ' height="1"/>'
        )


def test_a_root_other_than_svg_is_refused() -> None:
    with pytest.raises(SvgDrawingError, match="no <svg> root"):
        to_drawing("<html/>")


def test_comments_are_skipped_and_their_tail_is_kept() -> None:
    drawing = convert('<!-- a --><text x="1" y="2">Vor<!-- b -->her</text>')
    [text] = texts(drawing)
    assert text.text == "Vorher"
