"""E06-S01: reading ``chart`` blocks (cases of DocLibs ``ChartTests.cs``)."""

from __future__ import annotations

import pytest

from pta_documents.charts import ChartBlockError, ChartKind, parse

ORDERS = (
    "type: bar\ntitle: Orders by month\nunit: k\nsource: Quelle: erfunden\n---\n"
    "month, plan, actual\nJan, 120, 132\nFeb, 118, 121\nMar, 125,\n"
)


def test_settings_and_data_with_empty_cells_as_gaps() -> None:
    chart = parse(ORDERS, 4)
    assert chart.kind is ChartKind.BAR
    assert (chart.title, chart.unit, chart.source) == ("Orders by month", "k", "Quelle: erfunden")
    assert chart.categories == ("Jan", "Feb", "Mar")
    assert [s.name for s in chart.series] == ["plan", "actual"]
    assert chart.series[1].values == (132, 121, None)
    assert not chart.stacked


def test_csv_alone_quoted_commas_and_comments() -> None:
    csv = parse('region, "sales, net"\n"North, East", 1.5\n', 1)
    settings = parse(
        "type: area   # filled\n# a whole comment line\nstacked: true\n---\nx, a, b\n1, 2, 3\n"
    )
    assert csv.categories == ("North, East",)
    assert [s.name for s in csv.series] == ["sales, net"]
    assert csv.series[0].values == (1.5,)
    assert settings.kind is ChartKind.AREA
    assert settings.stacked
    # Lines never stack.
    assert not parse("type: line\nstacked: true\n---\nx, a\n1, 2\n").stacked


def test_semicolons_take_a_decimal_comma() -> None:
    chart = parse("Monat; Umsatz, netto; Kosten\nJan; 1250,5; -3\nFeb; ; 0,25\n")
    assert [s.name for s in chart.series] == ["Umsatz, netto", "Kosten"]
    assert chart.series[0].values == (1250.5, None)
    assert chart.series[1].values == (-3, 0.25)


def test_keys_and_kinds_ignore_case() -> None:
    chart = parse("Type: LINE\nTitle: T\n---\nx, a\n1, 2\n")
    assert (chart.kind, chart.title) == (ChartKind.LINE, "T")


@pytest.mark.parametrize(
    ("code", "line", "message"),
    [
        ("colour: red\n---\nx, a\n1, 2\n", 8, "Unknown setting 'colour'. Valid settings: type,"),
        ("type: bar\ntype: pie\n---\nx, a\n1, 2\n", 9, "The setting 'type' is given twice"),
        ("type: pie\n---\nx, a\n1, 2\n", 8, "The type 'pie' is not bar, line or area"),
        ("stacked: ja\n---\nx, a\n1, 2\n", 8, "stacked is true or false, not 'ja'"),
        ("just words\n---\nx, a\n1, 2\n", 8, "'just words' is not a setting"),
        ("---\nx, a\n1, 1,200\n", 10, "Row 2 of the data has 3 values; the header names 2 columns"),
        ("---\nx, a\n1, lots\n", 10, "'lots' in row 2 of the data is not a number"),
        ("---\nx, a\n1, 1e\n", 10, "'1e' in row 2"),
        ("x; a\n1; 1.5\n", 9, "with a decimal comma and no thousands separator"),
        ("x, a\n1, nan\n", 9, "'nan' in row 2"),
        ("---\nx, a\n", 7, "needs a header row and at least one row of values"),
        ("---\nx\n1\n", 9, "names the category column and at least one series"),
    ],
)
def test_mistakes_name_their_line_and_the_problem(code: str, line: int, message: str) -> None:
    with pytest.raises(ChartBlockError) as error:
        parse(code, 7)
    text = str(error.value)
    assert text.startswith(f"Line {line}: The chart block cannot be drawn: ")
    assert message in text


def test_without_a_line_the_message_has_none() -> None:
    with pytest.raises(ChartBlockError) as error:
        parse("x, a\n1, lots\n")
    assert str(error.value).startswith("The chart block cannot be drawn: ")
