"""E16-S02: minutes and clock times as authors write them."""

from __future__ import annotations

import pytest

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import durations

PPTX = DocumentFormat.PPTX


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        ("5", 5),
        ("90", 90),
        ("4h", 240),
        ("1h30", 90),
        ("1h05", 65),
        (" 2h 15 ", 135),
        ("45min", 45),
    ],
)
def test_a_length_is_minutes_or_hours_and_minutes(text: str, minutes: int) -> None:
    assert durations.parse_minutes(text, "x", PPTX) == minutes


@pytest.mark.parametrize("text", ["", "0", "abc", "1h60", "1:30", "-5", "1.5h", "h30"])
def test_a_wrong_length_names_examples(text: str) -> None:
    with pytest.raises(DocumentConversionError) as caught:
        durations.parse_minutes(text, "The value", PPTX)
    assert caught.value.reason.startswith("The value is no length of time")
    assert "'1h30'" in caught.value.reason


@pytest.mark.parametrize(("text", "minutes"), [("09:00", 540), ("9:30", 570), ("13.45", 825)])
def test_a_clock_time_is_minutes_after_midnight(text: str, minutes: int) -> None:
    assert durations.parse_clock(text, "x", PPTX) == minutes


@pytest.mark.parametrize("text", ["9", "24:00", "09:60", "neun", "9:5"])
def test_a_wrong_clock_time_names_an_example(text: str) -> None:
    with pytest.raises(DocumentConversionError, match="'09:00'"):
        durations.parse_clock(text, "x", PPTX)


def test_times_read_as_clock_or_offset() -> None:
    assert durations.clock(545) == "09:05"
    assert durations.clock(24 * 60 + 30) == "00:30"
    assert durations.offset(15) == "+0:15"
    assert durations.offset(135) == "+2:15"
