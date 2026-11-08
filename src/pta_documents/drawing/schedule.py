"""Timelines and Gantt charts as a ``Drawing`` (E15-S01), the same for every format.

``timeline`` draws a line across the whole width with a mark per date, the date above the line
and its text below — above and below by turns when the labels of neighbours would collide — and
the years over it; ``gantt`` the task names on the left and a bar per task on a grid of weeks,
months or quarters on the right, a diamond for a milestone and a dashed line for today. Sizes are
CSS pixels (a pixel is 0.75 pt); colours come from ``design.colors``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from pta_documents.design import colors
from pta_documents.drawing.model import (
    Drawing,
    DrawingItem,
    DrawingPath,
    DrawingShape,
    DrawingText,
    LineTo,
    MoveTo,
    ShapeKind,
    TextAnchor,
)
from pta_documents.drawing.svg_geometry import ellipse
from pta_documents.drawing.svg_output import estimate_width
from pta_documents.generation.common.schedule import Gantt, Schedule, Timeline

PIXELS_PER_POINT: Final = 4 / 3


def px(points: float) -> float:
    """Points in CSS pixels."""
    return points * PIXELS_PER_POINT


@dataclass(frozen=True)
class TimelineStyle:
    """Sizes of a timeline in pixels (sizes of text in points)."""

    date_pt: float = 12
    text_pt: float = 12
    year_pt: float = 10
    line_spacing: float = 1.25
    mark: float = 14
    """The diameter of a mark."""
    axis: float = 2
    """The thickness of the line."""
    gap: float = 8
    """The least room between the labels of neighbours."""
    label_gap: float = 5
    """Between a mark and its label."""
    year_band: float = 20
    """The band over the timeline for the years."""
    tick: float = 9
    """Half the height of the tick where a new year starts."""
    max_lines: int = 3
    """Lines a text is wrapped into; more are drawn smaller (``max_width``)."""


@dataclass(frozen=True)
class GanttStyle:
    """Sizes of a Gantt chart in pixels (sizes of text in points)."""

    name_pt: float = 14
    head_pt: float = 10
    owner_pt: float = 10
    row: float = px(0.9 / 2.54 * 72)
    """A task: 0.9 cm."""
    head: float = 26
    bar_share: float = 0.6
    name_share: tuple[float, float] = (0.18, 0.35)
    """The least and most share of the width the names take."""
    pad: float = 6
    milestone: float = 18
    grid_line: float = 1
    today_line: float = 1.5
    today_dash: tuple[float, float] = (4, 3)


TIMELINE: Final = TimelineStyle()
GANTT: Final = GanttStyle()


def draw(schedule: Schedule, width: float, *, dark: bool = False) -> Drawing:
    """``schedule`` drawn ``width`` pixels wide; ``dark``: on a dark slide (text in white)."""
    match schedule:
        case Timeline():
            return timeline(schedule, width, dark=dark)
        case Gantt():
            return gantt(schedule, width, dark=dark)


# ---------------------------------------------------------------------- the timeline


def wrap(text: str, size: float, width: float, max_lines: int) -> list[str]:
    """``text`` in lines at most ``width`` pixels wide at ``size`` pixels, word by word; the
    last of ``max_lines`` lines takes what is left (it is drawn smaller, never cut)."""
    lines: list[str] = []
    for word in text.split():
        if lines and len(lines) <= max_lines:
            candidate = f"{lines[-1]} {word}"
            if estimate_width(candidate, size) <= width or len(lines) == max_lines:
                lines[-1] = candidate
                continue
        lines.append(word)
    return lines or [""]


def collides(timeline: Timeline, width: float, style: TimelineStyle = TIMELINE) -> bool:
    """Whether a label is wider than the room between its neighbours, so labels go above and
    below the line by turns."""
    room = width / len(timeline.entries) - style.gap
    for entry in timeline.entries:
        if estimate_width(entry.label, px(style.date_pt)) > room:
            return True
        if len(wrap(entry.text, px(style.text_pt), room, style.max_lines)) > style.max_lines - 1:
            return True
        if any(estimate_width(word, px(style.text_pt)) > room for word in entry.text.split()):
            return True
    return False


def timeline(
    timeline: Timeline, width: float, *, dark: bool = False, style: TimelineStyle = TIMELINE
) -> Drawing:
    """The timeline ``width`` pixels wide; the marks are spread evenly in the order of the
    entries."""
    entries = timeline.entries
    count = len(entries)
    slot = width / count
    xs = [slot * (n + 0.5) for n in range(count)]
    by_turns = collides(timeline, width, style)
    room = (2 * slot if by_turns else slot) - style.gap
    date_size, text_size = px(style.date_pt), px(style.text_pt)
    line_height = text_size * style.line_spacing
    texts = [wrap(e.text, text_size, room, style.max_lines) for e in entries]
    most = max(len(lines) for lines in texts)
    radius = style.mark / 2
    above_date = radius + style.label_gap + date_size * 0.25
    below_first = radius + style.label_gap + date_size * 0.95
    if by_turns:
        axis_y = style.year_band + (most + 1) * line_height + above_date
    else:
        axis_y = style.year_band + line_height + above_date
    below_lines = most if by_turns else most - 1
    height = axis_y + below_first + below_lines * line_height + style.gap
    text_color = colors.WHITE if dark else colors.TEXT_SLIDES
    current = colors.LIGHT_BLUE if dark else colors.PTA_BLUE
    items: list[DrawingItem] = [
        DrawingShape(
            DrawingPath.rectangle(0, axis_y - style.axis / 2, width, style.axis),
            colors.GREY_MID,
            None,
            0,
            kind=ShapeKind.RECTANGLE,
        )
    ]
    year_size = px(style.year_pt)
    for n, entry in enumerate(entries):
        year = entry.when.start.year
        if n > 0 and year == entries[n - 1].when.start.year:
            continue
        x = 0.0 if n == 0 else (xs[n - 1] + xs[n]) / 2
        if n > 0:
            tick = DrawingPath((MoveTo(x, axis_y - style.tick), LineTo(x, axis_y + style.tick)))
            items.append(DrawingShape(tick, None, colors.GREY_MID, style.axis))
        items.append(
            DrawingText.line(
                x + (style.gap / 2 if n > 0 else 0),
                year_size,
                str(year),
                year_size,
                colors.GREY_DARK,
                bold=True,
            )
        )
    for n, (entry, x, lines) in enumerate(zip(entries, xs, texts, strict=True)):
        past = entry.is_past(timeline.today)
        mark = colors.GREY_DARK if past else current
        items.append(
            DrawingShape(
                DrawingPath(tuple(ellipse(x, axis_y, radius, radius))),
                mark,
                None,
                0,
                kind=ShapeKind.ELLIPSE,
            )
        )
        if not by_turns:
            # The date above the line, the text below it.
            date = axis_y - above_date
            text_baselines = [axis_y + below_first + k * line_height for k in range(len(lines))]
        else:
            if n % 2 == 1:
                date = axis_y - above_date - len(lines) * line_height
            else:
                date = axis_y + below_first
            text_baselines = [date + (k + 1) * line_height for k in range(len(lines))]
        items.append(
            DrawingText.line(
                x,
                date,
                entry.label,
                date_size,
                mark,
                bold=True,
                anchor=TextAnchor.MIDDLE,
                max_width=room,
            )
        )
        for text, baseline in zip(lines, text_baselines, strict=True):
            items.append(
                DrawingText.line(
                    x,
                    baseline,
                    text,
                    text_size,
                    text_color,
                    anchor=TextAnchor.MIDDLE,
                    max_width=room,
                )
            )
    return Drawing(width, height, tuple(items))


# ---------------------------------------------------------------------- the Gantt chart


def gantt(gantt: Gantt, width: float, *, dark: bool = False, style: GanttStyle = GANTT) -> Drawing:
    """The Gantt chart ``width`` pixels wide, ``row`` high a task under a heading row."""
    name_size, head_size, owner_size = px(style.name_pt), px(style.head_pt), px(style.owner_pt)
    least, most = style.name_share
    widest = max(estimate_width(row.name, name_size) for row in gantt.rows) + 2 * style.pad
    names = min(max(widest, width * least), width * most)
    unit_width = (width - names) / len(gantt.units)
    rows_top = style.head
    height = rows_top + len(gantt.rows) * style.row + style.pad
    text_color = colors.WHITE if dark else colors.TEXT_SLIDES
    head_color = colors.GREY_MID if dark else colors.GREY_DARK

    def x_of(units: float) -> float:
        return names + units * unit_width

    items: list[DrawingItem] = []
    for n in range(len(gantt.units) + 1):
        x = x_of(n)
        line = DrawingPath((MoveTo(x, rows_top - style.pad), LineTo(x, height - style.pad)))
        items.append(DrawingShape(line, None, colors.GREY_LIGHT, style.grid_line))
    rule = DrawingPath((MoveTo(0, rows_top), LineTo(width, rows_top)))
    items.append(DrawingShape(rule, None, colors.GREY_LIGHT, style.grid_line))
    for n, unit in enumerate(gantt.units):
        items.append(
            DrawingText.line(
                x_of(n + 0.5),
                rows_top - style.pad - head_size * 0.25,
                unit.label,
                head_size,
                head_color,
                anchor=TextAnchor.MIDDLE,
                max_width=unit_width - 2,
            )
        )
    bar_height = style.row * style.bar_share
    for r, row in enumerate(gantt.rows):
        top = rows_top + r * style.row
        middle = top + style.row / 2
        items.append(
            DrawingText.line(
                0,
                middle + name_size * 0.35,
                row.name,
                name_size,
                text_color,
                max_width=names - 2 * style.pad,
            )
        )
        secondary = gantt.is_secondary(row)
        start = x_of(gantt.offset(row.start))
        if row.is_milestone:
            centre = (start + x_of(gantt.offset_after(row.end))) / 2
            half = style.milestone / 2
            diamond = DrawingPath(
                (
                    MoveTo(centre, middle - half),
                    LineTo(centre + half, middle),
                    LineTo(centre, middle + half),
                    LineTo(centre - half, middle),
                )
            )
            items.append(DrawingShape(diamond, colors.DARK_BLUE, None, 0))
            left, right, inside = centre - half, centre + half, False
        else:
            end = x_of(gantt.offset_after(row.end))
            fill = colors.LIGHT_BLUE if secondary else colors.PTA_BLUE
            bar = DrawingPath.rectangle(start, middle - bar_height / 2, end - start, bar_height)
            items.append(DrawingShape(bar, fill, None, 0, kind=ShapeKind.RECTANGLE))
            left, right = start, end
            inside = True
        if row.owner:
            items.append(
                _owner(row.owner, left, right, inside, secondary, middle, owner_size, width, dark)
            )
    today = gantt.today_unit
    if today is not None:
        x = x_of(gantt.offset(gantt.today) + 0.5 / gantt.units[today].days)
        line = DrawingPath((MoveTo(x, rows_top - style.pad), LineTo(x, height)))
        items.append(
            DrawingShape(
                line,
                None,
                colors.LIGHT_BLUE if dark else colors.DARK_BLUE,
                style.today_line,
                dash=style.today_dash,
            )
        )
    return Drawing(width, height, tuple(items))


def _owner(
    owner: str,
    left: float,
    right: float,
    inside: bool,
    secondary: bool,
    middle: float,
    size: float,
    width: float,
    dark: bool,
) -> DrawingText:
    """Who does the task: in the bar if it fits there (white, dark blue on light blue), else
    after it, else before it."""
    needed = estimate_width(owner, size) + 2 * GANTT.pad
    baseline = middle + size * 0.35
    if inside and needed <= right - left:
        color = colors.DARK_BLUE if secondary else colors.WHITE
        return DrawingText.line(left + GANTT.pad, baseline, owner, size, color)
    color = colors.WHITE if dark else colors.TEXT_SLIDES
    if right + needed <= width:
        return DrawingText.line(right + GANTT.pad, baseline, owner, size, color)
    return DrawingText.line(left - GANTT.pad, baseline, owner, size, color, anchor=TextAnchor.END)
