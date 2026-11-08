"""The drawing model (E02-S03): port of DocLibs ``DrawingTests.cs``."""

from __future__ import annotations

from pta_documents.drawing import (
    Bounds,
    ClosePath,
    CubicTo,
    Drawing,
    DrawingHover,
    DrawingPath,
    DrawingShape,
    DrawingSpan,
    DrawingText,
    LineTo,
    MoveTo,
    ShapeKind,
    TextAnchor,
)


def make(label: str) -> Drawing:
    return Drawing(
        10,
        20,
        (
            DrawingShape(
                DrawingPath.rectangle(0, 0, 10, 20),
                "FFFFFF",
                "000000",
                1,
                dash=(2, 1),
                kind=ShapeKind.RECTANGLE,
            ),
            DrawingText.line(5, 10, label, 12, "000000", anchor=TextAnchor.MIDDLE, max_width=8),
        ),
    )


def test_drawings_compare_by_content() -> None:
    assert make("a") == make("a")
    assert hash(make("a")) == hash(make("a"))
    assert make("a") != make("b")


def test_lists_are_stored_as_tuples() -> None:
    drawing = Drawing(1, 1, [DrawingShape(DrawingPath([MoveTo(0, 0)]), None, None, 0, dash=[1])])  # type: ignore[arg-type]
    shape = drawing.items[0]
    assert isinstance(drawing.items, tuple)
    assert isinstance(shape, DrawingShape)
    assert isinstance(shape.path.segments, tuple) and shape.dash == (1,)
    assert hash(drawing)


def test_bounds_hold_every_point_control_points_too() -> None:
    path = DrawingPath((MoveTo(0, 0), CubicTo(-5, 10, 20, 10, 15, 0), ClosePath()))
    assert path.bounds == (-5.0, 0.0, 25.0, 10.0)
    assert path.bounds == Bounds(x=-5, y=0, width=25, height=10)


def test_an_empty_path_has_empty_bounds() -> None:
    assert DrawingPath(()).bounds == (0, 0, 0, 0)


def test_rectangle_is_a_closed_path() -> None:
    assert DrawingPath.rectangle(1, 2, 3, 4).segments == (
        MoveTo(1, 2),
        LineTo(4, 2),
        LineTo(4, 6),
        LineTo(1, 6),
        ClosePath(),
    )


def test_text_is_the_concatenated_spans() -> None:
    text = DrawingText(0, 0, (DrawingSpan("Bold", bold=True), DrawingSpan(" rest")), 12, "000000")
    assert text.text == "Bold rest"


def test_span_colours_take_part_in_equality() -> None:
    assert DrawingSpan("a", color="FF0000") != DrawingSpan("a")
    assert DrawingSpan("a", color="FF0000") == DrawingSpan("a", color="FF0000")


def test_fill_rule_and_hover_take_part_in_equality() -> None:
    path = DrawingPath.rectangle(0, 0, 1, 1)
    assert DrawingShape(path, "000000", None, 0) != DrawingShape(
        path, "000000", None, 0, even_odd=True
    )
    hovered = DrawingShape(path, "000000", None, 0, hover=DrawingHover("x", 0, 0))
    assert hovered != DrawingShape(path, "000000", None, 0)
