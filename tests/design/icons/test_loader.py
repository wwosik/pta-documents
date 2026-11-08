"""E15-S03: a bundled icon as a drawing of stroked outlines."""

from __future__ import annotations

import pytest

from pta_documents.design import icons
from pta_documents.design.icons import loader
from pta_documents.drawing.model import DrawingPath, DrawingShape, MoveTo


@pytest.mark.parametrize("name", icons.ICONS)
def test_every_icon_reads_into_outlines_on_its_grid(name: str) -> None:
    outlines = loader.outlines(name)
    assert outlines
    for outline in outlines:
        assert isinstance(outline[0], MoveTo)
        assert -0.5 <= outline[0].x <= 24.5 and -0.5 <= outline[0].y <= 24.5


def test_the_drawing_is_stroked_in_one_colour_and_scaled() -> None:
    drawing = loader.drawing("check", "006FB9", 48)
    assert (drawing.width, drawing.height) == (48, 48)
    (shape,) = drawing.items
    assert isinstance(shape, DrawingShape)
    assert shape.fill is None and shape.stroke == "006FB9"
    assert shape.stroke_width == pytest.approx(4.0)
    assert isinstance(shape.path, DrawingPath)
    first = shape.path.segments[0]
    assert first == MoveTo(10, 24)


def test_the_invisible_square_is_left_out() -> None:
    # Tabler starts every icon with <path stroke="none" d="M0 0h24v24H0z"/>.
    assert len(loader.outlines("check")) == 1
