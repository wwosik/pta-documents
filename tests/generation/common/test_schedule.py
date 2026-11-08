"""E15-S01: the model of ``::: timeline`` and ``::: gantt`` — dates, grids, mistakes."""

from __future__ import annotations

import datetime as dt
from typing import Final

import pytest

from pta_documents.design.variants import Language
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import layout_syntax, schedule
from pta_documents.generation.common.schedule import DateSpan, Grid
from pta_documents.markdown.parser import CONTAINER_OPEN, parse

TODAY: Final = dt.date(2026, 3, 15)
DOCX: Final = DocumentFormat.DOCX
TIMELINE: Final = """::: timeline
- 2026-01: Kick-off
- 2026-Q2: Analyse abgeschlossen {.done}
- 15.09.2026: Go-live
- 2027: Betrieb
:::
"""
GANTT: Final = """::: gantt
| Vorgang   | Start      | Ende       | Wer    |
| --------- | ---------- | ---------- | ------ |
| Analyse   | 2026-01-12 | 2026-02-27 | PTA    |
| Umsetzung | 2026-03-02 | 2026-06-30 | PTA    |
| Abnahme   | 2026-07-01 | 2026-07-15 | Kunde  |
| Go-live   | 2026-07-20 | 2026-07-20 |        |
:::
"""


def timeline(markdown: str = TIMELINE) -> schedule.Timeline:
    tokens = parse(markdown)
    return schedule.read_timeline(tokens, _first(markdown), DOCX, 0, TODAY)


def gantt(markdown: str = GANTT, language: Language = Language.DE) -> schedule.Gantt:
    tokens = parse(markdown)
    return schedule.read_gantt(tokens, _first(markdown), DOCX, 0, TODAY, language)


def _first(markdown: str) -> int:
    return next(i for i, t in enumerate(parse(markdown)) if t.type == CONTAINER_OPEN)


def table(rows: list[tuple[str, str, str]], arguments: str = "") -> str:
    lines = [f"::: gantt {arguments}".rstrip(), "| Vorgang | Start | Ende |", "| - | - | - |"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    return "\n".join([*lines, ":::", ""])


@pytest.mark.parametrize(
    ("text", "start", "end"),
    [
        ("2026", dt.date(2026, 1, 1), dt.date(2026, 12, 31)),
        ("2026-02", dt.date(2026, 2, 1), dt.date(2026, 2, 28)),
        ("2026-Q2", dt.date(2026, 4, 1), dt.date(2026, 6, 30)),
        ("2026-q4", dt.date(2026, 10, 1), dt.date(2026, 12, 31)),
        ("2026-03-05", dt.date(2026, 3, 5), dt.date(2026, 3, 5)),
        ("05.03.2026", dt.date(2026, 3, 5), dt.date(2026, 3, 5)),
        ("heute", TODAY, TODAY),
        (" Heute ", TODAY, TODAY),
    ],
)
def test_dates_name_a_year_month_quarter_or_day(text: str, start: dt.date, end: dt.date) -> None:
    assert schedule.parse_date(text, TODAY) == DateSpan(start, end)


@pytest.mark.parametrize(
    "text", ["", "26", "2026-13", "2026-Q5", "2026-02-30", "31.04.2026", "März 2026", "morgen"]
)
def test_other_text_is_no_date(text: str) -> None:
    assert schedule.parse_date(text, TODAY) is None


def test_a_timeline_reads_its_entries() -> None:
    read = timeline()
    assert [(e.label, e.text, e.done) for e in read.entries] == [
        ("2026-01", "Kick-off", False),
        ("2026-Q2", "Analyse abgeschlossen", True),
        ("15.09.2026", "Go-live", False),
        ("2027", "Betrieb", False),
    ]
    assert [e.line for e in read.entries] == [2, 3, 4, 5]
    assert [e.is_past(TODAY) for e in read.entries] == [True, True, False, False]


def test_markup_in_an_entry_is_left_out_of_its_text() -> None:
    read = timeline("::: timeline\n- **2026-01**: Start mit `code`\n- 2026-02: *Ende*\n:::\n")
    assert [(e.label, e.text) for e in read.entries] == [
        ("2026-01", "Start mit code"),
        ("2026-02", "Ende"),
    ]


@pytest.mark.parametrize(
    ("grid_start", "grid_end", "grid"),
    [
        (dt.date(2026, 1, 1), dt.date(2026, 4, 22), Grid.WEEK),  # 16 weeks
        (dt.date(2026, 1, 1), dt.date(2026, 4, 23), Grid.MONTH),
        (dt.date(2026, 1, 1), dt.date(2027, 12, 30), Grid.MONTH),
        (dt.date(2026, 1, 1), dt.date(2027, 12, 31), Grid.QUARTER),  # two years
    ],
)
def test_the_grid_follows_the_length(grid_start: dt.date, grid_end: dt.date, grid: Grid) -> None:
    assert schedule.grid_for(grid_start, grid_end) == grid


def test_a_gantt_chart_reads_its_rows_and_rounds_its_grid_to_whole_units() -> None:
    read = gantt()
    assert read.grid is Grid.MONTH
    assert [u.label for u in read.units] == ["Jan 26", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul"]
    assert (read.units[0].start, read.units[-1].end) == (dt.date(2026, 1, 1), dt.date(2026, 7, 31))
    assert (read.name_heading, read.owner_heading) == ("Vorgang", "Wer")
    assert [r.owner for r in read.rows] == ["PTA", "PTA", "Kunde", None]
    assert [read.is_secondary(r) for r in read.rows] == [False, False, True, False]
    assert [r.is_milestone for r in read.rows] == [False, False, False, True]
    assert read.today_unit == 2
    assert [read.covers(read.rows[0], u) for u in read.units] == [True, True] + [False] * 5


def test_weeks_are_calendar_weeks_from_monday() -> None:
    read = gantt(table([("A", "2026-01-07", "2026-01-20")]))
    assert read.grid is Grid.WEEK
    assert [u.label for u in read.units] == ["KW 02", "KW 03", "KW 04"]
    assert read.units[0].start == dt.date(2026, 1, 5)
    assert [
        u.label for u in gantt(table([("A", "2026-01-07", "2026-01-08")]), Language.EN).units
    ] == ["CW 02"]


def test_quarters_and_a_forced_grid() -> None:
    read = gantt(table([("A", "2026-02", "2028-01")]))
    assert read.grid is Grid.QUARTER
    assert read.units[0].label == "Q1 26" and read.units[-1].label == "Q1 28"
    forced = gantt(table([("A", "2026-02", "2026-03")], "raster=woche"))
    assert forced.grid is Grid.WEEK


def test_an_automatic_grid_wider_than_24_columns_takes_the_coarser_unit() -> None:
    # 25 months, less than two years.
    read = gantt(table([("A", "2026-01-31", "2028-01-01")]))
    assert read.grid is Grid.QUARTER


def test_offsets_place_days_within_their_unit() -> None:
    read = gantt(table([("A", "2026-01-01", "2026-02-28")], "raster=monat"))
    assert read.offset(dt.date(2026, 1, 1)) == 0
    assert read.offset(dt.date(2026, 2, 15)) == pytest.approx(1.5)
    assert read.offset_after(dt.date(2026, 1, 31)) == 1
    assert read.offset_after(dt.date(2026, 2, 28)) == 2


@pytest.mark.parametrize(
    ("markdown", "message"),
    [
        ("::: timeline\n- 2026-01: A\n:::\n", "Line 1: A '::: timeline' has 2 to 8 entries, not 1"),
        (
            "::: timeline\n" + "".join(f"- 2026-0{n}: A\n" for n in range(1, 10)) + ":::\n",
            "has 2 to 8 entries, not 9; split",
        ),
        ("::: timeline\n- 2026-01: A\n- Mai 2026: B\n:::\n", "Line 3: 'Mai 2026' is no date."),
        ("::: timeline\n- 2026-01: A\n- B\n:::\n", "Line 3: A timeline entry starts with its date"),
        (
            "::: timeline\n- 2026-01: A\n- 2026-02:\n:::\n",
            "Line 3: The timeline entry '2026-02' has no",
        ),
        ("::: timeline\n- 2026-03: A\n- 2026-02: B\n:::\n", "Line 3: The timeline goes from early"),
        (
            "::: timeline\n- 2026-01: A {.x}\n- 2026-02: B\n:::\n",
            "Line 2: Unknown attribute '{.x}'",
        ),
        ("::: timeline\nText\n:::\n", "Line 1: A '::: timeline' holds one list"),
        (
            "::: timeline\n- 2026-01: A\n\n  mehr\n- 2026-02: B\n:::\n",
            "Line 2: A timeline entry is one",
        ),
        (table([("A", "2026-01", "Q2")]), "Line 4: 'Q2' is no date."),
        (table([("A", "2026-03", "2026-01")]), "Line 4: The task 'A' ends before it starts."),
        (table([("", "2026-01", "2026-02")]), "Line 4: Every task of a '::: gantt' has a name."),
        (table([("A", "", "2026-02")]), "Line 4: The task 'A' needs a start and an end."),
        (
            table([("A", "2026-01", "2026-02")] * 13),
            "Line 1: A '::: gantt' has 1 to 12 tasks, not 13",
        ),
        (
            "::: gantt\n| A | B |\n| - | - |\n| x | y |\n:::\n",
            "Line 2: The table of a '::: gantt' has 3 or 4",
        ),
        ("::: gantt\n- 2026: A\n:::\n", "Line 1: A '::: gantt' holds one table"),
        (
            table([("A", "2026-01", "2026-02")], "raster=tag"),
            "Line 1: The container '::: gantt raster=tag'",
        ),
        (
            table([("A", "2026-01", "2026-12")], "raster=woche"),
            "53 columns (woche), 24 at most; take a coarser grid ('::: gantt raster=monat')",
        ),
        (
            table([("A", "2020", "2027")], "raster=quartal"),
            "32 columns (quartal), 24 at most; split the plan",
        ),
    ],
)
def test_mistakes_name_their_line(markdown: str, message: str) -> None:
    for format in (DocumentFormat.DOCX, DocumentFormat.PPTX):
        with pytest.raises(DocumentConversionError) as error:
            layout_syntax.check(parse(markdown), format, 0, TODAY)
        assert message in error.value.reason
        assert error.value.format is format


def test_the_check_takes_the_front_matter_lines_into_account() -> None:
    with pytest.raises(DocumentConversionError, match="Line 13: 'x' is no date"):
        layout_syntax.check(parse("::: timeline\n- 2026: A\n- x: B\n:::\n"), DOCX, 10, TODAY)


def test_today_is_the_front_matter_date_or_the_day_of_generating() -> None:
    assert schedule.reference_day(TODAY) == TODAY
    assert schedule.reference_day(None) == dt.date.today()
