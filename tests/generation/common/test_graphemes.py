"""E05-S04: text split into grapheme clusters (the cases of DocLibs ``LayoutTests``)."""

from __future__ import annotations

import pytest

from pta_documents.generation.common.graphemes import clusters, code_points


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("abc", ["a", "b", "c"]),
        ("👍🏽", ["👍🏽"]),
        ("❤️", ["❤️"]),
        ("👨‍👩‍👧", ["👨‍👩‍👧"]),
        ("🇩🇪🇫🇷", ["🇩🇪", "🇫🇷"]),
        ("éx", ["é", "x"]),
        ("1️⃣", ["1️⃣"]),
        (
            "🏴\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f",
            ["🏴\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f"],
        ),
        ("a\r\nb", ["a", "\r\n", "b"]),
        ("", []),
    ],
    ids=[
        "latin",
        "skin-tone",
        "variation",
        "family",
        "flags",
        "combining",
        "keycap",
        "tags",
        "crlf",
        "empty",
    ],
)
def test_text_splits_into_what_a_reader_sees_as_one_character(
    text: str, expected: list[str]
) -> None:
    assert clusters(text) == expected
    assert "".join(clusters(text)) == text


def test_code_points_name_each_one_outside_the_bmp_too() -> None:
    assert code_points("😀") == "U+1F600"
    assert code_points("👍🏽") == "U+1F44D U+1F3FD"
