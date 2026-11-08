"""The schedule of a training from the lengths of its slides (E16-S02).

``## Folie {dauer=5}`` plans five minutes for a slide, ``# Kapitel {dauer=45}`` 45 for a
chapter, whose slides without a length of their own share what is left evenly; ``## Pause
{.break dauer=15}`` is a break. The front matter of a deck may give the start (``beginn:
09:00``) and the planned length (``laenge: 4h``). From this ``build`` makes a ``Schedule``:
an entry per chapter, slide and break with its start and length. A slide without a length in
a chapter without one counts ``MINUTES_PER_SLIDE`` (the rule of thumb of ``check``) and is
reported (``schedule-missing``); the slides of a split slide count once (the schedule is made
from the headings, not from the slides written). The schedule ends at the closing slide
(``{.closing}``) or at the backup (``{.backup}``, E16-S04): what comes after it is not planned
(``backup.check`` rejects a break or a ``dauer`` there).

A deck has a schedule only when it says something about time: a ``dauer``, a break,
``beginn:`` or ``laenge:``. The deck uses it for the agenda (clock times, the breaks as items)
and the speaker notes of the trainer version ("Geplant: 09:20–09:25 (5 min)");
``./run.sh schedule`` writes it as a Word table (``to_markdown``).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Final

from markdown_it.token import Token

from pta_documents.design.variants import Language
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common import audience as audiences
from pta_documents.generation.common import durations, heading_attributes, layout_syntax
from pta_documents.generation.common.result import NoteCodes, Notes
from pta_documents.generation.common.style_rules import inline_text
from pta_documents.markdown.document import MarkdownDocument
from pta_documents.markdown.front_matter import FrontMatter, Keys
from pta_documents.markdown.parser import line_of, parse

MINUTES_PER_SLIDE: Final = 2
"""What a slide without a length counts: the rule of thumb of ``check`` (E08-S02)."""
ESTIMATE_TOLERANCE: Final = 0.5
"""``schedule-estimate``: the planned talking time is more than half off the rule of thumb."""
WORD_TEMPLATE: Final = "hoch-ohne-deckblatt"
"""The PTA Word template of the schedule document."""


class EntryKind(StrEnum):
    CHAPTER = "chapter"
    SLIDE = "slide"
    BREAK = "break"


@dataclass(frozen=True)
class ScheduleTexts:
    """The words of the schedule in a language of the deck."""

    planned: str
    start: str
    end: str
    length: str
    item: str
    notes: str
    total: str
    title: str
    begins: str
    planned_length: str
    assumed: str


TEXTS: Final = {
    Language.DE: ScheduleTexts(
        planned="Geplant",
        start="Von",
        end="Bis",
        length="Dauer",
        item="Kapitel/Folie",
        notes="Notizen",
        total="Summe",
        title="Zeitplan",
        begins="Beginn",
        planned_length="geplante Länge",
        assumed="Folien ohne Angabe sind mit je {0} min angesetzt (≈).",
    ),
    Language.EN: ScheduleTexts(
        planned="Planned",
        start="From",
        end="To",
        length="Duration",
        item="Chapter/slide",
        notes="Notes",
        total="Total",
        title="Schedule",
        begins="Start",
        planned_length="planned length",
        assumed="Slides without a length count {0} min each (≈).",
    ),
}


@dataclass(frozen=True)
class ScheduleEntry:
    kind: EntryKind
    title: str
    """The heading as it reads, without its attributes."""
    start: int
    """Minutes after the start of the schedule."""
    minutes: int
    line: int | None
    heading: int
    """The index of the ``heading_open`` token in the tokens ``build`` was given."""
    assumed: bool = False
    """A slide without a length: ``MINUTES_PER_SLIDE``."""

    @property
    def end(self) -> int:
        return self.start + self.minutes


@dataclass(frozen=True)
class Schedule:
    entries: tuple[ScheduleEntry, ...]
    total: int
    """The planned minutes, breaks included."""
    begin: int | None = None
    """``beginn:`` in minutes after midnight; None: times are offsets (``+0:15``)."""
    length: int | None = None
    """``laenge:`` in minutes."""
    language: Language = Language.DE
    overruns: tuple[tuple[ScheduleEntry, int], ...] = field(default=())
    """Chapters whose slides need more than the chapter's ``dauer``, with that ``dauer``."""
    title: str | None = None
    """The title of the deck: its first ``#`` heading, or ``titel:`` (``deck_schedule``)."""

    @property
    def texts(self) -> ScheduleTexts:
        return TEXTS[self.language]

    @property
    def missing(self) -> tuple[ScheduleEntry, ...]:
        """The slides without a length, counted with ``MINUTES_PER_SLIDE``."""
        return tuple(e for e in self.entries if e.assumed)

    @property
    def breaks(self) -> tuple[ScheduleEntry, ...]:
        return tuple(e for e in self.entries if e.kind is EntryKind.BREAK)

    @property
    def talking(self) -> int:
        """The planned minutes without the breaks."""
        return self.total - sum(e.minutes for e in self.breaks)

    def at(self, heading: int) -> ScheduleEntry | None:
        """The entry of the heading at ``tokens[heading]``."""
        return next((e for e in self.entries if e.heading == heading), None)

    def time(self, minutes: int) -> str:
        """``09:20`` with ``beginn:``, else ``+0:20``."""
        if self.begin is None:
            return durations.offset(minutes)
        return durations.clock(self.begin + minutes)

    def span(self, entry: ScheduleEntry) -> str:
        """``09:20–09:25 (5 min)``."""
        return f"{self.time(entry.start)}–{self.time(entry.end)} ({entry.minutes} min)"

    def planned(self, entry: ScheduleEntry) -> str:
        """The first line of the trainer's speaker notes: ``Geplant: 09:20–09:25 (5 min)``."""
        return f"{self.texts.planned}: {self.span(entry)}"

    def to_markdown(self) -> str:
        """The schedule as a Markdown table: From | To | Duration | Chapter/slide | Notes (empty,
        for the trainer), chapters bold, breaks marked (``==…==``), the total last."""
        texts = self.texts
        lines = [
            f"| {texts.start} | {texts.end} | {texts.length} | {texts.item} | {texts.notes} |",
            "| --- | --- | --- | --- | --- |",
        ]
        for entry in self.entries:
            title = escape(entry.title)
            if entry.kind is EntryKind.CHAPTER:
                title = f"**{title}**"
            elif entry.kind is EntryKind.BREAK:
                title = f"=={title}=="
            length = f"≈ {entry.minutes} min" if entry.assumed else f"{entry.minutes} min"
            lines.append(
                f"| {self.time(entry.start)} | {self.time(entry.end)} | {length} | {title} |  |"
            )
        lines.append(f"|  |  | **{self.total} min** | **{texts.total}** |  |")
        return "\n".join(lines) + "\n"

    def add_notes(self, notes: Notes) -> None:
        """``schedule-missing`` for slides without a length, ``schedule-length`` for a chapter
        its slides overrun and for a total other than ``laenge:``."""
        missing = self.missing
        if missing:
            count = "1 slide has" if len(missing) == 1 else f"{len(missing)} slides have"
            notes.add(
                NoteCodes.SCHEDULE_MISSING,
                missing[0].line,
                f"{count} no 'dauer'; the schedule assumes {MINUTES_PER_SLIDE} min each. Give "
                "each slide its minutes ('## Folie {dauer=5}') or its chapter ('# Kapitel "
                "{dauer=45}').",
            )
        for chapter, planned in self.overruns:
            notes.add(
                NoteCodes.SCHEDULE_LENGTH,
                chapter.line,
                f"The chapter '{chapter.title}' plans {planned} min, its slides sum to "
                f"{chapter.minutes} min.",
            )
        if self.length is not None and self.length != self.total:
            notes.add(
                NoteCodes.SCHEDULE_LENGTH,
                None,
                f"Planned {self.length} min ('{Keys.LENGTH}:'), slides sum to {self.total} min.",
            )

    def estimate_note(self, estimate: int, notes: Notes) -> None:
        """``schedule-estimate`` when the planned talking time is more than half off
        ``estimate`` (``check``'s rule of thumb) and at least one slide has a length."""
        if len(self.missing) == sum(1 for e in self.entries if e.kind is not EntryKind.CHAPTER):
            return
        if estimate <= 0 or abs(self.talking - estimate) <= ESTIMATE_TOLERANCE * estimate:
            return
        notes.add(
            NoteCodes.SCHEDULE_ESTIMATE,
            None,
            f"The schedule plans {self.talking} min of talking (breaks aside), the rule of thumb "
            f"about {estimate} min (2 per content slide plus the notes); check the 'dauer' "
            "values or the amount of slides.",
        )


def escape(text: str) -> str:
    """``text`` as literal Markdown in a table cell."""
    return "".join("\\" + c if c in "\\`*_[]|=<>~" else c for c in text)


@dataclass(frozen=True)
class _Slide:
    """A ``##`` heading of the schedule."""

    heading: int
    title: str
    line: int | None
    duration: int | None
    is_break: bool

    def entry(self, start: int, minutes: int, assumed: bool) -> ScheduleEntry:
        kind = EntryKind.BREAK if self.is_break else EntryKind.SLIDE
        return ScheduleEntry(kind, self.title, start, minutes, self.line, self.heading, assumed)


@dataclass
class _Group:
    """A ``#`` heading (or the start of the deck) and the ``##`` slides under it."""

    heading: int | None
    title: str
    line: int | None
    duration: int | None
    is_title: bool
    slides: list[_Slide] = field(default_factory=list)


def _heading(
    tokens: Sequence[Token], i: int, format: DocumentFormat
) -> tuple[str, heading_attributes.HeadingAttributes | None]:
    level = int(tokens[i].tag[1])
    inline, attributes = layout_syntax.without_attributes(tokens[i + 1], level, format)
    return inline_text(inline).strip(), attributes


def build(
    tokens: Sequence[Token],
    format: DocumentFormat = DocumentFormat.PPTX,
    line_offset: int = 0,
    begin: int | None = None,
    length: int | None = None,
    language: Language = Language.DE,
) -> Schedule | None:
    """The schedule of the level-0 ``#``/``##`` headings of ``tokens`` (checked by
    ``layout_syntax.check`` before); None when the deck says nothing about time."""
    groups: list[_Group] = []
    timed = begin is not None or length is not None
    seen_title = False
    for i, token in enumerate(tokens):
        if token.type != "heading_open" or token.level != 0 or token.tag not in ("h1", "h2"):
            continue
        title, attributes = _heading(tokens, i, format)
        line = line_of(token, line_offset)
        duration = attributes.duration if attributes is not None else None
        timed |= duration is not None
        if token.tag == "h1":
            if attributes is not None and (attributes.closing or attributes.backup):
                break  # nothing behind the closing slide is planned, the backup neither
            groups.append(_Group(i, title, line, duration, not seen_title))
            seen_title = True
            continue
        if not groups:
            groups.append(_Group(None, "", None, None, True))
            seen_title = True
        is_break = attributes is not None and attributes.kind == heading_attributes.BREAK
        timed |= is_break
        groups[-1].slides.append(_Slide(i, title, line, duration, is_break))
    if not timed:
        return None
    entries: list[ScheduleEntry] = []
    overruns: list[tuple[ScheduleEntry, int]] = []
    now = 0
    for group in groups:
        body = list(group.slides)
        trailing: list[_Slide] = []
        while body and body[-1].is_break:
            trailing.insert(0, body.pop())
        start = now
        planned = group.duration
        content = [s for s in body if not s.is_break]
        given = sum(s.duration or 0 for s in content)
        open_count = sum(1 for s in content if s.duration is None)
        share, extra = divmod(max((planned or 0) - given, 0), open_count or 1)
        slides: list[ScheduleEntry] = []
        shared = talk = 0
        for slide in body:
            minutes, assumed = slide.duration, False
            if minutes is None and planned is not None:
                minutes = share + (1 if shared < extra else 0)
                shared += 1
            elif minutes is None:
                minutes, assumed = MINUTES_PER_SLIDE, True
            slides.append(slide.entry(now, minutes, assumed))
            now += minutes
            talk += 0 if slide.is_break else minutes
        if planned is not None and talk < planned:
            now += planned - talk  # the chapter's time left after its slides
        if group.heading is None:
            entries.extend(slides)
        elif group.is_title and not body:
            if now > start:
                entries.append(
                    ScheduleEntry(
                        EntryKind.SLIDE, group.title, start, now - start, group.line, group.heading
                    )
                )
        else:
            chapter = ScheduleEntry(
                EntryKind.CHAPTER, group.title, start, now - start, group.line, group.heading
            )
            if planned is not None and talk > planned:
                overruns.append((chapter, planned))
            if not group.is_title:
                entries.append(chapter)
            entries.extend(slides)
        for pause in trailing:
            entries.append(pause.entry(now, pause.duration or 0, False))
            now += pause.duration or 0
    title = next((g.title for g in groups if g.is_title and g.heading is not None), None)
    return Schedule(tuple(entries), now, begin, length, language, tuple(overruns), title)


def deck_schedule(
    document: MarkdownDocument, audience: audiences.Audience | None = None
) -> Schedule | None:
    """The schedule of a deck in the version for ``audience`` (default: ``fassung:``, else
    ``kunde``), with ``beginn:``, ``laenge:`` and ``sprache:`` of its front matter. Raises
    ``DocumentConversionError`` for mistakes, as generating would."""
    format = DocumentFormat.PPTX
    front = FrontMatter.read(document.text, format)
    tokens = parse(front.body)
    layout_syntax.check(tokens, format, front.body_line)
    chosen = audiences.resolve(front, audience)
    tokens = audiences.filter_tokens(tokens, chosen, None, format, front.body_line)
    value = front.get(Keys.BEGIN)
    begin = (
        durations.parse_clock(value, f"The front matter key '{Keys.BEGIN}' ('{value}')", format)
        if value is not None
        else None
    )
    value = front.get(Keys.LENGTH)
    length = (
        durations.parse_minutes(value, f"The front matter key '{Keys.LENGTH}' ('{value}')", format)
        if value is not None
        else None
    )
    value = front.get(Keys.LANGUAGE)
    language = Language.parse(value, format) if value is not None else Language.DE
    schedule = build(tokens, format, front.body_line, begin, length, language)
    if schedule is not None and (title := front.get(Keys.TITLE)) is not None:
        schedule = replace(schedule, title=title)
    return schedule


def schedule_document(
    schedule: Schedule, audience: audiences.Audience = audiences.Audience.TRAINER
) -> str:
    """The Markdown of the schedule document (``./run.sh schedule``): the PTA Word template
    ``hoch-ohne-deckblatt``, a heading, start, planned length and total, the table; marked
    ``intern`` unless it is the customer's version."""
    texts = schedule.texts
    title = schedule.title
    heading = f"{texts.title}: {title}" if title else texts.title
    front = [
        "---",
        f"{Keys.TEMPLATE}: {WORD_TEMPLATE}",
        f'{Keys.TITLE}: "{heading}"',
        f"{Keys.LANGUAGE}: {schedule.language.value}",
    ]
    if audience is not audiences.Audience.KUNDE:
        front.append(f"{Keys.MARKING}: intern")
    front.append("---")
    facts: list[str] = []
    if schedule.begin is not None:
        facts.append(f"{texts.begins} {durations.clock(schedule.begin)}")
    if schedule.length is not None:
        facts.append(f"{texts.planned_length} {schedule.length} min")
    facts.append(f"{texts.total} {schedule.total} min")
    parts = [
        "\n".join(front),
        f"# {escape(heading)}",
        " · ".join(facts),
        schedule.to_markdown().rstrip("\n"),
    ]
    if schedule.missing:
        parts.append(texts.assumed.format(MINUTES_PER_SLIDE))
    return "\n\n".join(parts) + "\n"
