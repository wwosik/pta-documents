"""How much room slide content takes, and how it is shrunk or split to fit (DocLibs fitting).

Text shrinks in steps of 2 pt from the template's body size down to ``MIN_FONT_PT`` (12 pt);
what still does not fit continues on a further slide with the same title and "(Forts.)".
Tables keep their header row on every part; code splits between lines.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Final

from lxml import etree
from pptx.presentation import Presentation

from pta_documents.design import slides as design
from pta_documents.generation.common import text_metrics
from pta_documents.generation.pptx.model import Kind, Paragraph, Run, Table

A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
EMU_PER_POINT: Final = text_metrics.EMU_PER_POINT
LINE_FACTOR: Final = 1.2
SIZE_STEP: Final = 2.0
GAP: Final = design.cm(0.40)
"""Room between text, a visual and the text below it."""
CELL_INSETS: Final = 91440 * 2
CELL_PAD_Y: Final = 91440
CODE_PAD: Final = design.cm(0.30)
CODE_SIZES: Final = (design.CODE_SIZE_PT, design.MIN_FONT_PT)


@dataclass(frozen=True)
class LevelStyle:
    size_pt: float
    margin: int
    """Left margin in EMU (``marL``)."""
    space_before_pt: float


@dataclass(frozen=True)
class BodyStyle:
    """The five text levels of the master's body style, read from the template."""

    levels: tuple[LevelStyle, ...]

    @classmethod
    def read(cls, presentation: Presentation) -> BodyStyle:
        master: etree._Element = presentation.slide_masters[0]._element
        body = master.find(f"{{{P}}}txStyles/{{{P}}}bodyStyle")
        assert body is not None
        levels: list[LevelStyle] = []
        for n in range(1, 6):
            lvl = body.find(f"{{{A}}}lvl{n}pPr")
            assert lvl is not None
            run = lvl.find(f"{{{A}}}defRPr")
            space = lvl.find(f"{{{A}}}spcBef/{{{A}}}spcPts")
            levels.append(
                LevelStyle(
                    size_pt=int(run.get("sz", "1800")) / 100 if run is not None else 18.0,
                    margin=int(lvl.get("marL", "0")),
                    space_before_pt=int(space.get("val", "0")) / 100 if space is not None else 0.0,
                )
            )
        return cls(tuple(levels))

    @property
    def base_pt(self) -> float:
        return self.levels[1].size_pt

    def scales(self) -> list[float]:
        """Font scales to try, largest first: the base size in 2 pt steps down to 12 pt."""
        result: list[float] = []
        size = self.base_pt
        while size >= design.MIN_FONT_PT - 1e-9:
            result.append(size / self.base_pt)
            size -= SIZE_STEP
        return result or [1.0]


def metric_runs(runs: Sequence[Run]) -> list[text_metrics.TextRun]:
    return [r.metric() for r in runs]


def paragraph_height(style: BodyStyle, paragraph: Paragraph, scale: float, width: float) -> float:
    level = style.levels[paragraph.level]
    size = level.size_pt * scale
    bold = paragraph.kind is Kind.SUBHEADLINE
    lines = text_metrics.lines(metric_runs(paragraph.runs), size, bold, width - level.margin)
    return (lines * size * LINE_FACTOR + level.space_before_pt * scale) * EMU_PER_POINT


def text_height(
    style: BodyStyle, paragraphs: Sequence[Paragraph], scale: float, width: float
) -> float:
    if not paragraphs:
        return 0.0
    return sum(paragraph_height(style, p, scale, width) for p in paragraphs)


def text_scale(
    style: BodyStyle, paragraphs: Sequence[Paragraph], width: float, height: float
) -> float | None:
    """The largest scale at which the text fits, or None."""
    for scale in style.scales():
        if text_height(style, paragraphs, scale, width) <= height:
            return scale
    return None


def groups(paragraphs: Sequence[Paragraph]) -> list[list[Paragraph]]:
    """Paragraphs that stay together on one slide: one with the nested list items after it."""
    result: list[list[Paragraph]] = []
    for paragraph in paragraphs:
        nested = paragraph.kind in (Kind.BULLET, Kind.NUMBERED) and paragraph.depth > 0
        if result and nested:
            result[-1].append(paragraph)
        else:
            result.append([paragraph])
    return result


def pack[T](units: Sequence[list[T]], fits: Callable[[list[T]], bool]) -> list[list[T]]:
    """Units packed greedily into parts that fit; a unit too big gets a part of its own."""
    parts: list[list[T]] = []
    current: list[T] = []
    for unit in units:
        if current and not fits([*current, *unit]):
            parts.append(current)
            current = []
        current.extend(unit)
    if current:
        parts.append(current)
    return parts


# ---------------------------------------------------------------------- tables


@dataclass(frozen=True)
class TableLayout:
    header_pt: float
    row_pt: float
    widths: list[int]
    heights: list[int]
    """Row heights, the title row (if any) first."""

    @property
    def height(self) -> int:
        return sum(self.heights)


def table_steps() -> list[tuple[float, float]]:
    """(header, row) font sizes to try: the sample table's sizes in 2 pt steps down to 12 pt."""
    t = design.TABLE
    steps: list[tuple[float, float]] = []
    header, row = t.header_size_pt, t.row_size_pt
    while True:
        steps.append((max(header, design.MIN_FONT_PT), max(row, design.MIN_FONT_PT)))
        if header <= design.MIN_FONT_PT and row <= design.MIN_FONT_PT:
            break
        header -= SIZE_STEP
        row -= SIZE_STEP
    return steps


def table_layout(table: Table, width: int, header_pt: float, row_pt: float) -> TableLayout:
    t = design.TABLE
    cells = [[metric_runs(cell) for cell in row] for row in table.rows]
    widths = text_metrics.column_widths(cells, width, row_pt, CELL_INSETS, table.has_header)
    heights: list[int] = []
    if table.title:
        heights.append(t.title_height)
    for r, row in enumerate(cells):
        header = table.has_header and r == 0
        size = header_pt if header else row_pt
        lines = max(
            (
                text_metrics.lines(cell, size, header, widths[c] - CELL_INSETS)
                for c, cell in enumerate(row)
                if c < len(widths)
            ),
            default=1,
        )
        needed = int(lines * size * LINE_FACTOR * EMU_PER_POINT) + 2 * CELL_PAD_Y
        minimum = t.header_height if header else t.row_height
        heights.append(max(minimum, needed))
    return TableLayout(header_pt, row_pt, widths, heights)


def fit_table(table: Table, width: int, height: int) -> TableLayout | None:
    for header_pt, row_pt in table_steps():
        layout = table_layout(table, width, header_pt, row_pt)
        if layout.height <= height:
            return layout
    return None


def split_table(table: Table, width: int, height_first: int, height_rest: int) -> list[Table]:
    """Body rows across tables that fit at the smallest size, header (and title) repeated."""
    smallest = table_steps()[-1]
    first_row = 1 if table.has_header else 0
    rows = [[r] for r in range(first_row, len(table.rows))]
    parts: list[list[int]] = []
    current: list[int] = []
    for unit in rows:
        candidate = [*current, *unit]
        limit = height_first if not parts else height_rest
        fits = (
            table_layout(table.subset(candidate, keep_title=not parts), width, *smallest).height
            <= limit
        )
        if current and not fits:
            parts.append(current)
            current = []
        current.extend(unit)
    if current:
        parts.append(current)
    return [table.subset(part, keep_title=n == 0) for n, part in enumerate(parts)]


# ---------------------------------------------------------------------- code


def code_height(lines: int, size_pt: float) -> int:
    return int(lines * size_pt * LINE_FACTOR * EMU_PER_POINT) + 2 * CODE_PAD


def fit_code(lines: int, height: int) -> float | None:
    for size in CODE_SIZES:
        if code_height(lines, size) <= height:
            return size
    return None


def code_lines_per_slide(height: int) -> int:
    size = CODE_SIZES[-1]
    return max(1, int((height - 2 * CODE_PAD) / (size * LINE_FACTOR * EMU_PER_POINT)))


# ---------------------------------------------------------------------- flow text


def level_pt(style: BodyStyle, level: int, factor: float) -> float:
    """The size of a text level of the master at ``factor`` (body size 18 pt -> 1.0) on a flow
    slide: never below 12 pt, nor below the level's own size where that is smaller."""
    size = style.levels[level].size_pt
    return max(round(size * factor * 2) / 2, min(size, design.MIN_FONT_PT))


def flow_paragraph_height(
    style: BodyStyle, paragraph: Paragraph, factor: float, width: float
) -> float:
    level = style.levels[paragraph.level]
    size = level_pt(style, paragraph.level, factor)
    bold = paragraph.kind is Kind.SUBHEADLINE
    lines = text_metrics.lines(metric_runs(paragraph.runs), size, bold, width - level.margin)
    return (lines * size * LINE_FACTOR + level.space_before_pt * factor) * EMU_PER_POINT


def flow_text_height(
    style: BodyStyle, paragraphs: Sequence[Paragraph], factor: float, width: float
) -> int:
    """The height of paragraphs in a text box on a flow slide; the first one's space before
    does not count (PowerPoint leaves it out at the top of a box)."""
    if not paragraphs:
        return 0
    total = sum(flow_paragraph_height(style, p, factor, width) for p in paragraphs)
    first = style.levels[paragraphs[0].level].space_before_pt * factor * EMU_PER_POINT
    return int(total - first)
