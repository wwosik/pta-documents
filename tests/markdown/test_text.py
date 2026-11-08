from __future__ import annotations

import doctest

import pytest

from pta_documents.markdown import text as md
from pta_documents.markdown.parser import parse


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("customfield_10682", "customfield_10682"),
        ("_leading", "\\_leading"),
        ("*not bold*", "\\*not bold\\*"),
        ("[not a link]", "\\[not a link]"),
        ("<b> and a < b", "\\<b> and a < b"),
        ("C:\\path", "C:\\path"),
        ("2 * 3", "2 \\* 3"),
    ],
)
def test_escape_guards_only_what_would_format(text: str, expected: str) -> None:
    assert md.escape(text) == expected


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("# no heading", "\\# no heading"),
        ("- no item", "\\- no item"),
        ("2026. was a year", "2026\\. was a year"),
        ("---", "\\---"),
        ("end-to-end", "end-to-end"),
    ],
)
def test_escape_line_start_guards_block_markers(line: str, expected: str) -> None:
    assert md.escape_line_start(line) == expected


def test_code_survives_backticks() -> None:
    assert md.code("a") == "`a`"
    assert md.code("a`b") == "``a`b``"
    assert md.code("`x") == "`` `x ``"


def test_destination_wraps_awkward_urls() -> None:
    assert md.destination("images/a.png") == "images/a.png"
    assert md.destination("images/a b.png") == "<images/a b.png>"


def test_table_has_a_header_row_and_escapes_cells() -> None:
    table = md.table([["Item", "Price"], ["Pear | green", "0.90\nper kg"], ["Short"]])
    assert table == (
        "| Item | Price |\n| --- | --- |\n| Pear \\| green | 0.90<br>per kg |\n| Short |  |\n\n"
    )
    assert md.table([]) == ""


def test_compact_drops_empty_rows_and_columns() -> None:
    grid = md.compact([["a", "", "b"], ["", "", ""], ["c", " ", "d"]])
    assert grid == [["a", "b"], ["c", "d"]]


def test_normalize_collapses_blank_lines_and_ends_with_one_newline() -> None:
    assert md.normalize("\r\n\na  \r\n\r\n\r\n\nb\n\n\n") == "a\n\nb\n"
    assert md.normalize(" \n \n") == ""


def test_all_names_exactly_the_doclibs_helpers() -> None:
    assert sorted(md.__all__) == [
        "cell",
        "code",
        "compact",
        "destination",
        "escape",
        "escape_line_start",
        "normalize",
        "table",
    ]


def test_docstring_examples_hold() -> None:
    result = doctest.testmod(md)
    assert result.attempted >= len(md.__all__)
    assert result.failed == 0


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("a\\", "a\\\\"),
        ("a\\.", "a\\\\."),
        ("a\\b", "a\\b"),
        ("\\\\", "\\\\\\\\"),
        ("</a>", "\\</a>"),
        ("<!-- c -->", "\\<!-- c -->"),
        ("<?php", "\\<?php"),
        ("<1", "<1"),
        ("snake_case_name", "snake_case_name"),
        ("x_", "x\\_"),
    ],
)
def test_escape_guards_backslashes_and_tag_starts(text: str, expected: str) -> None:
    assert md.escape(text) == expected


def test_escape_leaves_entities_and_pta_extensions() -> None:
    # Like DocLibs: only CommonMark emphasis, code, links, strikethrough and tags are guarded.
    for text in ("&amp;", "==mark==", ":icon-rocket:", "a | b"):
        assert md.escape(text) == text


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("+ item", "\\+ item"),
        ("+", "\\+"),
        ("+++", "+++"),
        ("++ x", "++ x"),
        ("===", "\\==="),
        ("=", "\\="),
        ("> quote", "\\> quote"),
        ("| a |", "\\| a |"),
        ("123456789. x", "123456789\\. x"),
        ("123456789) x", "123456789\\) x"),
        ("1234567890. x", "1234567890. x"),
        ("1.", "1\\."),
        ("1.x", "1.x"),
        ("", ""),
    ],
)
def test_escape_line_start_list_markers_and_limits(line: str, expected: str) -> None:
    assert md.escape_line_start(line) == expected


def test_table_fills_short_rows_and_flattens_breaks_and_tabs() -> None:
    table = md.table([["a", "b", "c"], ["x"], ["1\tz", "p\r\nq", "r\\\ns"], ["t  \nu"]])
    assert table == (
        "| a | b | c |\n"
        "| --- | --- | --- |\n"
        "| x |  |  |\n"
        "| 1 z | p<br>q | r<br>s |\n"
        "| t<br>u |  |  |\n\n"
    )


def test_normalize_empty_and_blank_text_gives_nothing() -> None:
    assert md.normalize("") == ""
    assert md.normalize("\n\n  \n\t\n") == ""
    assert md.normalize("a  \nb") == "a\nb\n"


_TRICKY = [
    "*not bold* and **not strong**",
    "_leading and trailing_",
    "__init__ in snake_case_name",
    "`code` and ``more``",
    "[not a link](target) and ![no image](a.png)",
    "~~not struck~~",
    "<b>no tag</b>, <!-- no comment -->, <?php, <http://x.de>",
    "a < b > c",
    "C:\\path\\",
    "end\\",
    "\\*already escaped\\*",
    "# no heading",
    "> no quote",
    "| no | table |",
    "- no item",
    "+ no item",
    "-",
    "---",
    "===",
    "2026. was a year",
    "123456789) no item",
    "[^1] no footnote",
    "[ ] no task",
    "customfield_10682",
]


@pytest.mark.parametrize("text", _TRICKY)
def test_escaped_text_reads_back_unchanged_through_the_parser(text: str) -> None:
    tokens = parse(md.escape_line_start(md.escape(text)) + "\n")
    assert [t.type for t in tokens] == ["paragraph_open", "inline", "paragraph_close"]
    children = tokens[1].children or []
    assert all(child.type == "text" for child in children)
    assert "".join(child.content for child in children) == text
