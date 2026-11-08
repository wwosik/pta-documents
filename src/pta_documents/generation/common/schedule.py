"""Timelines and Gantt charts: the model of ``::: timeline`` and ``::: gantt`` (E15-S01).

``::: timeline`` holds a list of dates, each with its text (``- 2026-Q2: Analyse {.done}``);
``::: gantt`` a table of tasks with start and end and an optional fourth column (who). Dates are
a year (``2026``), a month (``2026-03``), a quarter (``2026-Q2``), a day (``2026-03-15`` or
``15.03.2026``) or the word ``heute``. ``read_timeline`` and ``read_gantt`` read them from the
tokens of the container; ``layout_syntax.check`` calls them first, so every generator rejects the
same mistakes with ``Line N: …``. Drawing them is ``drawing.schedule``.
"""

from __future__ import annotations

import calendar
import datetime as dt
import itertools
import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from markdown_it.token import Token

from pta_documents.design.variants import Language
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.markdown.parser import container, line_of

MIN_ENTRIES: Final = 2
MAX_ENTRIES: Final = 8
MAX_ROWS: Final = 12
MAX_COLUMNS: Final = 24
"""The most units (weeks, months, quarters) a Gantt chart's grid has."""
TODAY_WORDS: Final = ("heute", "today")
DONE: Final = "done"
GRID_KEY: Final = "raster"
WEEK_GRID_DAYS: Final = 16 * 7
"""Up to this many days a Gantt chart has a grid of weeks, above of months."""
QUARTER_GRID_DAYS: Final = 2 * 365
"""From this many days on, a grid of quarters."""
DATE_FORMS: Final = "2026, 2026-03, 2026-Q2, 2026-03-15, 15.03.2026 or heute"

_YEAR: Final = re.compile(r"(\d{4})")
_MONTH: Final = re.compile(r"(\d{4})-(\d{1,2})")
_QUARTER: Final = re.compile(r"(\d{4})-[Qq]([1-4])")
_ISO_DAY: Final = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")
_GERMAN_DAY: Final = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
_ATTRIBUTES: Final = re.compile(r"\s*\{\s*([^{}]*?)\s*\}\s*$")
_MONTHS: Final = {
    Language.DE: (
        "Jan",
        "Feb",
        "Mär",
        "Apr",
        "Mai",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Okt",
        "Nov",
        "Dez",
    ),
    Language.EN: (
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ),
}
_WEEK: Final = {Language.DE: "KW", Language.EN: "CW"}


class Grid(StrEnum):
    """The unit of a Gantt chart's columns (``::: gantt raster=…``)."""

    WEEK = "woche"
    MONTH = "monat"
    QUARTER = "quartal"


GRIDS: Final = ", ".join(grid.value for grid in Grid)
_COARSER: Final = {Grid.WEEK: Grid.MONTH, Grid.MONTH: Grid.QUARTER}


@dataclass(frozen=True)
class DateSpan:
    """The days a date names, both included: one day, a month, a quarter or a year."""

    start: dt.date
    end: dt.date


@dataclass(frozen=True)
class TimelineEntry:
    when: DateSpan
    label: str
    """The date as written (``2026-Q2``), shown above the line."""
    text: str
    done: bool
    """``{.done}`` at the end of the entry."""
    line: int | None = None

    def is_past(self, today: dt.date) -> bool:
        """Done, or over before ``today``: drawn in grey."""
        return self.done or self.when.end < today


@dataclass(frozen=True)
class Timeline:
    entries: tuple[TimelineEntry, ...]
    today: dt.date
    """What counts as today (the front matter ``datum``, else the day of generating)."""

    @property
    def alt(self) -> str:
        """The entries as one line, the alternative text of the drawing."""
        return "; ".join(f"{e.label}: {e.text}" for e in self.entries)


@dataclass(frozen=True)
class Unit:
    """A column of a Gantt chart: a week, month or quarter, with its heading (``KW 03``)."""

    start: dt.date
    end: dt.date
    label: str

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


@dataclass(frozen=True)
class GanttRow:
    name: str
    start: dt.date
    end: dt.date
    """The last day, included."""
    owner: str | None = None
    """The fourth column (who), if the table has one."""
    line: int | None = None

    @property
    def is_milestone(self) -> bool:
        """Start and end on the same day: a diamond instead of a bar."""
        return self.start == self.end


@dataclass(frozen=True)
class Gantt:
    rows: tuple[GanttRow, ...]
    grid: Grid
    units: tuple[Unit, ...]
    today: dt.date
    name_heading: str
    """The heading of the first column (``Vorgang``)."""
    owner_heading: str | None = None
    """The heading of the fourth column (``Wer``); None: the table has three."""

    def is_secondary(self, row: GanttRow) -> bool:
        """Whether the row's owner is not the first row's: drawn in light blue."""
        first = self.rows[0].owner
        return row.owner is not None and first is not None and row.owner != first

    def offset(self, day: dt.date) -> float:
        """Where ``day`` starts on the grid, in units from its start (clamped to the grid)."""
        if day <= self.units[0].start:
            return 0.0
        for n, unit in enumerate(self.units):
            if unit.start <= day <= unit.end:
                return n + (day - unit.start).days / unit.days
        return float(len(self.units))

    def offset_after(self, day: dt.date) -> float:
        """Where ``day`` ends on the grid, in units."""
        return (
            self.offset(day + dt.timedelta(days=1)) if day < self.units[-1].end else len(self.units)
        )

    def covers(self, row: GanttRow, unit: Unit) -> bool:
        """Whether the row runs in ``unit`` (its column is shaded in Word)."""
        return row.start <= unit.end and row.end >= unit.start

    @property
    def today_unit(self) -> int | None:
        """The column of today; None: today is not on the grid."""
        return next((n for n, u in enumerate(self.units) if u.start <= self.today <= u.end), None)

    @property
    def alt(self) -> str:
        return "; ".join(
            f"{r.name}: {r.start:%d.%m.%Y}–{r.end:%d.%m.%Y}" + (f" ({r.owner})" if r.owner else "")
            for r in self.rows
        )


Schedule = Timeline | Gantt


# ---------------------------------------------------------------------- dates


def parse_date(text: str, today: dt.date) -> DateSpan | None:
    """The days ``text`` names (see the module); None when it names none."""
    text = text.replace(" ", " ").strip()
    if text.lower() in TODAY_WORDS:
        return DateSpan(today, today)
    try:
        if match := _YEAR.fullmatch(text):
            year = int(match.group(1))
            return DateSpan(dt.date(year, 1, 1), dt.date(year, 12, 31))
        if match := _QUARTER.fullmatch(text):
            year, quarter = int(match.group(1)), int(match.group(2))
            return _months(year, quarter * 3 - 2, 3)
        if match := _MONTH.fullmatch(text):
            return _months(int(match.group(1)), int(match.group(2)), 1)
        if match := _ISO_DAY.fullmatch(text):
            day = dt.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            return DateSpan(day, day)
        if match := _GERMAN_DAY.fullmatch(text):
            day = dt.date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
            return DateSpan(day, day)
    except ValueError:
        return None
    return None


def _months(year: int, first: int, count: int) -> DateSpan:
    """``count`` months from month ``first`` of ``year``; raises ``ValueError`` for no month."""
    last = first + count - 1
    if not 1 <= first <= last <= 12:
        raise ValueError(f"no month {first}")
    return DateSpan(
        dt.date(year, first, 1), dt.date(year, last, calendar.monthrange(year, last)[1])
    )


def _date(text: str, today: dt.date, format: DocumentFormat, line: int | None) -> DateSpan:
    span = parse_date(text, today)
    if span is None:
        raise _error(format, line, f"'{text.strip()}' is no date. Write a date as {DATE_FORMS}.")
    return span


# ---------------------------------------------------------------------- the grid


def grid_for(start: dt.date, end: dt.date) -> Grid:
    """The grid for the days ``start`` to ``end``: weeks up to 16 weeks, quarters from two
    years on, months between."""
    days = (end - start).days + 1
    if days >= QUARTER_GRID_DAYS:
        return Grid.QUARTER
    if days > WEEK_GRID_DAYS:
        return Grid.MONTH
    return Grid.WEEK


def units(grid: Grid, start: dt.date, end: dt.date, language: Language) -> tuple[Unit, ...]:
    """The columns from the unit holding ``start`` to the one holding ``end`` (rounded to whole
    weeks from Monday, months, quarters); months and quarters name their year at the first column
    and at each new year (``Jan 27``)."""
    months = _MONTHS[language]
    result: list[Unit] = []
    match grid:
        case Grid.WEEK:
            day = start - dt.timedelta(days=start.weekday())
            while day <= end:
                week = day.isocalendar().week
                result.append(
                    Unit(day, day + dt.timedelta(days=6), f"{_WEEK[language]} {week:02d}")
                )
                day += dt.timedelta(days=7)
        case Grid.MONTH:
            year, month = start.year, start.month
            while dt.date(year, month, 1) <= end:
                span = _months(year, month, 1)
                label = months[month - 1]
                if not result or month == 1:
                    label += f" {year % 100:02d}"
                result.append(Unit(span.start, span.end, label))
                year, month = (year + 1, 1) if month == 12 else (year, month + 1)
        case Grid.QUARTER:
            year, quarter = start.year, (start.month - 1) // 3 + 1
            while dt.date(year, quarter * 3 - 2, 1) <= end:
                span = _months(year, quarter * 3 - 2, 3)
                result.append(Unit(span.start, span.end, f"Q{quarter} {year % 100:02d}"))
                year, quarter = (year + 1, 1) if quarter == 4 else (year, quarter + 1)
    return tuple(result)


def grid_argument(arguments: str, format: DocumentFormat) -> Grid | None:
    """The grid ``::: gantt raster=monat`` asks for; None without arguments; raises for any
    other argument."""
    if not arguments:
        return None
    key, equals, value = arguments.partition("=")
    if equals and key.strip() == GRID_KEY:
        for grid in Grid:
            if grid.value == value.strip().lower():
                return grid
    raise DocumentConversionError(
        format,
        f"The container '::: gantt {arguments}' takes {GRID_KEY}=… with one of: {GRIDS} "
        f"(such as '::: gantt {GRID_KEY}={Grid.MONTH.value}').",
    )


# ---------------------------------------------------------------------- reading


def read_timeline(
    tokens: Sequence[Token],
    i: int,
    format: DocumentFormat,
    line_offset: int,
    today: dt.date,
) -> Timeline:
    """The timeline of the ``::: timeline`` at ``tokens[i]``: one list of 2 to 8 entries
    ``date: text``, dates in order, ``{.done}`` at the end of an entry marks it done."""
    start_line = line_of(tokens[i], line_offset)
    kids = _children(tokens, i)
    lists = ("bullet_list_open", "ordered_list_open")
    if len(kids) != 1 or tokens[kids[0]].type not in lists:
        raise _error(
            format,
            start_line,
            "A '::: timeline' holds one list of dates, each with its text: '- 2026-03: Kick-off'.",
        )
    entries: list[TimelineEntry] = []
    for item in _children(tokens, kids[0]):
        line = line_of(tokens[item], line_offset)
        content = _children(tokens, item)
        if len(content) != 1 or tokens[content[0]].type != "paragraph_open":
            raise _error(
                format, line, "A timeline entry is one line: its date, a colon and its text."
            )
        entries.append(_entry(plain_text(tokens[content[0] + 1]), line, format, today))
    if not MIN_ENTRIES <= len(entries) <= MAX_ENTRIES:
        raise _error(
            format,
            start_line,
            f"A '::: timeline' has {MIN_ENTRIES} to {MAX_ENTRIES} entries, not {len(entries)}; "
            "split a longer one into two timelines.",
        )
    for before, entry in itertools.pairwise(entries):
        if entry.when.start < before.when.start:
            raise _error(
                format,
                entry.line,
                f"The timeline goes from early to late: '{entry.label}' comes before "
                f"'{before.label}'.",
            )
    return Timeline(tuple(entries), today)


def _entry(text: str, line: int | None, format: DocumentFormat, today: dt.date) -> TimelineEntry:
    label, colon, rest = text.partition(":")
    if not colon:
        raise _error(
            format, line, f"A timeline entry starts with its date and a colon: '2026-03: {text}'."
        )
    done = False
    if match := _ATTRIBUTES.search(rest):
        if match.group(1) != "." + DONE:
            raise _error(
                format,
                line,
                f"Unknown attribute '{{{match.group(1)}}}' of a timeline entry. "
                f"Valid: {{.{DONE}}}.",
            )
        done = True
        rest = rest[: match.start()]
    rest = rest.strip()
    if not rest:
        raise _error(format, line, f"The timeline entry '{label.strip()}' has no text.")
    return TimelineEntry(_date(label, today, format, line), label.strip(), rest, done, line)


def read_gantt(
    tokens: Sequence[Token],
    i: int,
    format: DocumentFormat,
    line_offset: int,
    today: dt.date,
    language: Language = Language.DE,
) -> Gantt:
    """The Gantt chart of the ``::: gantt`` at ``tokens[i]``: one table with the columns task,
    start, end and optionally a fourth (who), 1 to 12 rows, a grid of at most 24 columns."""
    start_line = line_of(tokens[i], line_offset)
    try:
        forced = grid_argument(container(tokens[i])[1], format)
    except DocumentConversionError as error:
        raise _error(format, start_line, error.reason) from None
    kids = _children(tokens, i)
    if len(kids) != 1 or tokens[kids[0]].type != "table_open":
        raise _error(
            format,
            start_line,
            "A '::: gantt' holds one table with the columns Vorgang, Start and Ende, and "
            "optionally a fourth such as Wer.",
        )
    table = _table(tokens, kids[0], line_offset)
    header, body = table[0], table[1:]
    columns = len(header[1])
    if columns not in (3, 4):
        raise _error(
            format,
            header[0],
            f"The table of a '::: gantt' has 3 or 4 columns (Vorgang, Start, Ende and optionally "
            f"Wer), not {columns}.",
        )
    if not 1 <= len(body) <= MAX_ROWS:
        raise _error(
            format,
            start_line,
            f"A '::: gantt' has 1 to {MAX_ROWS} tasks, not {len(body)}; split a longer plan "
            "into two charts, such as one per phase.",
        )
    rows: list[GanttRow] = []
    for line, cells in body:
        name, first, last = cells[0], cells[1], cells[2]
        if not name:
            raise _error(format, line, "Every task of a '::: gantt' has a name.")
        if not first or not last:
            raise _error(format, line, f"The task '{name}' needs a start and an end.")
        start = _date(first, today, format, line).start
        end = _date(last, today, format, line).end
        if end < start:
            raise _error(format, line, f"The task '{name}' ends before it starts.")
        owner = (cells[3] or None) if columns == 4 else None
        rows.append(GanttRow(name, start, end, owner, line))
    first_day = min(r.start for r in rows)
    last_day = max(r.end for r in rows)
    grid = forced or grid_for(first_day, last_day)
    grid_units = units(grid, first_day, last_day, language)
    while forced is None and len(grid_units) > MAX_COLUMNS and grid in _COARSER:
        grid = _COARSER[grid]
        grid_units = units(grid, first_day, last_day, language)
    if len(grid_units) > MAX_COLUMNS:
        coarser = _COARSER.get(grid)
        hint = (
            f"take a coarser grid ('::: gantt {GRID_KEY}={coarser.value}') or split the plan"
            if coarser is not None
            else "split the plan into two charts"
        )
        raise _error(
            format,
            start_line,
            f"The grid of the '::: gantt' has {len(grid_units)} columns ({grid.value}), "
            f"{MAX_COLUMNS} at most; {hint}.",
        )
    owner_heading = header[1][3] if columns == 4 else None
    return Gantt(tuple(rows), grid, grid_units, today, header[1][0], owner_heading)


def _table(tokens: Sequence[Token], i: int, line_offset: int) -> list[tuple[int | None, list[str]]]:
    """The rows of the table at ``tokens[i]``: their line and the plain text of their cells."""
    rows: list[tuple[int | None, list[str]]] = []
    j = i + 1
    while tokens[j].type != "table_close":
        token = tokens[j]
        if token.type == "tr_open":
            rows.append((line_of(token, line_offset), []))
        elif token.type == "inline" and rows:
            rows[-1][1].append(plain_text(token).strip())
        j += 1
    return rows


def plain_text(inline: Token) -> str:
    """The text of an inline token without its markup; line breaks are spaces."""
    parts: list[str] = []
    for child in inline.children or ():
        match child.type:
            case "text" | "code_inline":
                parts.append(child.content)
            case "softbreak" | "hardbreak":
                parts.append(" ")
            case _:
                pass
    return "".join(parts)


def _children(tokens: Sequence[Token], i: int) -> list[int]:
    """Where the child blocks of the block at ``tokens[i]`` start."""
    result: list[int] = []
    j = i + 1
    while not (tokens[j].nesting == -1 and tokens[j].level == tokens[i].level):
        result.append(j)
        j = _end(tokens, j)
    return result


def _end(tokens: Sequence[Token], i: int) -> int:
    if tokens[i].nesting != 1:
        return i + 1
    j = i + 1
    while not (tokens[j].nesting == -1 and tokens[j].level == tokens[i].level):
        j += 1
    return j + 1


def _error(format: DocumentFormat, line: int | None, reason: str) -> DocumentConversionError:
    where = f"Line {line}: " if line is not None else ""
    return DocumentConversionError(format, where + reason)


def reference_day(date: dt.date | None) -> dt.date:
    """What counts as today: the front matter ``datum`` if given, else the day of generating."""
    return date if date is not None else dt.date.today()
