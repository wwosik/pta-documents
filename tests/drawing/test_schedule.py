"""E15-S01: timelines and Gantt charts as a ``Drawing`` — layout, collisions, colours."""

from __future__ import annotations

import datetime as dt
from typing import Final

import pytest

from pta_documents.design import colors
from pta_documents.drawing import DrawingShape, DrawingText, ShapeKind, schedule
from pta_documents.drawing.model import Drawing
from pta_documents.generation.common.schedule import Gantt, Timeline
from tests.generation.common.test_schedule import GANTT, TODAY, gantt, table, timeline

DESIGN_COLOURS: Final = {
    value for name, value in vars(colors).items() if name.isupper() and isinstance(value, str)
}


def used_colours(drawing: Drawing) -> set[str]:
    found: set[str] = set()
    for item in drawing.items:
        match item:
            case DrawingShape():
                found |= {c for c in (item.fill, item.stroke) if c is not None}
            case DrawingText():
                found.add(item.color)
                found |= {s.color for s in item.spans if s.color is not None}
            case _:
                pass
    return found


def texts(drawing: Drawing) -> list[DrawingText]:
    return [item for item in drawing.items if isinstance(item, DrawingText)]


def marks(drawing: Drawing) -> list[DrawingShape]:
    return [
        item
        for item in drawing.items
        if isinstance(item, DrawingShape) and item.kind is ShapeKind.ELLIPSE
    ]


def test_a_timeline_has_a_mark_per_entry_grey_when_done_or_past() -> None:
    drawing = schedule.timeline(timeline(), 1179)
    assert drawing.width == 1179
    assert [m.fill for m in marks(drawing)] == [
        colors.GREY_DARK,
        colors.GREY_DARK,
        colors.PTA_BLUE,
        colors.PTA_BLUE,
    ]
    centres = [m.path.bounds.x + m.path.bounds.width / 2 for m in marks(drawing)]
    assert centres == [1179 / 8 * n for n in (1, 3, 5, 7)]
    axis = drawing.items[0]
    assert isinstance(axis, DrawingShape) and axis.fill == colors.GREY_MID
    assert axis.path.bounds.width == 1179 and axis.path.bounds.height == 2


def test_without_collisions_dates_are_above_and_texts_below_the_line() -> None:
    drawing = schedule.timeline(timeline(), 1179)
    axis = marks(drawing)[0].path.bounds
    axis_y = axis.y + axis.height / 2
    dates = [t for t in texts(drawing) if t.spans[0].bold and t.text.startswith(("20", "15."))]
    labels = [t for t in dates if t.size == 16]
    assert len(labels) == 4 and all(t.baseline < axis_y for t in labels)
    assert all(t.size == 16 for t in labels)
    body = [t for t in texts(drawing) if not t.spans[0].bold]
    assert [t.text for t in body] == ["Kick-off", "Analyse abgeschlossen", "Go-live", "Betrieb"]
    assert all(t.baseline > axis_y and t.color == colors.TEXT_SLIDES for t in body)
    assert not schedule.collides(timeline(), 1179)


def test_colliding_labels_go_above_and_below_by_turns() -> None:
    crowded = timeline(
        "::: timeline\n"
        + "".join(f"- 2026-0{n}: Ein recht langer Text für den Termin {n}\n" for n in range(1, 9))
        + ":::\n"
    )
    assert schedule.collides(crowded, 605)
    drawing = schedule.timeline(crowded, 605)
    axis = marks(drawing)[0].path.bounds
    axis_y = axis.y + axis.height / 2
    dates = [t for t in texts(drawing) if t.text.startswith("2026-0")]
    assert [t.baseline < axis_y for t in dates] == [False, True] * 4
    # Labels by turns have the room of two slots.
    assert {t.max_width for t in dates} == {2 * 605 / 8 - 8}
    assert all(t.size >= 10 * 4 / 3 - 1e-9 for t in texts(drawing))


def test_years_mark_where_they_start() -> None:
    drawing = schedule.timeline(timeline(), 1179)
    years = [
        t for t in texts(drawing) if t.text in ("2026", "2027") and t.color == colors.GREY_DARK
    ]
    assert [(t.text, t.x) for t in years] == [("2026", 0), ("2027", 1179 / 8 * 6 + 4)]


def test_wrap_breaks_at_words_and_never_drops_any() -> None:
    lines = schedule.wrap("eins zwei drei vier fünf sechs", 16, 80, 2)
    assert len(lines) == 2 and " ".join(lines) == "eins zwei drei vier fünf sechs"
    assert schedule.wrap("", 16, 80, 3) == [""]


def test_a_gantt_chart_draws_bars_a_milestone_and_today() -> None:
    read: Gantt = gantt()
    drawing = schedule.gantt(read, 1179)
    bars = [
        i for i in drawing.items if isinstance(i, DrawingShape) and i.kind is ShapeKind.RECTANGLE
    ]
    assert [b.fill for b in bars] == [colors.PTA_BLUE, colors.PTA_BLUE, colors.LIGHT_BLUE]
    row = schedule.GANTT.row
    assert {round(b.path.bounds.height, 3) for b in bars} == {round(row * 0.6, 3)}
    diamonds = [
        i for i in drawing.items if isinstance(i, DrawingShape) and i.fill == colors.DARK_BLUE
    ]
    assert len(diamonds) == 1
    today = [i for i in drawing.items if isinstance(i, DrawingShape) and i.dash is not None]
    assert len(today) == 1 and today[0].stroke == colors.DARK_BLUE
    assert drawing.height == schedule.GANTT.head + 4 * row + schedule.GANTT.pad
    names = [t for t in texts(drawing) if t.x == 0]
    assert [t.text for t in names] == ["Analyse", "Umsetzung", "Abnahme", "Go-live"]
    assert all(t.size == pytest.approx(14 * 4 / 3) for t in names)
    heads = [t for t in texts(drawing) if t.color == colors.GREY_DARK]
    assert [t.text for t in heads] == ["Jan 26", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul"]
    owners = {t.text: t.color for t in texts(drawing) if t.text in ("PTA", "Kunde")}
    assert owners == {"PTA": colors.WHITE, "Kunde": colors.DARK_BLUE}


def test_bars_sit_at_their_dates() -> None:
    read = gantt(table([("A", "2026-01-01", "2026-01-31"), ("B", "2026-02", "2026-02")]))
    drawing = schedule.gantt(read, 1000)
    bars = [
        i for i in drawing.items if isinstance(i, DrawingShape) and i.kind is ShapeKind.RECTANGLE
    ]
    first, second = (b.path.bounds for b in bars)
    assert first.x + first.width == second.x


def test_no_today_line_when_today_is_off_the_grid() -> None:
    read = gantt(table([("A", "2027-01", "2027-02")]))
    drawing = schedule.gantt(read, 1000)
    assert not [i for i in drawing.items if isinstance(i, DrawingShape) and i.dash is not None]


def test_an_owner_that_does_not_fit_in_its_bar_stands_beside_it() -> None:
    markdown = GANTT.replace(
        "| Abnahme   | 2026-07-01 | 2026-07-15 | Kunde  |",
        "| Abnahme | 2026-07-01 | 2026-07-02 | Kunde |",
    )
    drawing = schedule.gantt(gantt(markdown), 1179)
    owner = next(t for t in texts(drawing) if t.text == "Kunde")
    assert owner.color == colors.TEXT_SLIDES


def test_dark_slides_draw_text_in_white() -> None:
    drawing = schedule.draw(timeline(), 1179, dark=True)
    assert colors.TEXT_SLIDES not in used_colours(drawing)
    assert colors.WHITE in used_colours(drawing)


def test_every_colour_comes_from_the_design() -> None:
    read: Timeline = timeline()
    for drawing in (schedule.draw(read, 605), schedule.draw(gantt(), 605, dark=True)):
        assert used_colours(drawing) <= DESIGN_COLOURS
    assert dt.date(2026, 3, 15) == TODAY
