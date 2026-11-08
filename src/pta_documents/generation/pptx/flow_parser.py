"""The blocks of a flow slide: a ``##`` section that uses the slide-layout Markdown.

Port of the flow part of DocLibs ``DeckParser`` (``Container``, ``Cards``, ``Rows``, ``Item``,
``Flow``, ``Tags``, ``LabelledTags``, ``Columns``) with the same messages, plus the PTA
conclusion box (``::: conclusion``) and comment box (``::: comment``). Structural mistakes raise
``DocumentConversionError`` with the line in front, like ``layout_syntax.check``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Final

from markdown_it.token import Token

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import (
    heading_attributes,
    icons,
    layout_syntax,
    layout_tokens,
    risks,
    schedule,
    steps,
)
from pta_documents.generation.pptx.model import (
    Align,
    CalloutBlock,
    Card,
    CardsBlock,
    Chart,
    Click,
    Code,
    CodeLinesBlock,
    ColumnsBlock,
    CommentBlock,
    ConclusionBlock,
    Diagram,
    Effect,
    FlowBlock,
    FlowSlide,
    ImageRowBlock,
    Images,
    Item,
    LabelledTag,
    LabelledTagsBlock,
    PanelBlock,
    Paragraph,
    RiskMatrixBlock,
    Row,
    RowsBlock,
    Run,
    ScheduleBlock,
    StatementBlock,
    StepsBlock,
    Table,
    TableBlock,
    TagsBlock,
    TextBlock,
    trim,
)
from pta_documents.markdown.parser import ALERT, CONTAINER_OPEN, container

if TYPE_CHECKING:
    from pta_documents.generation.pptx.parser import DeckParser

FORMAT: Final = DocumentFormat.PPTX
SEPARATOR: Final = re.compile(r"^\s*(?:[–—:]|-(?=\s))?\s*")
"""What separates an item's bold title from its text: ``**Title** – text``, ``**Title:** text``."""
LISTS: Final = ("bullet_list_open", "ordered_list_open")


def block_end(tokens: list[Token], i: int) -> int:
    """The index after the block that starts at ``tokens[i]``."""
    token = tokens[i]
    if token.nesting != 1:
        return i + 1
    j = i + 1
    while not (tokens[j].nesting == -1 and tokens[j].level == token.level):
        j += 1
    return j + 1


def children(tokens: list[Token], i: int) -> list[int]:
    """Where the child blocks of the container block at ``tokens[i]`` start."""
    close = block_end(tokens, i) - 1
    result: list[int] = []
    j = i + 1
    while j < close:
        result.append(j)
        j = block_end(tokens, j)
    return result


@dataclass
class _Collector:
    """The blocks of a flow slide or of a container on one; consecutive paragraphs make one
    text block."""

    in_container: bool
    blocks: list[FlowBlock] = field(default_factory=lambda: list[FlowBlock]())
    text: list[Paragraph] | None = None

    def paragraph(self, paragraph: Paragraph) -> None:
        if self.text is None:
            self.text = []
            self.blocks.append(TextBlock(()))
        self.text.append(paragraph)
        self.blocks[-1] = TextBlock(tuple(self.text))

    def add(self, block: FlowBlock) -> None:
        self.text = None
        self.blocks.append(block)


class FlowReader:
    def __init__(self, deck: DeckParser) -> None:
        self.deck = deck
        self.tokens = deck.tokens
        self.conclusion: ConclusionBlock | None = None
        self.today = schedule.reference_day(deck.options.date)
        """What ``heute`` in a timeline or Gantt chart is."""

    def slide(
        self,
        title: tuple[Run, ...],
        line: int | None,
        attributes: heading_attributes.HeadingAttributes | None,
        start: int,
        end: int,
    ) -> FlowSlide:
        starts: list[int] = []
        i = start
        while i < end:
            starts.append(i)
            i = block_end(self.tokens, i)
        blocks = self.flow(starts, in_container=False)
        return FlowSlide(
            title,
            line,
            attributes.kicker if attributes else None,
            attributes.dark if attributes else False,
            tuple(blocks),
            self.conclusion,
        )

    # ------------------------------------------------------------------ walking

    def error(self, reason: str, token: Token) -> DocumentConversionError:
        return layout_syntax.at_line(DocumentConversionError(FORMAT, reason), self.deck.line(token))

    def flow(self, starts: list[int], in_container: bool) -> list[FlowBlock]:
        collector = _Collector(in_container)
        for i in starts:
            self.walk(i, collector)
        return collector.blocks

    def walk(self, i: int, target: _Collector) -> None:
        with self.deck.marked(self.tokens, i):
            self.read(i, target)

    def read(self, i: int, target: _Collector) -> None:
        """The block at ``tokens[i]``, its block marker applied (E09-S02): a block carries the
        click it is built on as a whole, ``deck.current``."""
        tokens = self.tokens
        token = tokens[i]
        deck = self.deck
        if token.type == CONTAINER_OPEN:
            self.container(i, target)
        elif token.type == "blockquote_open" and ALERT in token.meta:
            important = layout_syntax.is_important(str(token.meta[ALERT]), FORMAT)
            click = deck.current
            blocks = self.flow(children(tokens, i), in_container=True)
            target.add(CalloutBlock(important, tuple(blocks), click=click))
        elif token.type == "paragraph_open" and (tags := layout_tokens.tags(tokens[i + 1])):
            target.add(TagsBlock(tuple(tags), click=deck.current))
        elif (
            token.type in LISTS
            and target.in_container
            and (labelled := layout_tokens.labelled_tags(tokens, i)) is not None
        ):
            each = deck.take_each()
            click = deck.next_click(each) if each is not None else deck.current
            tagged = tuple(LabelledTag(label, self.inline_runs(rest)) for label, rest in labelled)
            target.add(LabelledTagsBlock(tagged, click=click))
        elif token.type == "table_open":
            items: list[Item] = []
            deck.table(tokens, i, items, labels=True)
            self.items(items, target)
        elif token.type == "hr":
            pass
        else:
            items = []
            deck.read_block(tokens, i, items, depth=0, italic=False)
            self.items(items, target)

    def items(self, items: list[Item], target: _Collector) -> None:
        for item in items:
            match item:
                case Paragraph():
                    target.paragraph(item)
                case Table():
                    target.add(TableBlock(item))
                case Images():
                    target.add(ImageRowBlock(item.images))
                case Code():
                    target.add(CodeLinesBlock(item.lines, item.spans, click=item.click))
                case Diagram():
                    raise layout_syntax.at_line(
                        DocumentConversionError(
                            FORMAT,
                            f"A `{item.alt}` drawing goes on a slide of its own (with text before "
                            "or after it); a flow slide has no place for it.",
                        ),
                        item.line,
                    )
                case Chart():
                    raise layout_syntax.at_line(
                        DocumentConversionError(
                            FORMAT,
                            "A chart goes on a slide of its own (with text before or after it), "
                            "or two side by side in a '::: columns' of nothing else; a flow "
                            "slide has no place for it yet.",
                        ),
                        item.line,
                    )
                case _:
                    pass  # a '---' means nothing on a flow slide

    def inline_runs(self, inline_children: list[Token]) -> tuple[Run, ...]:
        """The runs of some inline tokens (part of a paragraph)."""
        return self.deck.text_runs(Token("inline", "", 0, children=inline_children))

    def paragraph_runs(self, i: int) -> tuple[Run, ...]:
        """The runs of the paragraph or heading at ``tokens[i]``."""
        return self.deck.text_runs(self.tokens[i + 1])

    def text_only(self, starts: list[int], what: str, token: Token) -> tuple[Paragraph, ...]:
        paragraphs: list[Paragraph] = []
        for block in self.flow(starts, in_container=True):
            if not isinstance(block, TextBlock):
                raise self.error(f"A '::: {what}' holds text only.", token)
            paragraphs.extend(block.paragraphs)
        if not paragraphs:
            raise self.error(f"A '::: {what}' holds no text.", token)
        return tuple(paragraphs)

    # ------------------------------------------------------------------ containers

    def container(self, i: int, target: _Collector) -> None:
        tokens = self.tokens
        token = tokens[i]
        name, arguments = container(token)
        kids = children(tokens, i)
        # '{.build}' builds cards, rows and columns one by one: each takes a click of its own.
        each = self.deck.take_each()
        click = self.deck.current
        match name:
            case layout_syntax.CARDS:
                target.add(CardsBlock(tuple(self.cards(i, kids, each)), click=click))
            case layout_syntax.ROWS:
                target.add(RowsBlock(tuple(self.rows(i, kids, each)), click=click))
            case layout_syntax.PANEL:
                blocks = self.flow(kids, in_container=True)
                target.add(PanelBlock(arguments == "dark", tuple(blocks), click=click))
            case layout_syntax.COLUMNS:
                target.add(self.columns(i, kids, arguments, each))
            case layout_syntax.STATEMENT:
                if not kids or tokens[kids[0]].type != "paragraph_open":
                    raise self.error(
                        "A '::: statement' starts with a paragraph, its statement.", token
                    )
                target.add(StatementBlock(self.paragraph_runs(kids[0]), click=click))
                for kid in kids[1:]:
                    self.walk(kid, target)
            case layout_syntax.CONCLUSION:
                if target.in_container:
                    raise self.error(
                        "A '::: conclusion' goes on the slide itself, not inside another "
                        "container: it is the box at the foot of the slide.",
                        token,
                    )
                if self.conclusion is not None:
                    raise self.error("A slide holds one '::: conclusion' at most.", token)
                self.conclusion = ConclusionBlock(self.text_only(kids, name, token), click=click)
            case layout_syntax.COMMENT:
                paragraphs = self.text_only(kids, name, token)
                if not target.blocks or isinstance(target.blocks[-1], CommentBlock):
                    raise self.error(
                        "A '::: comment' comments on the block right before it; put it after "
                        "a paragraph, list, table, image or container.",
                        token,
                    )
                target.add(CommentBlock(paragraphs, click=click))
            case layout_syntax.TIMELINE:
                read = schedule.read_timeline(tokens, i, FORMAT, self.deck.line_offset, self.today)
                target.add(ScheduleBlock(read, click=click))
            case layout_syntax.GANTT:
                language = self.deck.options.language
                read = schedule.read_gantt(
                    tokens, i, FORMAT, self.deck.line_offset, self.today, language
                )
                target.add(ScheduleBlock(read, click=click))
            case layout_syntax.STEPS:
                read_steps = steps.read_steps(tokens, i, FORMAT, self.deck.line_offset)
                target.add(StepsBlock(read_steps, click=click))
            case layout_syntax.RISK_MATRIX:
                matrix = risks.read_risk_matrix(tokens, i, FORMAT, self.deck.line_offset)
                legend = matrix.legend()
                rows = tuple(tuple((Run(text),) for text in row) for row in legend)
                table = Table(rows, (Align.DEFAULT,) * len(legend[0]), True)
                target.add(RiskMatrixBlock(matrix, table, click=click))
            case _:  # pragma: no cover - layout_syntax.check refused it before
                layout_syntax.check_container(name, arguments, FORMAT)

    def click(self, each: Effect | None) -> Click | None:
        """The click of the next element of a container built one by one; None: not built
        so."""
        return self.deck.next_click(each) if each is not None else None

    def cards(self, i: int, kids: list[int], each: Effect | None = None) -> list[Card]:
        """A list of ``**Title** – text`` items, or a ``###`` heading before each card's blocks;
        with ``each``, every card on a click of its own."""
        tokens = self.tokens
        if len(kids) == 1 and tokens[kids[0]].type in LISTS:
            cards: list[Card] = []
            for item in children(tokens, kids[0]):
                first = children(tokens, item)
                icon = (
                    icons.leading(tokens[first[0] + 1])
                    if first and tokens[first[0]].type == "paragraph_open"
                    else None
                )
                click = self.click(each)
                with self.deck.at(click):
                    title, rest, others = self.item(item, layout_syntax.CARDS)
                    body = self.flow(others, in_container=True)
                    if rest:
                        body.insert(0, TextBlock((Paragraph(rest, click=self.deck.current),)))
                cards.append(Card(title, None, tuple(body), icon=icon, click=click))
            return cards

        cards = []
        heading: int | None = None
        blocks: list[int] = []

        def add() -> None:
            if heading is None:
                return
            figure: tuple[Run, ...] | None = None
            rest = blocks
            if (
                blocks
                and tokens[blocks[0]].type == "paragraph_open"
                and _is_figure(tokens[blocks[0] + 1])
            ):
                figure = self.paragraph_runs(blocks[0])
                rest = blocks[1:]
            inline = tokens[heading + 1]
            icon = icons.leading(inline)
            if icon is not None and figure is not None:
                raise self.error(
                    "A card has one figure: an icon at the start of its title or a **number** "
                    "below it, not both.",
                    tokens[heading],
                )
            click = self.click(each)
            with self.deck.at(click):
                body = self.flow(rest, in_container=True)
            title = self.deck.text_runs(icons.without_leading(inline))
            cards.append(Card(title, figure, tuple(body), icon=icon, click=click))

        for kid in kids:
            token = tokens[kid]
            if token.type == "heading_open" and token.tag == "h3":
                add()
                heading = kid
                blocks = []
            elif heading is None:
                raise self.error(
                    "In '::: cards', each card starts with a ### heading, or the container holds "
                    "one list of '- **Title** – text' items.",
                    token,
                )
            else:
                blocks.append(kid)
        add()
        if not cards:
            raise self.error("A '::: cards' holds no cards.", tokens[i])
        return cards

    def rows(self, i: int, kids: list[int], each: Effect | None = None) -> list[Row]:
        tokens = self.tokens
        if len(kids) != 1 or tokens[kids[0]].type not in LISTS:
            raise self.error(
                "A '::: rows' holds one list of '- **Term** – description' items.", tokens[i]
            )
        rows: list[Row] = []
        for item in children(tokens, kids[0]):
            click = self.click(each)
            with self.deck.at(click):
                term, rest, others = self.item(item, layout_syntax.ROWS)
                description = [Paragraph(rest, click=self.deck.current)] if rest else []
                for block in self.flow(others, in_container=True):
                    if not isinstance(block, TextBlock):
                        raise self.error("The items of '::: rows' hold text only.", tokens[item])
                    description.extend(block.paragraphs)
            rows.append(Row(term, tuple(description), click=click))
        return rows

    def item(self, i: int, name: str) -> tuple[tuple[Run, ...], tuple[Run, ...], list[int]]:
        """The bold start of a list item's first paragraph (its title), the rest of that
        paragraph without its separator, and where the item's other blocks start."""
        tokens = self.tokens
        kids = children(tokens, i)
        runs: list[Run] = []
        if kids and tokens[kids[0]].type == "paragraph_open":
            # In '::: cards', an icon before the title is the card's figure (E15-S03).
            inline = tokens[kids[0] + 1]
            if name == layout_syntax.CARDS:
                inline = icons.without_leading(inline)
            runs = list(self.deck.text_runs(inline))
        bold: list[Run] = []
        for run in runs:
            if run.is_break or not run.bold:
                break
            bold.append(run)
        if not bold:
            raise self.error(
                f"Each item of '::: {name}' starts with **bold** text, its title.", tokens[i]
            )
        title = [replace(r, bold=False) for r in bold]
        title[-1] = replace(title[-1], text=title[-1].text.rstrip().rstrip(":").rstrip())
        rest = runs[len(bold) :]
        if rest and not rest[0].is_break and _is_plain(rest[0]):
            rest[0] = replace(rest[0], text=SEPARATOR.sub("", rest[0].text, count=1))
        return tuple(trim(title)), tuple(trim(rest)), kids[1:]

    def columns(
        self, i: int, kids: list[int], arguments: str, each: Effect | None = None
    ) -> ColumnsBlock:
        """The parts of ``::: columns``, split at ``---``; with ``each``, every column on a
        click of its own."""
        tokens = self.tokens
        parts: list[list[int]] = [[]]
        for kid in kids:
            if tokens[kid].type == "hr":
                parts.append([])
            else:
                parts[-1].append(kid)
        try:
            widths = layout_syntax.columns(
                len(parts), any(not part for part in parts), arguments, FORMAT
            )
        except DocumentConversionError as error:
            raise layout_syntax.at_line(error, self.deck.line(tokens[i])) from None
        click = self.deck.current
        columns: list[tuple[FlowBlock, ...]] = []
        clicks: list[Click | None] = []
        for part in parts:
            clicks.append(self.click(each))
            with self.deck.at(clicks[-1]):
                columns.append(tuple(self.flow(part, in_container=True)))
        built = tuple(clicks) if each is not None else ()
        return ColumnsBlock(tuple(widths), tuple(columns), click=click, clicks=built)


def _is_plain(run: Run) -> bool:
    return not (run.bold or run.italic or run.strike or run.code or run.link or run.mark)


def _is_figure(inline: Token) -> bool:
    """A paragraph that is one ``**strong**`` span, spaces around it aside: a card's figure."""
    kids = [c for c in inline.children or [] if not (c.type == "text" and not c.content.strip())]
    if len(kids) < 3 or kids[0].type != "strong_open" or kids[-1].type != "strong_close":
        return False
    depth = 0
    for n, child in enumerate(kids):
        if child.type == "strong_open":
            depth += 1
        elif child.type == "strong_close":
            depth -= 1
            if depth == 0 and n != len(kids) - 1:
                return False
    return True
