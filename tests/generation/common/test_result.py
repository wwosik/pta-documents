"""E08-S01: the notes model (port of GenerationNotesTests.cs in vt-tools-libs)."""

from __future__ import annotations

from pta_documents import GenerationNote, GenerationResult, NoteCodes
from pta_documents.generation.common.result import Notes


def test_a_note_reads_as_line_and_message() -> None:
    assert str(GenerationNote(NoteCodes.RAW_HTML, 12, "Left out.")) == "line 12: Left out."
    assert str(GenerationNote(NoteCodes.RAW_HTML, None, "Left out.")) == "Left out."


def test_the_result_is_a_markdown_list_or_no_notes() -> None:
    notes = (
        GenerationNote(NoteCodes.RAW_HTML, 3, "A."),
        GenerationNote(NoteCodes.SLIDE_SPLIT, None, "B."),
    )
    assert str(GenerationResult(notes, slides=2)) == "- line 3: A.\n- B.\n"
    assert str(GenerationResult()) == "No notes.\n"
    assert GenerationResult(notes).codes() == ["raw-html", "slide-split"]


def test_notes_are_kept_once_and_sorted_by_line() -> None:
    notes = Notes()
    notes.add(NoteCodes.RAW_HTML, 9, "Later.")
    notes.add(NoteCodes.CODE_NOT_DRAWN, 2, "Earlier.")
    notes.add(NoteCodes.RAW_HTML, 9, "Later.")
    notes.add(NoteCodes.SLIDE_SPLIT, None, "Without a line.")
    assert [(n.line, n.message) for n in notes.to_tuple()] == [
        (None, "Without a line."),
        (2, "Earlier."),
        (9, "Later."),
    ]
    assert len(notes) == 3


def test_codes_are_unique_kebab_case() -> None:
    assert len(set(NoteCodes.ALL)) == len(NoteCodes.ALL)
    assert all(code == code.lower() and " " not in code for code in NoteCodes.ALL)


def test_characters_the_fonts_lack_are_noted_once_at_their_first_line() -> None:
    markdown = "Haken ✓ hier\n\n```\ncode ✓ und ★\n```\n\nnoch ein ✓ und `★` und ★ und é\n"
    notes = Notes()
    notes.characters(
        markdown,
        line_offset=3,
        in_text=lambda c: c == "é",
        in_code=lambda c: c != "★",
        effect="is replaced",
        alternatives={"✓": ["✔", "x"]},
    )
    result = notes.to_tuple()
    assert [(n.code, n.line) for n in result] == [
        (NoteCodes.CHARACTER_MISSING, 4),  # ✓ in text, line 1 + 3 lines of front matter
        (NoteCodes.CHARACTER_MISSING, 7),  # ★ in the code block
    ]
    assert result[0].message == (
        "'✓' (U+2713) is not in the fonts and is replaced. Write `x` instead."
    )
    assert result[1].message.endswith("Leave it out or write it in words.")
