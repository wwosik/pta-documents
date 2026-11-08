"""The PTA slide kinds of a ``##`` heading (E04-S04): agenda, interim conclusion, quote, contact.

``## Agenda {.agenda}`` takes one list (or none: the chapters of the deck), ``{.interim}`` no
content (nor does a break, ``{.break dauer=15}``, E16-S02, on the same layouts), ``{.quote}``
one paragraph (its source), ``{.contact}`` one ``###`` per person with a photo and lines for
function, e-mail and phone. Each picks its PTA layout itself; ``layout="…"`` may choose another
of the same kind. Mistakes raise ``DocumentConversionError``
with the line in front, like ``layout_syntax.check``.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Final

from markdown_it.token import Token

from pta_documents.design import slides as design
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import (
    heading_attributes,
    html,
    layout_syntax,
    training_schedule,
)
from pta_documents.generation.pptx.flow_parser import LISTS, block_end, children
from pta_documents.generation.pptx.model import (
    AgendaSlide,
    ContactSlide,
    Image,
    InterimSlide,
    Item,
    Paragraph,
    Person,
    QuoteSlide,
    Run,
    Separator,
    Slide,
    plain_text,
    trim,
)

if TYPE_CHECKING:
    from pta_documents.generation.pptx.parser import DeckParser

FORMAT: Final = DocumentFormat.PPTX
_BREAKS: Final = ("softbreak", "hardbreak")


def _key(title: str) -> str:
    """A title to compare an agenda item with a chapter: case and spacing aside."""
    return " ".join(title.split()).casefold()


class KindReader:
    def __init__(self, deck: DeckParser) -> None:
        self.deck = deck
        self.tokens = deck.tokens

    def error(self, reason: str, token: Token) -> DocumentConversionError:
        return layout_syntax.at_line(DocumentConversionError(FORMAT, reason), self.deck.line(token))

    def slide(
        self,
        kind: str,
        title: tuple[Run, ...],
        heading: Token,
        layout: str | None,
        start: int,
        end: int,
    ) -> Slide:
        line = self.deck.line(heading)
        family = design.KIND_LAYOUTS[kind]
        if layout is not None and layout not in family:
            valid = ", ".join(f"'{name}'" for name in family)
            raise self.error(
                f"The slide kind .{kind} goes on its own PTA layouts, not on '{layout}'. "
                f"Valid layouts: {valid}.",
                heading,
            )
        blocks = self.blocks(start, end)
        match kind:
            case heading_attributes.AGENDA:
                return self.agenda(title, line, heading, layout, blocks)
            case heading_attributes.INTERIM:
                if blocks:
                    raise self.error(
                        "An interim conclusion {.interim} is its heading alone; put the content "
                        "on a slide of its own.",
                        self.tokens[blocks[0]],
                    )
                return InterimSlide(title, line, layout or family[0])
            case heading_attributes.BREAK:
                if blocks:
                    raise self.error(
                        "A break {.break} is its heading alone ('## Pause {.break dauer=15}'); "
                        "put the content on a slide of its own.",
                        self.tokens[blocks[0]],
                    )
                _, attributes = layout_syntax.without_attributes(self.tokens[start - 2], 2, FORMAT)
                minutes = attributes.duration if attributes is not None else None
                return InterimSlide((*title, Run(f" · {minutes} min")), line, layout or family[0])
            case heading_attributes.QUOTE:
                return self.quote(title, line, layout or family[0], blocks)
            case _:
                return self.contact(title, line, heading, layout, blocks)

    def blocks(self, start: int, end: int) -> list[int]:
        """Where the blocks of the section start, HTML comments left out."""
        result: list[int] = []
        i = start
        while i < end:
            token = self.tokens[i]
            if not (token.type == "html_block" and html.is_comment(token.content)):
                result.append(i)
            i = block_end(self.tokens, i)
        return result

    # ------------------------------------------------------------------ agenda

    def agenda(
        self,
        title: tuple[Run, ...],
        line: int | None,
        heading: Token,
        layout: str | None,
        blocks: list[int],
    ) -> AgendaSlide:
        tokens = self.tokens
        if not blocks:
            items = self.chapters()
            if not items:
                raise self.error(
                    "An agenda {.agenda} takes one list of its items, or, without one, the "
                    "chapters ('#' headings after the title); the deck has none.",
                    heading,
                )
        else:
            if len(blocks) != 1 or tokens[blocks[0]].type not in LISTS:
                raise self.error(
                    "An agenda {.agenda} holds one list of its items and nothing else (or "
                    "nothing: then its items are the chapters of the deck).",
                    tokens[blocks[0]],
                )
            items = []
            for item in children(tokens, blocks[0]):
                kids = children(tokens, item)
                if len(kids) != 1 or tokens[kids[0]].type != "paragraph_open":
                    raise self.error("Each agenda item is one line of text.", tokens[item])
                items.append(self.deck.text_runs(tokens[kids[0] + 1]))
        items, breaks = self.timed(items)
        if len(items) > design.AGENDA_ITEMS:
            counted = f" ({breaks} of them breaks)" if breaks else ""
            raise self.error(
                f"An agenda holds {design.AGENDA_ITEMS} items at most, this one "
                f"{len(items)}{counted}. Split it into two agenda slides.",
                heading,
            )
        short = len(items) <= design.AGENDA_SHORT_ITEMS
        chosen = layout or (design.LAYOUTS.agenda_short if short else design.LAYOUTS.agenda_long)
        if chosen == design.LAYOUTS.agenda_short and not short:
            raise self.error(
                f"The layout '{chosen}' holds {design.AGENDA_SHORT_ITEMS} items, the agenda "
                f'{len(items)}. Leave out layout="…".',
                heading,
            )
        return AgendaSlide(title, line, tuple(items), chosen)

    def timed(self, items: list[tuple[Run, ...]]) -> tuple[list[tuple[Run, ...]], int]:
        """With ``beginn:`` and a schedule (E16-S02): each item that names a chapter with its
        start in front (``09:00 Einführung``), each break an item of its own before the first
        chapter after it; and the number of breaks added. Without, ``items`` as they are."""
        schedule = self.deck.schedule
        if schedule is None or schedule.begin is None:
            return items, 0
        starts = {
            _key(e.title): e.start
            for e in schedule.entries
            if e.kind is training_schedule.EntryKind.CHAPTER
        }
        timed: list[tuple[tuple[Run, ...], int | None]] = []
        for item in items:
            start = starts.get(_key(plain_text(item)))
            runs = item if start is None else (Run(schedule.time(start) + " "), *item)
            timed.append((runs, start))
        if all(start is None for _, start in timed):
            return items, 0
        for pause in schedule.breaks:
            runs = (Run(f"{schedule.time(pause.start)} {pause.title}"),)
            at = next(
                (
                    n
                    for n, (_, start) in enumerate(timed)
                    if start is not None and start >= pause.end
                ),
                None,
            )
            if at is None:
                at = 1 + max(n for n, (_, start) in enumerate(timed) if start is not None)
            timed.insert(at, (runs, None))
        return [runs for runs, _ in timed], len(schedule.breaks)

    def chapters(self) -> list[tuple[Run, ...]]:
        """The ``#`` headings of the deck after the first (the title slide), the closing slide
        aside."""
        result: list[tuple[Run, ...]] = []
        tokens = self.tokens
        first = True
        for i, token in enumerate(tokens):
            if token.type != "heading_open" or token.tag != "h1" or token.level != 0:
                continue
            inline, attributes = layout_syntax.without_attributes(tokens[i + 1], 1, FORMAT)
            if attributes is not None and attributes.closing:
                continue
            if first:
                first = False
                continue
            result.append(self.deck.text_runs(inline))
        return result

    # ------------------------------------------------------------------ quote

    def quote(
        self, title: tuple[Run, ...], line: int | None, layout: str, blocks: list[int]
    ) -> QuoteSlide:
        tokens = self.tokens
        if not blocks:
            return QuoteSlide(title, line, (), layout)
        if len(blocks) != 1 or tokens[blocks[0]].type != "paragraph_open":
            raise self.error(
                "A quote {.quote} takes one paragraph under it at most: its source "
                "(— Name, Funktion).",
                tokens[blocks[-1] if len(blocks) > 1 else blocks[0]],
            )
        return QuoteSlide(title, line, self.deck.text_runs(tokens[blocks[0] + 1]), layout)

    # ------------------------------------------------------------------ contact

    def contact(
        self,
        title: tuple[Run, ...],
        line: int | None,
        heading: Token,
        layout: str | None,
        blocks: list[int],
    ) -> ContactSlide:
        tokens = self.tokens
        persons: list[Person] = []
        text: list[Paragraph] = []
        groups: list[tuple[int, list[int]]] = []
        for block in blocks:
            token = tokens[block]
            if token.type == "heading_open" and token.tag == "h3":
                groups.append((block, []))
            elif not groups:
                raise self.error(
                    "A contact slide {.contact} holds a ### heading per person, with the "
                    "person's photo and lines under it.",
                    token,
                )
            else:
                groups[-1][1].append(block)
        if not groups:
            raise self.error(
                "A contact slide {.contact} holds a ### heading per person (one to "
                f"{design.CONTACT_PERSONS}).",
                heading,
            )
        if len(groups) > design.CONTACT_PERSONS:
            raise self.error(
                f"A contact slide holds {design.CONTACT_PERSONS} persons at most, this one "
                f"{len(groups)}. Split it into two contact slides.",
                heading,
            )
        for name, person_blocks in groups:
            person, person_text = self.person(name, person_blocks)
            persons.append(person)
            text.extend(person_text)
        if text and len(persons) > 1:
            raise self.error(
                "Text beside the contact lines goes on a contact slide of one person "
                "('Kontakt mit Text'); this one has "
                f"{len(persons)}.",
                heading,
            )
        default = design.LAYOUTS.contact_text if text else design.CONTACT_LAYOUTS[len(persons) - 1]
        chosen = layout or default
        if chosen == design.LAYOUTS.contact_text:
            fits = len(persons) == 1
        else:
            fits = not text and design.CONTACT_LAYOUTS.index(chosen) + 1 >= len(persons)
        if not fits:
            raise self.error(
                f"The layout '{chosen}' has no place for {len(persons)} persons"
                f"{' and text' if text else ''}; '{default}' has. Leave out layout=\"…\".",
                heading,
            )
        return ContactSlide(title, line, tuple(persons), tuple(text), chosen)

    def person(self, heading: int, blocks: list[int]) -> tuple[Person, list[Paragraph]]:
        """A person: the photo, then one paragraph of contact lines (function, e-mail, phone,
        in any order); what follows is text (``Kontakt mit Text``)."""
        tokens = self.tokens
        name = self.deck.text_runs(tokens[heading + 1])
        who = plain_text(name)
        photo: Image | None = None
        lines: dict[str, tuple[Run, ...]] = {}
        read_lines = False
        text: list[Paragraph] = []
        for block in blocks:
            token = tokens[block]
            if not read_lines and token.type == "paragraph_open":
                inline = tokens[block + 1]
                for part in _lines(inline):
                    images = [c for c in part if c.type == "image"]
                    if images:
                        if photo is not None or len(images) > 1 or _has_text(part):
                            raise self.error(
                                f"The person '{who}' has one photo at most, on a line of its own.",
                                token,
                            )
                        photo = self.deck.image(images[0], inline)
                        continue
                    runs = self.deck.text_runs(inline.copy(children=part))
                    if not runs:
                        continue
                    kind = _line_kind(plain_text(runs))
                    if kind in lines:
                        raise self.error(
                            f"The person '{who}' has two lines of the kind {kind}: one each for "
                            "function, e-mail (with @) and phone (starts with + or a digit).",
                            token,
                        )
                    lines[kind] = _mail_link(runs) if kind == "e-mail" else runs
                read_lines = bool(lines)
                continue
            items: list[Item] = []
            self.deck.block(tokens, block, items, depth=0, italic=False)
            for item in items:
                if isinstance(item, Separator):
                    continue
                if not isinstance(item, Paragraph):
                    raise self.error(
                        "A contact slide takes text beside the contact lines only (paragraphs "
                        "and lists), no tables, images, code or charts.",
                        token,
                    )
                text.append(item)
        person = Person(
            name,
            photo,
            lines.get("function", ()),
            lines.get("e-mail", ()),
            lines.get("phone", ()),
        )
        return person, text


def _lines(inline: Token) -> list[list[Token]]:
    """The inline children of a paragraph, split at its line breaks."""
    result: list[list[Token]] = [[]]
    for child in inline.children or []:
        if child.type in _BREAKS:
            result.append([])
        else:
            result[-1].append(child)
    return [part for part in result if part]


def _has_text(part: list[Token]) -> bool:
    return any(c.type != "image" and not (c.type == "text" and not c.content.strip()) for c in part)


def _line_kind(text: str) -> str:
    """A contact line by its pattern: e-mail (has an @), phone (starts with + or a digit),
    else function."""
    if "@" in text:
        return "e-mail"
    if text[:1] == "+" or text[:1].isdigit():
        return "phone"
    return "function"


def _mail_link(runs: tuple[Run, ...]) -> tuple[Run, ...]:
    """An e-mail line as a ``mailto:`` link, unless it is a link already."""
    if any(r.link for r in runs):
        return runs
    address = plain_text(runs)
    return tuple(trim([replace(r, link=f"mailto:{address}") for r in runs]))
