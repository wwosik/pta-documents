"""A ``SummaryTable`` (port of DocLibs ``SummaryTableDrawing.cs``).

No plot and no axis: a header band and a grid of figures, right-aligned so a column reads down
as one comparison. The only colour is the verdict of the comparison rows.
"""

from __future__ import annotations

from enum import Enum
from typing import Final

from pta_documents.charts.financial import canvas as rules
from pta_documents.charts.financial.canvas import Canvas
from pta_documents.charts.financial.model import SummaryBlock, SummaryCell, SummaryTable
from pta_documents.drawing.model import Drawing, TextAnchor

PADDING_LEFT: Final = 20.0
PADDING_RIGHT: Final = 20.0
LABEL_WIDTH: Final = 170.0
COLUMN_WIDTH: Final = 88.0
CELL_PADDING: Final = 10.0
TOTAL_GAP: Final = 24.0
"""What separates the total from the columns it totals."""
BLOCK_GAP: Final = 18.0
HEADER_TOP: Final = 62.0
HEADER_HEIGHT: Final = 24.0
BLOCK_LABEL_HEIGHT: Final = 22.0
ROW_HEIGHT: Final = 22.0
NONE: Final = "–"
"""What a cell without a figure shows."""


class _Row(Enum):
    VALUE = 0
    CHANGE = 1
    GAP = 2
    RATE = 3
    PREVIOUS_RATE = 4
    RATE_POINTS = 5
    RATE_GAP = 6


def draw(table: SummaryTable, canvas: Canvas) -> Drawing:
    colors = canvas.colors
    labels = canvas.labels
    words = canvas.words
    definition = table.columns
    if not definition:
        raise ValueError("A summary table needs at least one column.")
    for block in table.blocks:
        if len(block.cells) != len(definition):
            raise ValueError(
                f"The block '{block.metric}' has {len(block.cells)} cells for {len(definition)} "
                "columns."
            )

    # What the value row draws as 0,0: half of the last digit it prints.
    rounds_to_zero = canvas.scale_factor * 0.05

    def nothing(cell: SummaryCell) -> bool:
        return abs(cell.current) < rounds_to_zero and abs(cell.previous) < rounds_to_zero

    def silent(block: SummaryBlock, column: int) -> bool:
        """Whether a cell states no rates or differences: it rounds to nothing, or it is a
        rest too small to be a proportion of its total."""
        if nothing(block.cells[column]):
            return True
        if not definition[column].rest:
            return False
        total = next(
            (abs(block.cells[i].current) for i, c in enumerate(definition) if c.total), 0.0
        )
        return total > 0 and abs(block.cells[column].current) < total * canvas.options.rest_share

    # The rest column only when it holds something; every other column whatever it holds.
    drawn = [
        i
        for i, column in enumerate(definition)
        if not column.rest or any(not nothing(b.cells[i]) for b in table.blocks)
    ]
    columns = [definition[i] for i in drawn]
    lefts: list[float] = []
    x = PADDING_LEFT + LABEL_WIDTH
    for column in columns:
        lefts.append(x)
        x += COLUMN_WIDTH + (TOTAL_GAP if column.total else 0)
    canvas.width = lefts[-1] + COLUMN_WIDTH + PADDING_RIGHT
    width = canvas.width

    def right(column: int) -> float:
        return lefts[column] + COLUMN_WIDTH - CELL_PADDING

    unit = f" ({canvas.options.unit})" if canvas.options.unit else ""

    def rows_of(block: SummaryBlock) -> list[tuple[_Row, str]]:
        versus_previous = f"{words.versus} {labels.previous}"
        if block.rate_of is None:
            gap = f"{words.versus} {labels.reference} ({canvas.signed_percent(block.reference)})"
            return [
                (_Row.VALUE, labels.value + unit),
                (_Row.CHANGE, versus_previous),
                (_Row.GAP, gap),
            ]
        # The reference is points on the share, so the label says so.
        gap = f"{words.versus} {labels.reference} ({canvas.signed_points(block.reference)})"
        return [
            (_Row.VALUE, labels.value + unit),
            (_Row.RATE, rules.fill(words.percent_of, labels.current, block.rate_of)),
            (_Row.PREVIOUS_RATE, rules.fill(words.percent_of, labels.previous, block.rate_of)),
            (_Row.RATE_POINTS, versus_previous),
            (_Row.RATE_GAP, gap),
        ]

    rows = [rows_of(block) for block in table.blocks]
    heights = [BLOCK_LABEL_HEIGHT + len(r) * ROW_HEIGHT for r in rows]
    height = (
        HEADER_TOP + HEADER_HEIGHT + sum(heights) + max(0, len(table.blocks) - 1) * BLOCK_GAP + 18
    )

    subtitle = rules.fill(words.year_to_date, labels.previous, labels.reference)
    canvas.heading(table, subtitle, PADDING_LEFT, 43)

    # The total column takes the darker header.
    for i, column in enumerate(columns):
        fill = colors.total_header if column.total else colors.table_header
        canvas.rect(lefts[i], HEADER_TOP, COLUMN_WIDTH, HEADER_HEIGHT, fill, None, 0)
        canvas.text(
            right(i),
            HEADER_TOP + 16,
            column.label,
            10,
            colors.header_text,
            TextAnchor.END,
            True,
            COLUMN_WIDTH - 2 * CELL_PADDING,
        )

    def level(share: float | None) -> tuple[str, str]:
        return (canvas.rate(share), colors.text) if share is not None else (NONE, colors.muted)

    def points(share: float | None, against: float | None) -> tuple[str, str]:
        if share is None or against is None:
            return NONE, colors.muted
        return canvas.signed_points(share - against), canvas.verdict(share, against)

    block_top = HEADER_TOP + HEADER_HEIGHT
    for b, block in enumerate(table.blocks):
        rows_top = block_top + BLOCK_LABEL_HEIGHT
        block_rows = rows[b]
        for i, column in enumerate(columns):
            if column.total:
                canvas.rect(
                    lefts[i],
                    rows_top,
                    COLUMN_WIDTH,
                    len(block_rows) * ROW_HEIGHT,
                    colors.total_fill,
                    None,
                    0,
                )
        canvas.text(
            PADDING_LEFT,
            block_top + 16,
            block.metric,
            12,
            colors.text,
            bold=True,
            max_width=LABEL_WIDTH,
        )
        for r, (kind, label) in enumerate(block_rows):
            baseline = rows_top + r * ROW_HEIGHT + 15
            canvas.text(
                PADDING_LEFT + 12, baseline, label, 11, colors.muted, max_width=LABEL_WIDTH - 14
            )
            for i, column in enumerate(columns):
                cell = block.cells[drawn[i]]
                quiet = silent(block, drawn[i])
                if kind is _Row.VALUE:
                    text, color = canvas.table_value(cell.current), colors.text
                elif quiet:
                    text, color = NONE, colors.muted
                elif kind is _Row.RATE:
                    text, color = level(cell.rate)
                elif kind is _Row.PREVIOUS_RATE:
                    text, color = level(cell.previous_rate)
                elif kind is _Row.RATE_POINTS:
                    text, color = points(cell.rate, cell.previous_rate)
                elif kind is _Row.RATE_GAP:
                    text, color = points(cell.rate, cell.reference_rate)
                elif kind is _Row.CHANGE:
                    text, color = canvas.signed_percent(cell.change), canvas.verdict(cell.change, 0)
                else:
                    # A distance between two growth rates, written with % like the block.
                    text = canvas.signed_percent(cell.change - cell.reference)
                    color = canvas.verdict(cell.change, cell.reference)
                canvas.text(right(i), baseline, text, 11, color, TextAnchor.END, column.total)
            rule_y = rows_top + (r + 1) * ROW_HEIGHT
            canvas.line(PADDING_LEFT, rule_y, width - PADDING_RIGHT, rule_y, colors.gridline, 1)

        block_top += heights[b] + BLOCK_GAP
        if b < len(table.blocks) - 1:
            divider = block_top - BLOCK_GAP / 2
            canvas.line(
                PADDING_LEFT, divider, width - PADDING_RIGHT, divider, colors.axis, 1, (4, 3)
            )
    return canvas.finish(height)
