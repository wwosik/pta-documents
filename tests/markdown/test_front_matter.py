from __future__ import annotations

import datetime as dt

import pytest

from pta_documents import DocumentConversionError, DocumentFormat
from pta_documents.design.colors import StatusCategory
from pta_documents.markdown import FrontMatter, Keys


def read(markdown: str, format: DocumentFormat = DocumentFormat.PDF) -> FrontMatter:
    return FrontMatter.read(markdown, format)


def test_block_is_removed_from_the_body() -> None:
    front = read("---\ntitel: x\n---\n# Kapitel\n")
    assert front.body == "# Kapitel\n"
    assert front.body_line == 3


@pytest.mark.parametrize(
    "markdown", ["---\n\n## Folie\n", "## Folie\n\n---\n\ntitel: x\n", "---", ""]
)
def test_without_front_matter_the_markdown_is_unchanged(markdown: str) -> None:
    front = read(markdown)
    assert front.body == markdown
    assert front.entries == ()


def test_comments_blank_lines_quotes_dots_and_any_case() -> None:
    front = read(
        "---\r\n# Kommentar\r\n\r\nTITEL: \"Plan: 2027\"\r\nautor: 'Team Docs'\r\n"
        "status.success: Fertig\r\n...\r\nText\r\n"
    )
    assert front.get(Keys.TITLE) == "Plan: 2027"
    assert front.get(Keys.AUTHOR) == "Team Docs"
    assert front.get("status.SUCCESS") == "Fertig"
    assert front.body == "Text\r\n"


@pytest.mark.parametrize(
    ("markdown", "expected"),
    [
        ("---\ntitel: a\nTitel: b\n---\n", "'Titel' appears twice"),
        ("---\ntitel: a\nnur Text\n---\n", "'nur Text' is not 'key: value'"),
        ("---\ntitel:\n---\n", "'titel' has no value"),
        ("---\ntitel: a\n## Folie\n", "never closed"),
    ],
)
def test_malformed_blocks_raise_with_the_generators_format(markdown: str, expected: str) -> None:
    with pytest.raises(DocumentConversionError) as error:
        read(markdown, DocumentFormat.DOCX)
    assert error.value.format is DocumentFormat.DOCX
    assert expected in error.value.reason


def test_unknown_keys_list_the_valid_ones() -> None:
    front = read("---\ntitel: a\nfarbe: rot\n---\n")
    with pytest.raises(DocumentConversionError) as error:
        front.check_keys([Keys.TITLE, Keys.AUTHOR])
    assert "'farbe' is not supported here. Valid keys: titel, autor." in error.value.reason


def test_status_keys_are_allowed_when_asked() -> None:
    front = read("---\nstatus.danger: Rot; Kritisch\n---\n")
    front.check_keys([Keys.TITLE], allow_status=True)
    assert front.status_labels() == {
        "Rot": StatusCategory.DANGER,
        "Kritisch": StatusCategory.DANGER,
    }
    with pytest.raises(DocumentConversionError):
        front.check_keys([Keys.TITLE])


def test_status_mistakes() -> None:
    with pytest.raises(DocumentConversionError) as error:
        read("---\nstatus.gut: x\n---\n").status_labels()
    assert "status.success, status.warning" in error.value.reason
    with pytest.raises(DocumentConversionError) as error:
        read("---\nstatus.info: A\nstatus.danger: A\n---\n").status_labels()
    assert "'A' is assigned to two categories" in error.value.reason


@pytest.mark.parametrize(("value", "expected"), [("JA", True), ("nein", False)])
def test_booleans_are_ja_and_nein(value: str, expected: bool) -> None:
    assert read(f"---\ninhaltsverzeichnis: {value}\n---\n").boolean(Keys.TOC) is expected


def test_boolean_mistake() -> None:
    with pytest.raises(DocumentConversionError) as error:
        read("---\ninhaltsverzeichnis: true\n---\n").boolean(Keys.TOC)
    assert "has the value 'true'; expected 'ja' or 'nein'" in error.value.reason


@pytest.mark.parametrize("value", ["2026-11-06", "06.11.2026", "6.11.2026"])
def test_dates(value: str) -> None:
    assert read(f"---\ndatum: {value}\n---\n").date() == dt.date(2026, 11, 6)


@pytest.mark.parametrize("value", ["morgen", "2026-13-01", "31.02.2026"])
def test_bad_dates(value: str) -> None:
    with pytest.raises(DocumentConversionError):
        read(f"---\ndatum: {value}\n---\n").date()
