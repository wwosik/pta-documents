from __future__ import annotations

import pytest

from pta_documents.markdown import text as md


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
