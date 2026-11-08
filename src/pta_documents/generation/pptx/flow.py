"""Flow slides on ``Nur Titel``: blocks stacked top to bottom in the content area.

Port of the flow part of DocLibs ``DeckWriter`` (``Stack``, ``Place``, cards, rows, panels,
callouts, tags, code) and of ``FitFlow``, in the PTA style (``design.slides.FLOW``), plus the
PTA conclusion box (at the foot of the content area) and comment box (a speech bubble on the
block before it). Every method measures; with a slide it also draws.
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Final

from lxml import etree
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.slide import Slide as PptxSlide
from pptx.util import Emu

from pta_documents.design import colors
from pta_documents.design import icons as icon_set
from pta_documents.design import slides as design
from pta_documents.design.icons import loader as icon_loader
from pta_documents.drawing import riskmatrix as risk_drawing
from pta_documents.drawing import schedule as schedule_drawing
from pta_documents.drawing import steps as steps_drawing
from pta_documents.generation.common import icons, text_metrics
from pta_documents.generation.pptx import drawing, fitting, visuals
from pta_documents.generation.pptx.model import (
    CalloutBlock,
    Card,
    CardsBlock,
    CodeLinesBlock,
    ColumnsBlock,
    CommentBlock,
    ConclusionBlock,
    FlowBlock,
    FlowSlide,
    ImageRowBlock,
    Kind,
    LabelledTagsBlock,
    PanelBlock,
    Paragraph,
    RiskMatrixBlock,
    RowsBlock,
    Run,
    ScheduleBlock,
    StatementBlock,
    StepsBlock,
    TableBlock,
    TagsBlock,
    TextBlock,
    plain_text,
)

if TYPE_CHECKING:
    from pta_documents.generation.pptx.writer import DeckWriter

A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
EMU_PER_POINT: Final = text_metrics.EMU_PER_POINT
FLOW: Final = design.FLOW
CODE_EM: Final = 0.55
"""The width of a Consolas character, in em."""
SNAP: Final = design.cm(1.5)
"""A column edge this close to a guide moves onto it."""
GUIDE_GAPS: Final = tuple(
    (design.cm(end), design.cm(start))
    for (_, end), (start, _) in zip(design.COLUMN_GUIDES, design.COLUMN_GUIDES[1:], strict=False)
)


def a(name: str) -> str:
    return f"{{{A}}}{name}"


def p(name: str) -> str:
    return f"{{{P}}}{name}"


@dataclass(frozen=True)
class Box:
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    def below(self, y: int) -> Box:
        """The part of the box from ``y`` down."""
        return Box(self.x, y, self.w, max(self.bottom - y, 0))


@dataclass(frozen=True)
class Look:
    """How blocks are set: on a dark ground or not, shrunk by ``scale``, text at ``body_pt``."""

    dark: bool
    scale: float = 1.0
    body_pt: float = FLOW.text_pt

    def pt(self, size: float) -> float:
        """A size shrunk by the slide's scale, never below 12 pt (or the size itself)."""
        return max(round(size * self.scale * 2) / 2, min(size, design.MIN_FONT_PT))

    @property
    def gap(self) -> int:
        return FLOW.gap if self.scale >= 1 else FLOW.gap // 2

    @property
    def text_color(self) -> str | None:
        return colors.WHITE if self.dark else None

    @property
    def heading_color(self) -> str:
        return colors.WHITE if self.dark else colors.PTA_BLUE


def factor(size_pt: float) -> float:
    """The factor of a text size against the body size, for ``fitting.level_pt``."""
    return size_pt / FLOW.text_pt


def line_height(size_pt: float) -> int:
    return int(size_pt * fitting.LINE_FACTOR * EMU_PER_POINT)


def code_width(text: str, size_pt: float, bold: bool = False) -> int:
    width = len(text) * size_pt * CODE_EM * EMU_PER_POINT
    return int(width * (text_metrics.BOLD_FACTOR if bold else 1.0))


def bold(runs: Sequence[Run]) -> tuple[Run, ...]:
    return tuple(r if r.is_break else replace(r, bold=True) for r in runs)


class FlowWriter:
    def __init__(self, deck: DeckWriter, slide: PptxSlide | None) -> None:
        self.deck = deck
        self.slide = slide
        self.style = deck.body_style

    @property
    def measure(self) -> FlowWriter:
        return self if self.slide is None else FlowWriter(self.deck, None)

    # ------------------------------------------------------------------ stacking

    def stack(self, blocks: Sequence[FlowBlock], box: Box, look: Look) -> int:
        """Blocks top to bottom with a gap between them; returns the height they take.

        Images share the height the other blocks leave, each at least a quarter of the slide;
        a comment takes no height, it sits on the block before it.
        """
        placed = [b for b in blocks if not isinstance(b, CommentBlock)]
        visuals_count = sum(1 for b in placed if _is_visual(b))
        visual_room: int | None = None
        if visuals_count and box.h > 0:
            measure = self.measure
            others = sum(
                measure.place(b, Box(box.x, box.y, box.w, 0), look)
                for b in placed
                if not _is_visual(b)
            )
            others += look.gap * (len(placed) - 1)
            visual_room = max((box.h - others) // visuals_count, 0)
        y = box.y
        previous: Box | None = None
        for block in blocks:
            if isinstance(block, CommentBlock):
                if previous is not None:
                    self.comment(block, previous, box, look)
                continue
            if previous is not None:
                y += look.gap
            room = (
                visual_room
                if _is_visual(block) and visual_room is not None
                else max(box.bottom - y, 0)
            )
            height = self.place(block, Box(box.x, y, box.w, room), look)
            previous = Box(box.x, y, box.w, height)
            y += height
        return y - box.y

    def place(self, block: FlowBlock, box: Box, look: Look) -> int:
        match block:
            case TextBlock():
                return self.text(block.paragraphs, box, look.pt(look.body_pt), look.text_color)
            case TableBlock():
                return self.table(block, box, look)
            case ImageRowBlock():
                return self.pictures(block, box)
            case ColumnsBlock():
                return self.columns(block, box, look)
            case CardsBlock():
                return self.cards(block, box, look)
            case RowsBlock():
                return self.rows(block, box, look)
            case PanelBlock():
                return self.panel(block, box, look)
            case CalloutBlock():
                return self.callout(block, box, look)
            case StatementBlock():
                paragraph = Paragraph(bold(block.text), Kind.SUBHEADLINE)
                return self.text([paragraph], box, look.pt(FLOW.statement_pt), look.heading_color)
            case TagsBlock():
                return self.tags(block, box, look)
            case LabelledTagsBlock():
                return self.labelled_tags(block, box, look)
            case CodeLinesBlock():
                return self.code(block, box, look)
            case CommentBlock():
                return 0
            case ScheduleBlock():
                return self.schedule(block, box, look)
            case StepsBlock():
                return self.steps(block, box, look)
            case RiskMatrixBlock():
                return self.risk_matrix(block, box, look)

    # ------------------------------------------------------------------ text and visuals

    def text(
        self, paragraphs: Sequence[Paragraph], box: Box, size_pt: float, color: str | None
    ) -> int:
        """Paragraphs at their levels of the master, the body level at ``size_pt``."""
        f = factor(size_pt)
        height = fitting.flow_text_height(self.style, paragraphs, f, box.w)
        if self.slide is not None and paragraphs:
            body = self.text_box(Box(box.x, box.y, box.w, height))
            for n, paragraph in enumerate(paragraphs):
                element = self.deck.paragraph_element(self.slide, paragraph, f, color, n == 0)
                body.append(element)
        return height

    def text_box(self, box: Box) -> etree._Element:
        assert self.slide is not None
        body = visuals.text_box(self.slide, box.x, box.y, box.w, box.h)
        for old in body.findall(a("p")):
            body.remove(old)
        return body

    def table(self, block: TableBlock, box: Box, look: Look) -> int:
        table = block.table
        steps = fitting.table_steps()
        layout = fitting.fit_table(table, box.w, box.h) if box.h > 0 else None
        if layout is None:
            sizes = steps[0] if box.h <= 0 else steps[-1]
            layout = fitting.table_layout(table, box.w, *sizes)
        if self.slide is not None:
            deck = self.deck
            visuals.draw_table(
                self.slide, table, layout, box.x, box.y, deck.run_element, deck.lang, look.dark
            )
        return layout.height

    def pictures(self, block: ImageRowBlock, box: Box) -> int:
        room = max(box.h, FLOW.min_visual_height)
        images = list(block.images)
        used, factors = visuals.draw_pictures(self.slide, images, box.x, box.y, box.w, room)
        if self.slide is not None:
            for image, enlarged in zip(images, factors, strict=True):
                self.deck.note_enlarged(image, enlarged)
        return used

    def code(self, block: CodeLinesBlock, box: Box, look: Look) -> int:
        """Code on an area of its own, in Consolas with 130 % line spacing."""
        size = look.pt(FLOW.code_pt)
        line = int(size * FLOW.code_line_spacing * EMU_PER_POINT)
        height = len(block.lines) * line + 2 * FLOW.pad
        if self.slide is not None:
            self.shape(Box(box.x, box.y, box.w, height), FLOW.surface)
            body = self.text_box(
                Box(box.x + FLOW.pad, box.y + FLOW.pad, box.w - 2 * FLOW.pad, height - 2 * FLOW.pad)
            )
            body_pr = body.find(a("bodyPr"))
            assert body_pr is not None
            body_pr.set("wrap", "none")
            lang = self.deck.lang
            for n, text in enumerate(block.lines):
                paragraph = etree.SubElement(body, a("p"))
                p_pr = etree.SubElement(paragraph, a("pPr"), marL="0", indent="0", algn="l")
                spacing = etree.SubElement(p_pr, a("lnSpc"))
                etree.SubElement(spacing, a("spcPct")).set(
                    "val", str(round(FLOW.code_line_spacing * 100000))
                )
                etree.SubElement(etree.SubElement(p_pr, a("spcBef")), a("spcPts")).set("val", "0")
                etree.SubElement(p_pr, a("buNone"))
                spans = block.spans[n] if block.spans else None
                visuals.code_runs(paragraph, text, spans, size, lang)
                end = etree.SubElement(paragraph, a("endParaRPr"), lang=lang)
                end.set("sz", str(round(size * 100)))
        return height

    def schedule(self, block: ScheduleBlock, box: Box, look: Look) -> int:
        """A timeline or Gantt chart (E15-S01) as a group of shapes as wide as ``box``; its
        sizes stay as designed (text never below 10 pt), the slide is split or noted instead."""
        picture = schedule_drawing.draw(
            block.schedule, box.w / drawing.EMU_PER_PIXEL, dark=look.dark
        )
        height = round(picture.height * drawing.EMU_PER_PIXEL)
        if self.slide is not None:
            alt = block.schedule.alt
            drawing.place(self.slide, picture, box.x, box.y, box.w, height, alt, self.deck.lang)
        return height

    def steps(self, block: StepsBlock, box: Box, look: Look) -> int:
        """A row of chevrons (E15-S02) as a group of shapes as wide as ``box``, the texts below
        the chevrons; sizes stay as designed, the slide is split or noted instead."""
        picture = steps_drawing.draw(block.steps, box.w / drawing.EMU_PER_PIXEL, dark=look.dark)
        height = round(picture.height * drawing.EMU_PER_PIXEL)
        if self.slide is not None:
            alt = block.steps.alt
            drawing.place(self.slide, picture, box.x, box.y, box.w, height, alt, self.deck.lang)
        return height

    def risk_matrix(self, block: RiskMatrixBlock, box: Box, look: Look) -> int:
        """A risk matrix (E15-S02): the matrix in its natural size as a group of shapes on the
        left, its legend as a table to its right — below it when the right has less room than a
        column of the grid."""
        picture = risk_drawing.draw(block.matrix, dark=look.dark)
        width = round(picture.width * drawing.EMU_PER_PIXEL)
        height = round(picture.height * drawing.EMU_PER_PIXEL)
        beside = box.w - width - design.COLUMN_GAP >= design.RISK_LEGEND_MIN_WIDTH
        if self.slide is not None:
            alt = block.matrix.alt
            drawing.place(self.slide, picture, box.x, box.y, width, height, alt, self.deck.lang)
        legend = TableBlock(block.legend)
        if beside:
            left = box.x + width + design.COLUMN_GAP
            room = Box(left, box.y, box.x + box.w - left, box.h)
            return max(height, self.table(legend, room, look))
        top = box.y + height + look.gap
        room = Box(box.x, top, box.w, max(box.h - height - look.gap, 0) if box.h > 0 else 0)
        return height + look.gap + self.table(legend, room, look)

    # ------------------------------------------------------------------ containers

    def column_boxes(self, box: Box, weights: Sequence[int]) -> list[Box]:
        """Columns side by side in the ratio of ``weights``, ``COLUMN_GAP`` apart; across the
        whole content area their edges sit on the master's guides where they come close."""
        area = design.CONTENT_AREA
        count = len(weights)
        whole = box.x == area.left and box.w == area.width
        if whole and len(set(weights)) == 1 and count in (2, 3, 4):
            return [Box(x, box.y, w, box.h) for x, w in design.grid(count)]
        room = box.w - (count - 1) * design.COLUMN_GAP
        total = sum(weights)
        edges: list[tuple[int, int]] = []
        x = box.x
        for n, weight in enumerate(weights):
            width = box.right - x if n == count - 1 else room * weight // total
            edges.append((x, x + width))
            x += width + design.COLUMN_GAP
        if whole:
            for n in range(count - 1):
                end = edges[n][1]
                gap = min(GUIDE_GAPS, key=lambda g: abs(g[0] - end))
                if abs(gap[0] - end) <= SNAP:
                    edges[n] = (edges[n][0], gap[0])
                    edges[n + 1] = (gap[1], edges[n + 1][1])
        return [Box(left, box.y, right - left, box.h) for left, right in edges]

    def columns(self, block: ColumnsBlock, box: Box, look: Look) -> int:
        height = 0
        for column, blocks in zip(self.column_boxes(box, block.widths), block.columns, strict=True):
            height = max(height, self.stack(blocks, column, look))
        return height

    def cards(self, block: CardsBlock, box: Box, look: Look) -> int:
        """Cards side by side, up to four to a row on the grid, each row as tall as its tallest
        card: rectangles without fill, outlined in light grey."""
        per_row = min(len(block.cards), FLOW.max_cards_per_row)
        inner = replace(look, body_pt=FLOW.card_text_pt)
        y = box.y
        measure = self.measure
        for start in range(0, len(block.cards), per_row):
            row = block.cards[start : start + per_row]
            cells = self.column_boxes(box, [1] * per_row)
            height = max(
                measure.card(card, Box(cell.x, 0, cell.w, 0), inner)
                for card, cell in zip(row, cells, strict=False)
            )
            if self.slide is not None:
                for card, cell in zip(row, cells, strict=False):
                    frame = Box(cell.x, y, cell.w, height)
                    self.shape(frame, None, FLOW.card_line, FLOW.card_line_pt)
                    self.card(card, frame, inner)
            y += height + look.gap
        return y - look.gap - box.y

    def card(self, card: Card, box: Box, look: Look) -> int:
        """The figure (large), then the title, then the blocks."""
        pad = FLOW.pad
        inner = Box(box.x + pad, box.y + pad, box.w - 2 * pad, max(box.h - 2 * pad, 0))
        y = inner.y
        if card.figure is not None:
            figure = Paragraph(bold(card.figure), Kind.SUBHEADLINE)
            y += self.text([figure], inner.below(y), look.pt(FLOW.figure_pt), look.heading_color)
        if card.icon is not None:
            y += self.icon(card.icon, inner.x, y, look) + FLOW.row_pad
        title = Paragraph(card.title, Kind.SUBHEADLINE)
        y += self.text([title], inner.below(y), look.pt(FLOW.title_pt), look.heading_color)
        if card.blocks:
            y += FLOW.row_pad
            y += self.stack(card.blocks, inner.below(y), look)
        return y - inner.y + 2 * pad

    def icon(self, name: str, x: int, y: int, look: Look) -> int:
        """The icon ``name`` (E15-S03) as a group of shapes ``FLOW.icon`` wide, its top left
        corner at (``x``, ``y``), in PTA blue (white on dark areas); returns its height."""
        size = round(FLOW.icon * min(look.scale, 1.0))
        if self.slide is not None:
            picture = icon_loader.drawing(
                name, icons.color_on(look.dark), size / drawing.EMU_PER_PIXEL
            )
            alt = icon_set.alt(name)
            drawing.place(self.slide, picture, x, y, size, size, alt, self.deck.lang, alt)
        return size

    def rows(self, block: RowsBlock, box: Box, look: Look) -> int:
        """The term in the left third, the description beside it; a light rule above each row
        and a dark one below the last, like the slide table."""
        term_width = box.w // 3
        gap = design.COLUMN_GAP
        description_x = box.x + term_width + gap
        description_width = box.w - term_width - gap
        rule = int(FLOW.rule_pt * EMU_PER_POINT)
        measure = self.measure
        y = box.y
        for row in block.rows:
            term = Paragraph(row.term, Kind.SUBHEADLINE)
            term_pt, text_pt = look.pt(FLOW.title_pt), look.pt(look.body_pt)
            height = max(
                measure.text([term], Box(box.x, 0, term_width, 0), term_pt, None),
                measure.text(row.description, Box(0, 0, description_width, 0), text_pt, None),
            )
            height += 2 * FLOW.row_pad
            if self.slide is not None:
                self.rule(box.x, box.right, y, FLOW.rule)
                top = y + FLOW.row_pad
                self.text([term], Box(box.x, top, term_width, 0), term_pt, look.heading_color)
                self.text(
                    row.description,
                    Box(description_x, top, description_width, 0),
                    text_pt,
                    look.text_color,
                )
            y += height
        if self.slide is not None:
            self.rule(box.x, box.right, y, colors.WHITE if look.dark else FLOW.closing_rule)
        return y + rule - box.y

    def panel(self, block: PanelBlock, box: Box, look: Look) -> int:
        """An area of light grey behind its blocks; ``dark``: dark blue, text in white."""
        inner = replace(look, dark=block.dark)
        pad = FLOW.pad
        content = Box(box.x + pad, box.y + pad, box.w - 2 * pad, max(box.h - 2 * pad, 0))
        height = self.measure.stack(block.blocks, content, inner) + 2 * pad
        if self.slide is not None:
            fill = FLOW.dark_surface if block.dark else FLOW.surface
            self.shape(Box(box.x, box.y, box.w, height), fill)
            self.stack(block.blocks, content, inner)
        return height

    def callout(self, block: CalloutBlock, box: Box, look: Look) -> int:
        """An area of light grey with a bar on its left: PTA blue for notes and tips, yellow for
        the important kinds."""
        inner = replace(look, dark=False)
        pad = FLOW.pad
        left = box.x + FLOW.alert_bar + pad
        content = Box(left, box.y + pad, box.right - pad - left, max(box.h - 2 * pad, 0))
        height = self.measure.stack(block.blocks, content, inner) + 2 * pad
        if self.slide is not None:
            self.shape(Box(box.x, box.y, box.w, height), FLOW.surface)
            bar = FLOW.important_bar if block.important else FLOW.note_bar
            self.shape(Box(box.x, box.y, FLOW.alert_bar, height), bar)
            self.stack(block.blocks, content, inner)
        return height

    # ------------------------------------------------------------------ tags

    def chip_height(self, size_pt: float) -> int:
        return line_height(size_pt) + 2 * FLOW.chip_pad_y

    def tags(self, block: TagsBlock, box: Box, look: Look) -> int:
        """Chips left to right, wrapping at the right edge."""
        size = look.pt(FLOW.tag_pt)
        height = self.chip_height(size)
        x, y = box.x, box.y
        for tag in block.tags:
            width = min(code_width(tag, size) + 2 * FLOW.chip_pad_x, box.w)
            if x > box.x and x + width > box.right:
                x, y = box.x, y + height + FLOW.chip_gap
            if self.slide is not None:
                self.chip(Box(x, y, width, height), tag, size, False, look)
            x += width + FLOW.chip_gap
        return y + height - box.y

    def labelled_tags(self, block: LabelledTagsBlock, box: Box, look: Look) -> int:
        """The labels as chips in a column as wide as the widest, each text beside its label."""
        size = look.pt(FLOW.tag_pt)
        chip = self.chip_height(size)
        label_width = min(
            max(code_width(i.label, size, bold=True) for i in block.items) + 2 * FLOW.chip_pad_x,
            box.w // 2,
        )
        text_x = box.x + label_width + FLOW.chip_gap
        text_width = box.w - label_width - FLOW.chip_gap
        text_pt = look.pt(look.body_pt)
        measure = self.measure
        y = box.y
        for n, item in enumerate(block.items):
            if n:
                y += FLOW.chip_gap
            paragraph = Paragraph(item.text)
            text = measure.text([paragraph], Box(0, 0, text_width, 0), text_pt, None)
            if self.slide is not None:
                self.chip(Box(box.x, y, label_width, chip), item.label, size, True, look)
                self.text([paragraph], Box(text_x, y, text_width, 0), text_pt, look.text_color)
            y += max(chip, text)
        return y - box.y

    def chip(self, box: Box, text: str, size_pt: float, strong: bool, look: Look) -> None:
        """A chip: outlined in PTA blue (white on dark), its text in Consolas."""
        color = colors.WHITE if look.dark else FLOW.tag_line
        shape = self.shape(box, None, color, FLOW.tag_line_pt)
        body = self.shape_text(shape, FLOW.chip_pad_x, FLOW.chip_pad_y, wrap=False)
        paragraph = etree.SubElement(body, a("p"))
        etree.SubElement(paragraph, a("pPr"), algn="ctr")
        run = self.deck.run_element(
            self.slide_, Run(text, bold=strong), round(size_pt * 100), color
        )
        r_pr = run.find(a("rPr"))
        assert r_pr is not None
        for latin in r_pr.findall(a("latin")):
            r_pr.remove(latin)
        etree.SubElement(r_pr, a("latin")).set("typeface", design.CODE_FONT)
        paragraph.append(run)

    # ------------------------------------------------------------------ PTA boxes

    def comment(self, block: CommentBlock, previous: Box, box: Box, look: Look) -> None:
        """The comment box at the top right of the block before it, its point to the lower
        left onto that block; at most half as wide as ``box``."""
        if self.slide is None:
            return
        style = design.COMMENT
        size = look.pt(style.size_pt)
        runs = [bold(p.runs) for p in block.paragraphs]
        natural = max(
            text_metrics.width(plain_text(r), size, bold=True) for r in runs if plain_text(r)
        )
        width = int(min(natural + 2 * style.inset_x + 1, box.w * style.max_share))
        available = width - 2 * style.inset_x
        lines = sum(text_metrics.lines(fitting.metric_runs(r), size, True, available) for r in runs)
        height = lines * line_height(size) + 2 * style.inset_y
        top = previous.y
        shape = self.shape(
            Box(box.right - width, top, width, height),
            style.fill,
            preset=MSO_SHAPE.RECTANGULAR_CALLOUT,
        )
        # The point: a tenth of the width left of the box, down onto the block before it.
        point = min(previous.bottom, top + height + height // 2)
        below = max((point - (top + height / 2)) / height, 0.6)
        adjustments: Any = shape.adjustments
        adjustments[0] = -0.6
        adjustments[1] = below
        sp_pr = shape._element.spPr
        line = etree.SubElement(sp_pr, a("ln"), w=str(round(style.line_pt * EMU_PER_POINT)))
        gradient = etree.SubElement(line, a("gradFill"))
        stops = etree.SubElement(gradient, a("gsLst"))
        for position, color in ((0, style.line_from), (100_000, style.line_to)):
            stop = etree.SubElement(stops, a("gs"), pos=str(position))
            etree.SubElement(stop, a("srgbClr")).set("val", color)
        etree.SubElement(gradient, a("lin"), ang="5400000", scaled="1")
        body = self.shape_text(shape, style.inset_x, style.inset_y, wrap=True)
        for paragraph_runs in runs:
            paragraph = etree.SubElement(body, a("p"))
            etree.SubElement(paragraph, a("pPr"), algn="ctr")
            for run in paragraph_runs:
                if run.is_break:
                    etree.SubElement(etree.SubElement(paragraph, a("br")), a("rPr"))
                    continue
                paragraph.append(
                    self.deck.run_element(self.slide, run, round(size * 100), style.color)
                )

    def conclusion(self, block: ConclusionBlock, size_pt: float) -> None:
        """The conclusion box in the measures of the template collection: dark blue across the
        foot of the content area, bold white text."""
        style = design.CONCLUSION
        area = style.area
        shape = self.shape(Box(area.left, area.top, area.width, area.height), style.fill)
        body = self.shape_text(shape, style.inset_left, style.inset_y, wrap=True)
        body_pr = body.find(a("bodyPr"))
        assert body_pr is not None
        body_pr.set("rIns", str(style.inset_right))
        assert self.slide is not None
        for paragraph_runs in block.paragraphs:
            paragraph = etree.SubElement(body, a("p"))
            etree.SubElement(paragraph, a("pPr"), marL="0", indent="0", algn="l")
            for run in bold(paragraph_runs.runs):
                if run.is_break:
                    etree.SubElement(etree.SubElement(paragraph, a("br")), a("rPr"))
                    continue
                element = self.deck.run_element(self.slide, run, round(size_pt * 100), style.color)
                paragraph.append(element)

    # ------------------------------------------------------------------ shapes

    @property
    def slide_(self) -> PptxSlide:
        assert self.slide is not None
        return self.slide

    def shape(
        self,
        box: Box,
        fill: str | None,
        line: str | None = None,
        line_pt: float = 0.75,
        preset: MSO_SHAPE = MSO_SHAPE.RECTANGLE,
    ) -> Any:
        """A shape of ``preset`` (PTA patterns are square), filled or not, outlined or not."""
        shape: Any = self.slide_.shapes.add_shape(
            preset, Emu(box.x), Emu(box.y), Emu(box.w), Emu(max(box.h, 1))
        )
        element = shape._element
        style = element.find(p("style"))
        if style is not None:
            element.remove(style)
        sp_pr = element.spPr
        if fill is None:
            etree.SubElement(sp_pr, a("noFill"))
        else:
            _fill(sp_pr, fill)
        if line is not None:
            outline = etree.SubElement(sp_pr, a("ln"), w=str(round(line_pt * EMU_PER_POINT)))
            _fill(outline, line)
        elif preset is not MSO_SHAPE.RECTANGULAR_CALLOUT:
            etree.SubElement(etree.SubElement(sp_pr, a("ln")), a("noFill"))
        for paragraph in element.txBody.findall(a("p")):
            element.txBody.remove(paragraph)
        etree.SubElement(element.txBody, a("p"))
        return shape

    def shape_text(self, shape: Any, inset_x: int, inset_y: int, wrap: bool) -> etree._Element:
        """The emptied text body of ``shape``, its text centred vertically between insets."""
        body: etree._Element = shape._element.txBody
        for paragraph in body.findall(a("p")):
            body.remove(paragraph)
        body_pr = body.find(a("bodyPr"))
        assert body_pr is not None
        for child in list(body_pr):
            body_pr.remove(child)
        body_pr.set("wrap", "square" if wrap else "none")
        body_pr.set("lIns", str(inset_x))
        body_pr.set("rIns", str(inset_x))
        body_pr.set("tIns", str(inset_y))
        body_pr.set("bIns", str(inset_y))
        body_pr.set("rtlCol", "0")
        body_pr.set("anchor", "ctr")
        etree.SubElement(body_pr, a("noAutofit"))
        return body

    def rule(self, left: int, right: int, y: int, color: str) -> None:
        connector: Any = self.slide_.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, Emu(left), Emu(y), Emu(right), Emu(y)
        )
        element = connector._element
        style = element.find(p("style"))
        if style is not None:
            element.remove(style)
        line = etree.SubElement(element.spPr, a("ln"), w=str(round(FLOW.rule_pt * EMU_PER_POINT)))
        _fill(line, color)


def _fill(parent: etree._Element, color: str) -> None:
    fill = etree.SubElement(parent, a("solidFill"))
    etree.SubElement(fill, a("srgbClr")).set("val", color)


def _is_visual(block: FlowBlock) -> bool:
    if isinstance(block, ImageRowBlock):
        return True
    if isinstance(block, ColumnsBlock):
        return any(_is_visual(b) for column in block.columns for b in column)
    return False


# ---------------------------------------------------------------------- the slide


@dataclass(frozen=True)
class _Piece:
    block: FlowBlock
    origin: int


def units(blocks: Sequence[FlowBlock]) -> list[list[_Piece]]:
    """The blocks in the units a split may fall between: paragraph groups, table rows (each
    with the header), the items of rows and labelled tags; a comment stays with the block
    before it, every other block is whole."""
    result: list[list[_Piece]] = []
    for origin, block in enumerate(blocks):
        match block:
            case TextBlock():
                for group in fitting.groups(block.paragraphs):
                    result.append([_Piece(TextBlock(tuple(group)), origin)])
            case RowsBlock():
                for row in block.rows:
                    result.append([_Piece(RowsBlock((row,)), origin)])
            case LabelledTagsBlock():
                for item in block.items:
                    result.append([_Piece(LabelledTagsBlock((item,)), origin)])
            case TableBlock() if len(block.table.rows) - block.table.has_header >= 2:
                table = block.table
                for n, row in enumerate(range(1 if table.has_header else 0, len(table.rows))):
                    part = table.subset([row], keep_title=n == 0)
                    result.append([_Piece(TableBlock(part), origin)])
            case CommentBlock() if result:
                result[-1].append(_Piece(block, origin))
            case _:
                result.append([_Piece(block, origin)])
    return result


def combine(pieces: Sequence[_Piece]) -> list[FlowBlock]:
    """Pieces back into blocks: neighbouring pieces of one block joined."""
    blocks: list[FlowBlock] = []
    last: _Piece | None = None
    for piece in pieces:
        if last is not None and last.origin == piece.origin:
            joined = _join(blocks[-1], piece.block)
            if joined is not None:
                blocks[-1] = joined
                last = piece
                continue
        blocks.append(piece.block)
        last = piece
    return blocks


def _join(first: FlowBlock, second: FlowBlock) -> FlowBlock | None:
    match first, second:
        case TextBlock(), TextBlock():
            return TextBlock(first.paragraphs + second.paragraphs)
        case RowsBlock(), RowsBlock():
            return RowsBlock(first.rows + second.rows)
        case LabelledTagsBlock(), LabelledTagsBlock():
            return LabelledTagsBlock(first.items + second.items)
        case TableBlock(), TableBlock():
            a_table, b_table = first.table, second.table
            skip = 1 if b_table.has_header else 0
            return TableBlock(
                replace(
                    a_table,
                    rows=a_table.rows + b_table.rows[skip:],
                    highlighted=a_table.highlighted + b_table.highlighted[skip:],
                )
            )
        case _:
            return None


def conclusion_size(deck: DeckWriter, block: ConclusionBlock) -> tuple[float | None, int]:
    """The largest size at which the conclusion takes at most two lines (None: none), and the
    lines it takes at the smallest size."""
    style = design.CONCLUSION
    available = style.area.width - style.inset_left - style.inset_right
    lines = 0
    for size in style.sizes_pt:
        lines = sum(
            text_metrics.lines(fitting.metric_runs(bold(p.runs)), size, True, available)
            for p in block.paragraphs
        )
        if lines <= style.max_lines:
            return size, lines
    return None, lines


def flow_area(slide: FlowSlide) -> Box:
    area = design.CONTENT_AREA
    bottom = area.bottom
    if slide.conclusion is not None:
        bottom = design.CONCLUSION.area.top - FLOW.gap
    return Box(area.left, area.top, area.width, bottom - area.top)


def write_flow_slide(deck: DeckWriter, slide: FlowSlide) -> None:
    """The slide on ``Nur Titel``; what does not fit at the smallest step continues on further
    slides with "(Forts.)", which keep the kicker; the conclusion box goes on the last."""
    if _two_columns(deck, slide):
        return
    conclusion_pt: float | None = None
    if slide.conclusion is not None:
        conclusion_pt, lines = conclusion_size(deck, slide.conclusion)
        if conclusion_pt is None:
            smallest = design.CONCLUSION.sizes_pt[-1]
            raise deck.error(
                f"The '::: conclusion' of the slide \"{plain_text(slide.title)}\" takes "
                f"{design.CONCLUSION.max_lines} lines at most (the PTA conclusion box), but needs "
                f"{lines} even at {smallest:g} pt. Shorten it",
                slide,
            )
    area = flow_area(slide)
    measure = FlowWriter(deck, None)
    steps = FLOW.shrink_steps

    def height(blocks: Sequence[FlowBlock], step: int) -> int:
        return measure.stack(blocks, area, Look(slide.dark, steps[step]))

    def fitting_step(blocks: Sequence[FlowBlock]) -> int | None:
        return next((s for s in range(len(steps)) if height(blocks, s) <= area.h), None)

    last = len(steps) - 1
    step = fitting_step(slide.blocks)
    parts: list[tuple[Sequence[FlowBlock], int]] = []
    if step is not None:
        parts.append((slide.blocks, step))
    else:
        packed = fitting.pack(
            units(slide.blocks), lambda pieces: height(combine(pieces), last) <= area.h
        )
        for pieces in packed:
            blocks = combine(pieces)
            part_step = fitting_step(blocks)
            if part_step is None:
                deck.note_overfull(slide)
                part_step = last
            parts.append((blocks, part_step))
        deck.note_split(slide, len(parts))
    color = colors.WHITE if slide.dark else None
    for n, (blocks, part_step) in enumerate(parts):
        target = _headed_slide(deck, slide, design.LAYOUTS.title_only, n)
        FlowWriter(deck, target).stack(blocks, area, Look(slide.dark, steps[part_step]))
        if slide.conclusion is not None and conclusion_pt is not None and n == len(parts) - 1:
            FlowWriter(deck, target).conclusion(slide.conclusion, conclusion_pt)
        deck.finish(target, footer=True, color=color)


def _headed_slide(deck: DeckWriter, slide: FlowSlide, layout: str, part: int) -> PptxSlide:
    """A new slide with its title (and kicker); dark: on the background of the title slide."""
    target = deck.new_slide(layout, slide)
    color = colors.WHITE if slide.dark else None
    if slide.dark:
        _paint_dark(deck, target)
    deck.set_title(target, deck.continued(slide.title, part), color)
    if slide.kicker is not None:
        _kicker(deck, target, slide.kicker, color or FLOW.kicker_color)
    return target


def _paint_dark(deck: DeckWriter, target: PptxSlide) -> None:
    layout = deck.layouts.get(design.DARK_BACKGROUND_LAYOUT)
    background = None
    if layout is not None:
        background = layout._element.find(f"{p('cSld')}/{p('bg')}")
    c_sld = target._element.find(p("cSld"))
    assert c_sld is not None
    if background is not None:
        c_sld.insert(0, copy.deepcopy(background))
        return
    bg = etree.Element(p("bg"))
    bg_pr = etree.SubElement(bg, p("bgPr"))
    _fill(bg_pr, colors.DARK_BLUE)
    etree.SubElement(bg_pr, a("effectLst"))
    c_sld.insert(0, bg)


def _kicker(deck: DeckWriter, target: PptxSlide, kicker: str, color: str) -> None:
    """The kicker above the title: 12 pt bold capitals."""
    area = design.CONTENT_AREA
    size = FLOW.kicker_pt
    left, top = FLOW.kicker_left, FLOW.kicker_top
    body = FlowWriter(deck, target).text_box(Box(left, top, area.right - left, line_height(size)))
    paragraph = etree.SubElement(body, a("p"))
    etree.SubElement(paragraph, a("pPr"), marL="0", indent="0")
    run = deck.run_element(target, Run(kicker, bold=True), round(size * 100), color)
    r_pr = run.find(a("rPr"))
    assert r_pr is not None
    r_pr.set("cap", "all")
    paragraph.append(run)


def _two_columns(deck: DeckWriter, slide: FlowSlide) -> bool:
    """PTA rule, layouts of the template first: exactly two equal columns of text (and nothing
    else on a light slide) go on ``Titel und Text (zweispaltig)``, if they fit there."""
    if slide.dark or slide.conclusion is not None or len(slide.blocks) != 1:
        return False
    block = slide.blocks[0]
    if not isinstance(block, ColumnsBlock) or len(block.columns) != 2:
        return False
    if block.widths[0] != block.widths[1]:
        return False
    if not all(isinstance(b, TextBlock) for column in block.columns for b in column):
        return False
    texts = [
        [p for b in column if isinstance(b, TextBlock) for p in b.paragraphs]
        for column in block.columns
    ]
    layout_name = design.LAYOUTS.title_and_two_texts
    layout = deck.layouts.get(layout_name)
    if layout is None:
        return False
    sizes = {
        shape.placeholder_format.idx: (int(shape.width or 0), int(shape.height or 0))
        for shape in layout.placeholders
    }
    ph = design.PLACEHOLDERS
    scales: list[float] = []
    for idx, text in zip((ph.body, ph.second_body), texts, strict=True):
        if idx not in sizes:
            return False
        scale = fitting.text_scale(deck.body_style, text, *sizes[idx])
        if scale is None:
            return False
        scales.append(scale)
    target = _headed_slide(deck, slide, layout_name, 0)
    for idx, text in zip((ph.body, ph.second_body), texts, strict=True):
        deck.set_paragraphs(target, idx, text, min(scales))
    deck.finish(target, footer=True)
    return True
