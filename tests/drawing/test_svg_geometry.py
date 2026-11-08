"""E06-S03: SVG geometry (port of DocLibs ``SvgGeometryTests.cs``)."""

from __future__ import annotations

import math

import pytest

from pta_documents.drawing import ClosePath, CubicTo, LineTo, MoveTo
from pta_documents.drawing import svg_geometry as geometry
from pta_documents.drawing.svg_geometry import SvgDrawingError


def test_path_handles_absolute_and_relative_commands() -> None:
    assert geometry.path("M10,20 l5 0 H30 v10 L 0 0 z m 1 1") == [
        MoveTo(10, 20),
        LineTo(15, 20),
        LineTo(30, 20),
        LineTo(30, 30),
        LineTo(0, 0),
        ClosePath(),
        MoveTo(11, 21),
    ]


def test_implicit_pairs_after_a_move_are_lines() -> None:
    assert geometry.path("M0 0 10 0 10 10") == [MoveTo(0, 0), LineTo(10, 0), LineTo(10, 10)]


def test_a_quadratic_becomes_the_equivalent_cubic() -> None:
    assert geometry.path("M0,0 Q30,30 60,0")[1] == CubicTo(20, 20, 40, 20, 60, 0)


def test_mermaids_rounded_corners_are_quadratics() -> None:
    curve = geometry.path("M0,0L10,0Q15,0 15,5")[2]
    assert isinstance(curve, CubicTo)
    assert (curve.x, curve.y) == (15, 5)


def test_an_arc_ends_exactly_at_its_end_point_in_pieces_of_at_most_a_quarter() -> None:
    path = geometry.path("M 232 240 L 232 112 A 128 128 0 1 1 108.91 204.88 Z")
    arcs = [s for s in path if isinstance(s, CubicTo)]
    assert len(arcs) == 4  # 286°
    assert (arcs[-1].x, arcs[-1].y) == (108.91, 204.88)
    for arc in arcs:
        assert 127.99 <= math.hypot(arc.x - 232, arc.y - 240) <= 128.01


def test_a_semicircle_passes_through_the_far_side() -> None:
    arcs = [s for s in geometry.path("M0,0 A10,10 0 0 1 20,0") if isinstance(s, CubicTo)]
    assert len(arcs) == 2
    assert arcs[0].x == pytest.approx(10)
    assert arcs[0].y == pytest.approx(-10)  # sweep 1 runs clockwise on screen: over the top


def test_transforms_compose_left_to_right() -> None:
    transform = geometry.transform("translate(10 20) scale(2)")
    assert transform.apply(1, 2) == (12, 24)
    assert transform.is_axis_aligned
    assert not geometry.transform("rotate(45)").is_axis_aligned


def test_css_transforms_with_units() -> None:
    transform = geometry.transform("rotate(90deg) translate(10px, 0px)")
    x, y = transform.apply(0, 0)
    assert (round(x, 9), round(y, 9)) == (0, 10)


@pytest.mark.parametrize("value", ["skewX(10)", "translate(1 2) nonsense", "rotate(1rad)"])
def test_an_unknown_transform_raises(value: str) -> None:
    with pytest.raises(SvgDrawingError):
        geometry.transform(value)


def test_a_malformed_path_raises() -> None:
    with pytest.raises(SvgDrawingError):
        geometry.path("M 1")
