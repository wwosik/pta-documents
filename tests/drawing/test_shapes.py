"""E15-S02: chevrons, home plates and pie slices — outlines and kinds."""

from __future__ import annotations

import math

import pytest

from pta_documents.drawing import ShapeKind, to_svg
from pta_documents.drawing.model import Drawing, LineTo, MoveTo
from pta_documents.drawing.shapes import chevron, pie


def test_a_chevron_points_right_with_a_notch_on_the_left() -> None:
    shape = chevron(10, 0, 100, 40, 14, None)
    assert shape.kind is ShapeKind.CHEVRON
    assert shape.point_depth == 14
    assert tuple(shape.path.bounds) == (10, 0, 100, 40)
    points = [s.points[0] for s in shape.path.segments if isinstance(s, MoveTo | LineTo)]
    assert (110, 20) in points  # the point
    assert (24, 20) in points  # the notch


def test_the_first_is_a_home_plate_with_a_straight_left_side() -> None:
    shape = chevron(0, 0, 100, 40, 14, None, first=True)
    assert shape.kind is ShapeKind.HOME_PLATE
    xs = [s.points[0][0] for s in shape.path.segments if isinstance(s, MoveTo | LineTo)]
    assert xs.count(0) == 2 and 14 not in xs


@pytest.mark.parametrize(("start", "end", "pieces"), [(270, 0, 1), (270, 90, 2), (270, 180, 3)])
def test_a_pie_runs_clockwise_in_quarter_arcs(start: float, end: float, pieces: int) -> None:
    shape = pie(50, 50, 20, start, end, None)
    assert shape.kind is ShapeKind.PIE
    assert shape.angles == (start, end)
    first, line = shape.path.segments[:2]
    assert first.points == ((50, 50),)
    assert line.points[0] == pytest.approx((50, 30))  # twelve o'clock
    last = shape.path.segments[-2].points[-1]
    angle = math.radians(end)
    assert last == pytest.approx((50 + 20 * math.cos(angle), 50 + 20 * math.sin(angle)))
    assert len(shape.path.segments) == 2 + pieces + 1


def test_svg_draws_the_new_kinds_as_paths() -> None:
    drawing = Drawing(200, 100, (chevron(0, 0, 100, 40, 14, None), pie(150, 50, 20, 270, 0, None)))
    svg = to_svg(drawing)
    assert svg.count("<path") == 2
