"""E15-S02: steps as a row of chevrons — width, colours, texts."""

from __future__ import annotations

import itertools

import pytest

from pta_documents.design import colors
from pta_documents.drawing import DrawingShape, DrawingText, ShapeKind
from pta_documents.drawing import steps as drawing
from pta_documents.drawing.model import Drawing
from pta_documents.generation.common.steps import Step, Steps
from tests.drawing.test_schedule import DESIGN_COLOURS, used_colours


def chevrons(picture: Drawing) -> list[DrawingShape]:
    return [i for i in picture.items if isinstance(i, DrawingShape)]


def five(current: int | None = None, text: str = "Kurz") -> Steps:
    names = ("Analyse", "Konzept", "Umsetzung", "Abnahme", "Betrieb")
    return Steps(tuple(Step(n, text, i == current) for i, n in enumerate(names)))


def test_a_chevron_per_step_across_the_whole_width() -> None:
    picture = drawing.draw(five(), 1000)
    shapes = chevrons(picture)
    assert len(shapes) == 5
    assert shapes[0].kind is ShapeKind.HOME_PLATE
    assert {s.kind for s in shapes[1:]} == {ShapeKind.CHEVRON}
    assert shapes[0].path.bounds.x == 0
    last = shapes[-1].path.bounds
    assert abs(last.x + last.width - 1000) < 1e-6
    # Each fits into the notch of the next, a gap apart.
    for before, after in itertools.pairwise(shapes):
        b = before.path.bounds
        assert after.path.bounds.x == pytest.approx(
            b.x + b.width - before.point_depth + drawing.STEPS.gap
        )


def test_without_current_all_are_light_blue() -> None:
    assert {s.fill for s in chevrons(drawing.draw(five(), 1000))} == {colors.LIGHT_BLUE}


def test_the_current_step_is_pta_blue_and_those_before_it_grey() -> None:
    picture = drawing.draw(five(current=2), 1000)
    assert [s.fill for s in chevrons(picture)] == [
        colors.GREY_LIGHT,
        colors.GREY_LIGHT,
        colors.PTA_BLUE,
        colors.LIGHT_BLUE,
        colors.LIGHT_BLUE,
    ]
    titles = {t.text: t for t in picture.items if isinstance(t, DrawingText) and t.spans[0].bold}
    assert titles["Umsetzung"].color == colors.WHITE
    assert titles["Abnahme"].color == colors.DARK_BLUE
    assert titles["Analyse"].size == drawing.px(16)
    assert used_colours(picture) <= DESIGN_COLOURS


def test_texts_go_below_the_chevrons() -> None:
    picture = drawing.draw(five(text="Ein Satz darunter"), 1000)
    below = [t for t in picture.items if isinstance(t, DrawingText) and not t.spans[0].bold]
    assert below and all(t.baseline > drawing.STEPS.height for t in below)
    assert {t.size for t in below} == {drawing.px(12)}
    assert picture.height > drawing.STEPS.height
    assert drawing.draw(five(text=""), 1000).height == drawing.STEPS.height
    assert drawing.draw(five(text="x"), 1000, texts=False).height == drawing.STEPS.height
    dark = drawing.draw(five(text="x"), 1000, dark=True)
    assert [t.color for t in dark.items if isinstance(t, DrawingText) and not t.spans[0].bold] == [
        colors.WHITE
    ] * 5


def test_texts_fit_when_no_word_is_too_wide_and_they_take_few_lines() -> None:
    assert drawing.texts_fit(five(text="Kurz"), 600, 12)
    long = "Wort " * 40
    assert not drawing.texts_fit(five(text=long), 600, 12)
    assert not drawing.texts_fit(five(text="Donaudampfschifffahrtsgesellschaft"), 600, 12)
