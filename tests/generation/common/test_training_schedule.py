"""E16-S02: the training schedule from ``dauer=…``, ``{.break}``, ``beginn:`` and ``laenge:``."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

from pta_documents.conversions.docx import DocxConverter
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import heading_attributes, layout_syntax
from pta_documents.generation.common.audience import Audience
from pta_documents.generation.common.check import DeckStats, check
from pta_documents.generation.common.result import NoteCodes, Notes
from pta_documents.generation.common.training_schedule import (
    EntryKind,
    Schedule,
    build,
    deck_schedule,
    schedule_document,
)
from pta_documents.markdown import MarkdownDocument
from pta_documents.markdown.parser import parse
from tests.conftest import REPO_ROOT, REVIEW_DIR
from tests.generation.docx.conftest import open_docx

PPTX: Final = DocumentFormat.PPTX
DECK: Final = """---
beginn: 09:00
laenge: 1h30
---
# Kurs

## Agenda {.agenda dauer=5}

# Einführung {dauer=30}

## Ziele {dauer=10}

Text

## Ablauf

Text

## Begriffe

Text

## Pause {.break dauer=15}

# Praxis

## Übung {dauer=1h30}

Text

# Danke {.closing}

## Nach dem Ende

Text
"""


def schedule_of(markdown: str, audience: Audience | None = None) -> Schedule:
    schedule = deck_schedule(MarkdownDocument(markdown), audience)
    assert schedule is not None
    return schedule


def rows(schedule: Schedule) -> list[tuple[str, str, str, int]]:
    return [(e.kind.value, e.title, schedule.time(e.start), e.minutes) for e in schedule.entries]


# ---------------------------------------------------------------------- reading


@pytest.mark.parametrize(
    ("block", "minutes"),
    [("{dauer=5}", 5), ('{dauer="5"}', 5), ("{dauer=1h30}", 90), ("{.dark dauer=4h}", 240)],
)
def test_dauer_is_read_with_or_without_quotes(block: str, minutes: int) -> None:
    text, attributes = heading_attributes.split(f"Folie {block}", PPTX)
    assert text == "Folie"
    assert attributes is not None and attributes.duration == minutes


def test_a_break_is_a_slide_kind_with_its_length() -> None:
    _, attributes = heading_attributes.split("Pause {.break dauer=15}", PPTX)
    assert attributes is not None
    assert attributes.kind == heading_attributes.BREAK and attributes.duration == 15


@pytest.mark.parametrize(
    ("markdown", "message"),
    [
        (
            "# Deck\n\n## Folie {dauer=abc}\n",
            "Line 3: The heading attribute dauer=abc is no length",
        ),
        ("# Deck\n\n## Folie {dauer=0}\n", "like '5', '90', '4h' or '1h30'"),
        ("# Deck\n\n## Pause {.break}\n", "Line 3: The break in '{.break}' needs its length"),
        ("# Deck\n\n# Pause {.break dauer=5}\n", "goes on a '##' heading"),
        ("# Deck\n\n## Pause {.agenda .break dauer=5}\n", "a slide is one of them at most"),
        ("# Deck\n\n# Danke {.closing dauer=5}\n", "comes after the schedule; leave out dauer"),
    ],
)
def test_wrong_lengths_and_breaks_raise_with_line_and_example(markdown: str, message: str) -> None:
    with pytest.raises(DocumentConversionError) as caught:
        layout_syntax.check(parse(markdown), PPTX)
    assert message in caught.value.reason


def test_other_braces_without_quotes_stay_text() -> None:
    assert heading_attributes.split("Mengen {a=b}", PPTX) == ("Mengen {a=b}", None)


# ---------------------------------------------------------------------- the schedule


def test_a_deck_without_anything_about_time_has_no_schedule() -> None:
    assert build(parse("# Deck\n\n## Folie\n\nText\n")) is None
    assert deck_schedule(MarkdownDocument("# Deck\n\n## Folie\n")) is None


def test_slides_chapters_and_breaks_follow_each_other() -> None:
    schedule = schedule_of(DECK)
    assert rows(schedule) == [
        ("slide", "Agenda", "09:00", 5),
        ("chapter", "Einführung", "09:05", 30),
        ("slide", "Ziele", "09:05", 10),
        ("slide", "Ablauf", "09:15", 10),
        ("slide", "Begriffe", "09:25", 10),
        ("break", "Pause", "09:35", 15),
        ("chapter", "Praxis", "09:50", 90),
        ("slide", "Übung", "09:50", 90),
    ]
    assert schedule.total == 140 and schedule.talking == 125
    assert schedule.length == 90 and schedule.title == "Kurs"
    assert schedule.missing == ()


def test_slides_without_a_length_share_what_their_chapter_has_left() -> None:
    schedule = schedule_of("# K\n\n# Teil {dauer=10}\n\n## A {dauer=3}\n\n## B\n\n## C\n\n## D\n")
    assert [e.minutes for e in schedule.entries] == [10, 3, 3, 2, 2]


def test_a_chapter_without_slides_takes_its_own_length() -> None:
    schedule = schedule_of("# K\n\n# Teil {dauer=10}\n\n# Weiter\n\n## A {dauer=3}\n")
    assert rows(schedule) == [
        ("chapter", "Teil", "+0:00", 10),
        ("chapter", "Weiter", "+0:10", 3),
        ("slide", "A", "+0:10", 3),
    ]


def test_a_chapter_with_time_left_ends_after_it() -> None:
    schedule = schedule_of(
        "# K\n\n# Teil {dauer=10}\n\n## A {dauer=3}\n\n# Weiter\n\n## B {dauer=2}\n"
    )
    assert [(e.title, e.start) for e in schedule.entries] == [
        ("Teil", 0),
        ("A", 0),
        ("Weiter", 10),
        ("B", 10),
    ]


def test_a_break_inside_a_chapter_does_not_eat_its_length() -> None:
    schedule = schedule_of(
        "# K\n\n# Teil {dauer=10}\n\n## A\n\n## Pause {.break dauer=5}\n\n## B\n"
    )
    assert rows(schedule) == [
        ("chapter", "Teil", "+0:00", 15),
        ("slide", "A", "+0:00", 5),
        ("break", "Pause", "+0:05", 5),
        ("slide", "B", "+0:10", 5),
    ]


def test_without_beginn_times_are_offsets() -> None:
    schedule = schedule_of("# K\n\n## A {dauer=75}\n\n## B {dauer=5}\n")
    assert schedule.begin is None
    assert [schedule.span(e) for e in schedule.entries] == [
        "+0:00–+1:15 (75 min)",
        "+1:15–+1:20 (5 min)",
    ]


def test_times_run_on_over_breaks_and_past_noon() -> None:
    schedule = schedule_of(
        "---\nbeginn: 11:50\n---\n# K\n\n## A {dauer=5}\n\n"
        "## P {.break dauer=1h}\n\n## B {dauer=5}\n"
    )
    assert [schedule.span(e) for e in schedule.entries] == [
        "11:50–11:55 (5 min)",
        "11:55–12:55 (60 min)",
        "12:55–13:00 (5 min)",
    ]


def test_split_slides_count_once() -> None:
    long = "\n".join(f"- Punkt {n}" for n in range(30))
    schedule = schedule_of(f"# K\n\n## Lang {{dauer=5}}\n\n{long}\n")
    assert schedule.total == 5


def test_the_schedule_is_that_of_the_version() -> None:
    markdown = "# K\n\n## A {dauer=5}\n\n## Intern {.internal dauer=10}\n"
    assert schedule_of(markdown).total == 5
    assert schedule_of(markdown, Audience.TRAINER).total == 15


# ---------------------------------------------------------------------- notes


def notes_of(markdown: str) -> list[tuple[str, int | None, str]]:
    collector = Notes()
    schedule_of(markdown).add_notes(collector)
    return [(n.code, n.line, n.message) for n in collector.to_tuple()]


def test_slides_without_a_length_are_reported_once() -> None:
    found = notes_of("# K\n\n## A {dauer=5}\n\n## B\n\n## C\n")
    assert found == [
        (
            NoteCodes.SCHEDULE_MISSING,
            5,
            "2 slides have no 'dauer'; the schedule assumes 2 min each. Give each slide its "
            "minutes ('## Folie {dauer=5}') or its chapter ('# Kapitel {dauer=45}').",
        )
    ]


def test_a_total_other_than_laenge_is_reported() -> None:
    found = notes_of(DECK)
    assert found == [
        (NoteCodes.SCHEDULE_LENGTH, None, "Planned 90 min ('laenge:'), slides sum to 140 min.")
    ]
    assert notes_of("---\nlaenge: 5\n---\n# K\n\n## A {dauer=5}\n") == []


def test_a_chapter_its_slides_overrun_is_reported() -> None:
    found = notes_of("# K\n\n# Teil {dauer=5}\n\n## A {dauer=4}\n\n## B {dauer=3}\n")
    assert found == [
        (NoteCodes.SCHEDULE_LENGTH, 3, "The chapter 'Teil' plans 5 min, its slides sum to 7 min.")
    ]


def test_only_laenge_assumes_two_minutes_a_slide() -> None:
    schedule = schedule_of("---\nlaenge: 10\n---\n# K\n\n## A\n\n## B\n")
    assert schedule.total == 4 and len(schedule.missing) == 2


def test_check_compares_with_the_rule_of_thumb() -> None:
    far = "# K\n\n## A {dauer=60}\n\nText\n"
    result = check(MarkdownDocument(far), PPTX)
    assert result.codes() == [NoteCodes.SCHEDULE_ESTIMATE]
    assert "plans 60 min of talking (breaks aside), the rule of thumb about 2 min" in str(
        result.notes[0]
    )
    near = "# K\n\n## A {dauer=3}\n\nText\n\n## P {.break dauer=30}\n"
    assert check(MarkdownDocument(near), PPTX).codes() == []


def test_check_does_not_compare_a_schedule_without_any_dauer() -> None:
    markdown = "---\nlaenge: 2\n---\n# K\n\n## A\n\nText\n"
    assert check(MarkdownDocument(markdown), PPTX).codes() == [NoteCodes.SCHEDULE_MISSING]


# ---------------------------------------------------------------------- backup (E16-S04)

BACKUP_SLIDES: Final = "".join(f"## Reserve {n}\n\nText\n\n" for n in range(1, 11))


@pytest.mark.parametrize("closing", ["# Danke {.closing}\n\n", ""])
def test_backup_chapters_get_no_times_and_do_not_count_toward_laenge(closing: str) -> None:
    markdown = (
        "---\nbeginn: 09:00\nlaenge: 15\n---\n# K\n\n## A {dauer=5}\n\nText\n\n"
        "# Teil {dauer=10}\n\n## B\n\nText\n\n"
        f"{closing}# Backup {{.backup}}\n\n{BACKUP_SLIDES}# Mehr Backup\n\n## Noch eine\n"
    )
    schedule = schedule_of(markdown)
    assert [e.title for e in schedule.entries] == ["A", "Teil", "B"]
    assert schedule.total == 15 and schedule.missing == ()
    notes = Notes()
    schedule.add_notes(notes)
    assert notes.to_tuple() == ()


@pytest.mark.parametrize(
    "markdown",
    [
        "# K\n\n## A {dauer=5}\n\n# Danke {.closing}\n\n# Backup {.backup}\n\n"
        "## Pause {.break dauer=15}\n",
        "# K\n\n## A {dauer=5}\n\n# Backup {.backup}\n\n# Mehr\n\n## Pause {.break dauer=5}\n",
        "# K\n\n## A {dauer=5}\n\n# Danke {.closing}\n\n## Pause {.break dauer=15}\n",
    ],
)
def test_a_break_in_the_backup_or_behind_the_closing_slide_raises(markdown: str) -> None:
    for format in (PPTX, DocumentFormat.DOCX):
        with pytest.raises(DocumentConversionError) as caught:
            layout_syntax.check(parse(markdown), format)
        assert "where nothing is planned any more" in caught.value.reason
        assert caught.value.reason.startswith("Line ")


@pytest.mark.parametrize(
    "markdown",
    [
        "# K\n\n# Danke {.closing}\n\n# Backup {.backup dauer=10}\n",
        "# K\n\n# Backup {.backup}\n\n## Reserve {dauer=5}\n",
        "# K\n\n# Danke {.closing}\n\n## Danach {dauer=5}\n",
    ],
)
def test_a_dauer_in_the_backup_or_behind_the_closing_slide_raises(markdown: str) -> None:
    with pytest.raises(DocumentConversionError) as caught:
        layout_syntax.check(parse(markdown), PPTX)
    assert "backup slides get no time. Leave out dauer." in caught.value.reason


def test_check_compares_without_the_backup_slides() -> None:
    markdown = f"# K\n\n## A {{dauer=3}}\n\nText\n\n# Danke {{.closing}}\n\n{BACKUP_SLIDES}"
    result = check(MarkdownDocument(markdown), PPTX)
    assert result.codes() == []
    assert isinstance(result.stats, DeckStats)
    assert result.stats.backup == 10 and result.stats.minutes == 2


# ---------------------------------------------------------------------- the table


def test_the_table_marks_chapters_breaks_and_assumed_lengths() -> None:
    schedule = schedule_of(
        "---\nbeginn: 09:00\n---\n# K\n\n# Teil|1\n\n## A *b* {dauer=5}\n\n## C\n\n"
        "## P {.break dauer=10}\n"
    )
    assert schedule.to_markdown() == (
        "| Von | Bis | Dauer | Kapitel/Folie | Notizen |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 09:00 | 09:07 | 7 min | **Teil\\|1** |  |\n"
        "| 09:00 | 09:05 | 5 min | A b |  |\n"
        "| 09:05 | 09:07 | ≈ 2 min | C |  |\n"
        "| 09:07 | 09:17 | 10 min | ==P== |  |\n"
        "|  |  | **17 min** | **Summe** |  |\n"
    )
    assert [e.kind for e in schedule.entries][-1] is EntryKind.BREAK


def test_the_table_speaks_the_language_of_the_deck() -> None:
    schedule = schedule_of("---\nsprache: en\n---\n# K\n\n## A {dauer=5}\n")
    assert schedule.to_markdown().startswith("| From | To | Duration | Chapter/slide | Notes |")
    assert schedule.planned(schedule.entries[0]) == "Planned: +0:00–+0:05 (5 min)"


def test_the_document_is_a_word_document_on_the_template_without_cover() -> None:
    text = schedule_document(schedule_of(DECK))
    assert text.startswith(
        '---\nvorlage: hoch-ohne-deckblatt\ntitel: "Zeitplan: Kurs"\nsprache: de\n'
        "kennzeichnung: intern\n---\n\n# Zeitplan: Kurs\n\n"
        "Beginn 09:00 · geplante Länge 90 min · Summe 140 min\n\n| Von |"
    )
    customer = schedule_document(schedule_of(DECK), Audience.KUNDE)
    assert "kennzeichnung" not in customer
    assert "je 2 min angesetzt" in schedule_document(schedule_of("# K\n\n## A\n\n## B {dauer=1}\n"))


# ---------------------------------------------------------------------- ./run.sh schedule


def load_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "schedule_tool", REPO_ROOT / "tools/schedule/schedule.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TOOL: Final = load_tool()


def test_the_tool_writes_the_schedule_as_word(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "kurs-praesentation.md"
    source.write_text(DECK, encoding="utf-8")
    assert TOOL.main([str(source), "--markdown"]) == 0
    target = tmp_path / "kurs-praesentation-zeitplan.docx"
    data = target.read_bytes()
    review = REVIEW_DIR / "zeitplan"
    review.mkdir(parents=True, exist_ok=True)
    (review / target.name).write_bytes(data)
    out = capsys.readouterr().out
    assert f"wrote {target}" in out
    assert "slides sum to 140 min" in out and "| 09:50 | 11:20 | 90 min | Übung |  |" in out
    document = open_docx(data)
    assert document.tables and document.tables[0].rows[-1].cells[2].text == "140\u00a0min"
    markdown = DocxConverter().convert(data).text
    assert "| 09:35 | 09:50 | 15\u00a0min | Pause |  |" in markdown
    assert TOOL.main([str(source), "--strict"]) == 1


def test_the_tool_stops_for_a_deck_without_schedule_and_skips_it_in_a_folder(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "kurs-praesentation.md"
    source.write_text("# Kurs\n\n## Folie\n", encoding="utf-8")
    (tmp_path / "text-bericht.md").write_text("# Bericht\n", encoding="utf-8")
    assert TOOL.main([str(source)]) == 1
    assert "no schedule" in capsys.readouterr().err
    assert TOOL.main([str(tmp_path)]) == 0
    assert "skipped" in capsys.readouterr().out
    assert not list(tmp_path.glob("*.docx"))


def test_the_tool_reports_mistakes_and_wrong_switches(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "kurs-praesentation.md"
    source.write_text("# Kurs\n\n## Folie {dauer=x}\n", encoding="utf-8")
    assert TOOL.main([str(source)]) == 1
    assert "Line 3: The heading attribute dauer=x" in capsys.readouterr().err
    assert TOOL.main([str(source), "--audience", "alle"]) == 1
    assert TOOL.main([]) == 1


def test_the_sample_has_a_schedule_without_notes() -> None:
    sample = REPO_ROOT / "samples/funktionen/zeitplan-praesentation.md"
    schedule = schedule_of(sample.read_text(encoding="utf-8"))
    assert schedule.total == schedule.length
    collector = Notes()
    schedule.add_notes(collector)
    assert collector.to_tuple() == ()
