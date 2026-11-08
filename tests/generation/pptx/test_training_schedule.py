"""E16-S02: the schedule on the slides: break slides, the agenda with clock times, the planned
time in the trainer's notes."""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path
from typing import Final

import pytest

from pta_documents.design import slides as design
from pta_documents.design.variants import WordVariant
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.common.audience import Audience
from pta_documents.generation.common.result import NoteCodes
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.html.generator import HtmlDeckGenerator
from pta_documents.generation.html.options import HtmlDeckOptions
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import MarkdownDocument
from tests.conftest import REPO_ROOT
from tests.generation.docx.conftest import open_docx
from tests.generation.pptx.conftest import layout_names, open_pptx, texts
from tests.generation.pptx.test_speaker_notes import notes_texts

DECK: Final = """---
beginn: 09:00
---
# Kurs

## Agenda {.agenda dauer=5}

# Einführung {dauer=20}

## Ziele

Text

## Ablauf

Text

## Pause {.break dauer=15}

# Praxis

## Übung {dauer=30}

Text

::: notes
Zeit für Fragen lassen.
:::

# Danke {.closing}
"""


def generate(markdown: str, audience: Audience | None = None) -> bytes:
    output = io.BytesIO()
    result = PptxGenerator().generate(
        MarkdownDocument(markdown), output, PptxOptions(audience=audience)
    )
    assert result.notes == (), str(result)
    return output.getvalue()


def agenda_items(data: bytes) -> list[str]:
    slide = open_pptx(data).slides[1]
    found = texts(slide)
    return [found[idx] for idx in design.PLACEHOLDERS.agenda_texts if found.get(idx)]


def test_a_break_is_a_slide_on_the_interim_layout(review_dir: Path) -> None:
    data = generate(DECK)
    (review_dir / "zeitplan.pptx").write_bytes(data)
    names = layout_names(data)
    assert names[5] == design.LAYOUTS.interim_01
    assert open_pptx(data).slides[5].shapes.title.text_frame.text == "Pause · 15 min"  # type: ignore[union-attr]


def test_a_break_takes_another_interim_layout_but_no_content() -> None:
    data = generate(f'# K\n\n## Pause {{.break dauer=5 layout="{design.LAYOUTS.interim_02}"}}\n')
    assert layout_names(data)[1] == design.LAYOUTS.interim_02
    with pytest.raises(
        DocumentConversionError, match=r"Line 5: A break \{\.break\} is its heading"
    ):
        generate("# K\n\n## Pause {.break dauer=5}\n\nText\n")


def test_the_agenda_shows_clock_times_and_breaks() -> None:
    assert agenda_items(generate(DECK)) == ["09:05 Einführung", "09:25 Pause", "09:40 Praxis"]


def test_without_beginn_the_agenda_is_as_before() -> None:
    data = generate(DECK.replace("beginn: 09:00", "laenge: 70"))
    assert agenda_items(data) == ["Einführung", "Praxis"]


def test_an_agenda_list_gets_times_where_it_names_a_chapter() -> None:
    markdown = DECK.replace(
        "## Agenda {.agenda dauer=5}\n",
        "## Agenda {.agenda dauer=5}\n\n- einführung\n- Fragen\n- Praxis\n",
    )
    assert agenda_items(generate(markdown)) == [
        "09:05 einführung",
        "Fragen",
        "09:25 Pause",
        "09:40 Praxis",
    ]


def test_an_agenda_list_without_chapters_gets_no_breaks() -> None:
    markdown = DECK.replace(
        "## Agenda {.agenda dauer=5}\n", "## Agenda {.agenda dauer=5}\n\n- Eins\n- Zwei\n"
    )
    assert agenda_items(generate(markdown)) == ["Eins", "Zwei"]


def test_breaks_count_towards_the_eight_agenda_items() -> None:
    chapters = "".join(f"# K{n} {{dauer=5}}\n\n## P{n} {{.break dauer=5}}\n\n" for n in range(5))
    markdown = f"---\nbeginn: 09:00\n---\n# Kurs\n\n## Agenda {{.agenda dauer=5}}\n\n{chapters}"
    with pytest.raises(DocumentConversionError, match="this one 10 \\(5 of them breaks\\)"):
        generate(markdown)


def test_the_trainer_sees_the_planned_time_first_in_the_notes() -> None:
    notes = notes_texts(generate(DECK, Audience.TRAINER))
    assert notes == [
        None,
        "Geplant: 09:00–09:05 (5 min)",
        "Geplant: 09:05–09:25 (20 min)",
        "Geplant: 09:05–09:15 (10 min)",
        "Geplant: 09:15–09:25 (10 min)",
        "Geplant: 09:25–09:40 (15 min)",
        "Geplant: 09:40–10:10 (30 min)",
        "Geplant: 09:40–10:10 (30 min)\nZeit für Fragen lassen.",
        None,
    ]


@pytest.mark.parametrize("audience", [None, Audience.KUNDE, Audience.INTERN])
def test_other_versions_have_no_planned_times(audience: Audience | None) -> None:
    notes = notes_texts(generate(DECK, audience))
    assert notes == [None] * 7 + ["Zeit für Fragen lassen.", None]


def test_a_split_slide_has_the_planned_time_on_every_part() -> None:
    long = "\n".join(f"- Punkt {n} mit etwas mehr Text darin" for n in range(24))
    output = io.BytesIO()
    result = PptxGenerator().generate(
        MarkdownDocument(f"# K\n\n## Lang {{dauer=5}}\n\n{long}\n"),
        output,
        PptxOptions(audience=Audience.TRAINER),
    )
    assert NoteCodes.SLIDE_SPLIT in result.codes()
    notes = notes_texts(output.getvalue())
    assert len(notes) > 2 and set(notes[1:]) == {"Geplant: +0:00–+0:05 (5 min)"}


def test_the_hints_come_with_generating() -> None:
    output = io.BytesIO()
    markdown = "---\nlaenge: 10\n---\n# K\n\n## A {dauer=5}\n\n## B\n"
    result = PptxGenerator().generate(MarkdownDocument(markdown), output)
    assert result.codes() == [NoteCodes.SCHEDULE_LENGTH, NoteCodes.SCHEDULE_MISSING]


def test_wrong_front_matter_raises_with_an_example() -> None:
    with pytest.raises(DocumentConversionError, match=r"'beginn' has the value 'neun'.*'09:00'"):
        generate("---\nbeginn: neun\n---\n# K\n")
    with pytest.raises(DocumentConversionError, match=r"'laenge' has the value 'lang'.*'1h30'"):
        generate("---\nlaenge: lang\n---\n# K\n")
    output = io.BytesIO()
    with pytest.raises(DocumentConversionError, match="front matter key 'beginn' is not supported"):
        DocxGenerator().generate(MarkdownDocument("---\nbeginn: 09:00\n---\n# K\n"), output)


def test_word_takes_the_attributes_and_shows_a_break_plainly() -> None:
    output = io.BytesIO()
    markdown = "# Kapitel {dauer=20}\n\n## Teil {dauer=5}\n\nText\n\n## Pause {.break dauer=15}\n"
    options = DocxOptions(variant=WordVariant.PORTRAIT_NO_COVER)
    assert DocxGenerator().generate(MarkdownDocument(markdown), output, options).notes == ()
    paragraphs = [
        (p.style.name if p.style else "", p.text) for p in open_docx(output.getvalue()).paragraphs
    ]
    assert ("Standard fett", "Pause") in paragraphs
    assert "Kapitel" in [text for _, text in paragraphs]
    assert not any("dauer" in text for _, text in paragraphs)


def test_the_html_deck_has_the_planned_times_of_the_trainer() -> None:
    output = io.BytesIO()
    HtmlDeckGenerator().generate(
        MarkdownDocument(DECK), output, HtmlDeckOptions(audience=Audience.TRAINER)
    )
    assert "Geplant: 09:00–09:05 (5 min)" in output.getvalue().decode("utf-8")


def test_generate_alle_writes_the_trainer_version_of_a_deck_with_schedule() -> None:
    spec = importlib.util.spec_from_file_location(
        "generate_tool", REPO_ROOT / "tools/generate/generate.py"
    )
    assert spec is not None and spec.loader is not None
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    assert tool.audiences_of(DECK, "pptx", "alle") == [Audience.KUNDE, Audience.TRAINER]
    assert tool.audiences_of("# K\n\n## A\n", "pptx", "alle") == [Audience.KUNDE]
    assert tool.audiences_of(DECK, "docx", "alle") == [Audience.KUNDE]
