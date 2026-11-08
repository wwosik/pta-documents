"""E17-S02: code blocks in the PTA colours."""

from __future__ import annotations

from pta_documents.design import colors
from pta_documents.generation.common.code_highlight import (
    LOOKS,
    CodeKind,
    highlight,
    highlight_fence,
)
from pta_documents.generation.common.result import NoteCodes, Notes

PYTHON = ["def answer(x):", '    """Doc."""', "    return 42  # the answer", "", "x = None"]


def kinds(language: str, lines: list[str]) -> list[list[tuple[str, CodeKind]]]:
    result = highlight(lines, language)
    assert result is not None
    return [[(s.text, s.kind) for s in line] for line in result]


def test_each_kind_of_token_gets_its_kind() -> None:
    lines = kinds("python", PYTHON)
    assert len(lines) == len(PYTHON)
    assert lines[0][0] == ("def ", CodeKind.KEYWORD)
    assert ('"""Doc."""', CodeKind.STRING) in lines[1]
    assert ("return ", CodeKind.KEYWORD) in lines[2]
    assert ("42  ", CodeKind.NUMBER) in lines[2]
    assert ("# the answer", CodeKind.COMMENT) in lines[2]
    assert lines[3] == []
    assert ("None", CodeKind.NUMBER) in lines[4]
    assert "".join(t for t, _ in lines[2]) == PYTHON[2]


def test_the_pta_scheme() -> None:
    assert LOOKS[CodeKind.KEYWORD].color == colors.PTA_BLUE and LOOKS[CodeKind.KEYWORD].bold
    assert LOOKS[CodeKind.STRING].color == colors.DARK_BLUE
    assert LOOKS[CodeKind.COMMENT].color == colors.GREY_DARK and LOOKS[CodeKind.COMMENT].italic
    assert LOOKS[CodeKind.NUMBER].color == colors.TEXT_SLIDES
    assert LOOKS[CodeKind.TEXT].color is None


def test_a_multi_line_string_keeps_its_colour() -> None:
    lines = kinds("python", ['s = """eins', 'zwei"""'])
    assert lines[1] == [('zwei"""', CodeKind.STRING)]


def test_without_or_with_an_unknown_language_in_one_colour() -> None:
    notes = Notes()
    assert highlight_fence("", ["x"], 3, notes) is None
    assert notes.to_tuple() == ()
    assert highlight_fence("klingonisch", ["x"], 3, notes) is None
    assert [(n.code, n.line) for n in notes.to_tuple()] == [(NoteCodes.CODE_LANGUAGE_UNKNOWN, 3)]


def test_graphic_languages_and_turned_off_highlighting_are_not_noted() -> None:
    notes = Notes()
    assert highlight_fence("mermaid", ["graph TD"], 1, notes) is None
    assert highlight_fence("klingonisch", ["x"], 1, notes, enabled=False) is None
    assert highlight_fence("python", ["x"], 1, notes, enabled=False) is None
    assert notes.to_tuple() == ()
