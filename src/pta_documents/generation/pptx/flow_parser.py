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
from pta_documents.generation.common import heading_attributes, layout_syntax, layout_tokens
from pta_documents.generation.pptx.model import (
    CalloutBlock,
    Card,
    CardsBlock,
    Chart,
    Code,
    CodeLinesBlock,
    ColumnsBlock,
    CommentBlock,
    ConclusionBlock,
    Diagram,
    FlowBlock,
    FlowSlide,
    ImageRowBlock,
    Images,
    Item,
    LabelledTag,
    LabelledTagsBlock,
    PanelBlock,
    Paragraph,
    Row,
    RowsBlock,
    Run,
    StatementBlock,
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
        tokens = self.tokens
        token = tokens[i]
        if token.type == CONTAINER_OPEN:
            self.container(i, target)
        elif token.type == "blockquote_open" and ALERT in token.meta:
            important = layout_syntax.is_important(str(token.meta[ALERT]), FORMAT)
            blocks = self.flow(children(tokens, i), in_container=True)
            target.add(CalloutBlock(important, tuple(blocks)))
        elif token.type == "paragraph_open" and (tags := layout_tokens.tags(tokens[i + 1])):
            target.add(TagsBlock(tuple(tags)))
        elif (
            token.type in LISTS
            and target.in_container
            and (labelled := layout_tokens.labelled_tags(tokens, i)) is not None
        ):
            tagged = tuple(LabelledTag(label, self.inline_runs(rest)) for label, rest in labelled)
            target.add(LabelledTagsBlock(tagged))
        elif token.type == "table_open":
            items: list[Item] = []
            self.deck.table(tokens, i, items, labels=True)
            self.items(items, target)
        elif token.type == "hr":
            pass
        else:
            items = []
            self.deck.block(tokens, i, items, depth=0, italic=False)
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
                    target.add(CodeLinesBlock(item.lines, item.spans))
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
        match name:
            case layout_syntax.CARDS:
                target.add(CardsBlock(tuple(self.cards(i, kids))))
            case layout_syntax.ROWS:
                target.add(RowsBlock(tuple(self.rows(i, kids))))
            case layout_syntax.PANEL:
                blocks = self.flow(kids, in_container=True)
                target.add(PanelBlock(arguments == "dark", tuple(blocks)))
            case layout_syntax.COLUMNS:
                target.add(self.columns(i, kids, arguments))
            case layout_syntax.STATEMENT:
                if not kids or tokens[kids[0]].type != "paragraph_open":
                    raise self.error(
                        "A '::: statement' starts with a paragraph, its statement.", token
                    )
                target.add(StatementBlock(self.paragraph_runs(kids[0])))
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
                self.conclusion = ConclusionBlock(self.text_only(kids, name, token))
            case layout_syntax.COMMENT:
                paragraphs = self.text_only(kids, name, token)
                if not target.blocks or isinstance(target.blocks[-1], CommentBlock):
                    raise self.error(
                        "A '::: comment' comments on the block right before it; put it after "
                        "a paragraph, list, table, image or container.",
                        token,
                    )
                target.add(CommentBlock(paragraphs))
            case _:  # pragma: no cover - layout_syntax.check refused it before
                layout_syntax.check_container(name, arguments, FORMAT)

    def cards(self, i: int, kids: list[int]) -> list[Card]:
        """A list of ``**Title** – text`` items, or a ``###`` heading before each card's blocks."""
        tokens = self.tokens
        if len(kids) == 1 and tokens[kids[0]].type in LISTS:
            cards: list[Card] = []
            for item in children(tokens, kids[0]):
                title, rest, others = self.item(item, layout_syntax.CARDS)
                body = self.flow(others, in_container=True)
                if rest:
                    body.insert(0, TextBlock((Paragraph(rest),)))
                cards.append(Card(title, None, tuple(body)))
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
            body = self.flow(rest, in_container=True)
            cards.append(Card(self.paragraph_runs(heading), figure, tuple(body)))

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

    def rows(self, i: int, kids: list[int]) -> list[Row]:
        tokens = self.tokens
        if len(kids) != 1 or tokens[kids[0]].type not in LISTS:
            raise self.error(
                "A '::: rows' holds one list of '- **Term** – description' items.", tokens[i]
            )
        rows: list[Row] = []
        for item in children(tokens, kids[0]):
            term, rest, others = self.item(item, layout_syntax.ROWS)
            description: list[Paragraph] = [Paragraph(rest)] if rest else []
            for block in self.flow(others, in_container=True):
                if not isinstance(block, TextBlock):
                    raise self.error("The items of '::: rows' hold text only.", tokens[item])
                description.extend(block.paragraphs)
            rows.append(Row(term, tuple(description)))
        return rows

    def item(self, i: int, name: str) -> tuple[tuple[Run, ...], tuple[Run, ...], list[int]]:
        """The bold start of a list item's first paragraph (its title), the rest of that
        paragraph without its separator, and where the item's other blocks start."""
        tokens = self.tokens
        kids = children(tokens, i)
        runs: list[Run] = []
        if kids and tokens[kids[0]].type == "paragraph_open":
            runs = list(self.paragraph_runs(kids[0]))
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

    def columns(self, i: int, kids: list[int], arguments: str) -> ColumnsBlock:
        """The parts of ``::: columns``, split at ``---``."""
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
        columns = tuple(tuple(self.flow(part, in_container=True)) for part in parts)
        return ColumnsBlock(tuple(widths), columns)


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
