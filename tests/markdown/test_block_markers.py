"""E09-S02: block markers (``{.build}`` …) are taken out of the token stream and mark the block
after them; wrong ones stay with their reason, for ``layout_syntax.check``."""

from __future__ import annotations

import pytest
from markdown_it.token import Token

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import layout_syntax
from pta_documents.markdown import block_markers
from pta_documents.markdown.block_markers import ERROR, MARKER, Marker, MarkerError, read
from pta_documents.markdown.parser import parse


def marked(tokens: list[Token]) -> list[tuple[str, Marker]]:
    return [(t.type, t.meta[MARKER]) for t in tokens if MARKER in t.meta]


def texts(tokens: list[Token]) -> list[str]:
    return [t.content for t in tokens if t.type == "inline"]


def test_read_knows_the_markers_and_entrances() -> None:
    assert read("{.build}") == Marker("build", "fade", "{.build}")
    assert read("  { .frag=fly }  ") == Marker("frag", "fly", "{ .frag=fly }")
    assert read("{.exit}") == Marker("exit", "fade", "{.exit}")
    assert read("{.emphasize}") == Marker("emphasize", "fade", "{.emphasize}")
    assert read("{.build} text") is None
    assert read("[words]{.success}") is None
    assert read("{#id}") is None


@pytest.mark.parametrize(
    ("line", "reason"),
    [
        ("{.wide}", "Unknown block marker '{.wide}'. Valid markers: {.build}, {.frag}"),
        ("{.build .frag}", "more than one block marker"),
        ("{.exit=fade}", "takes no value"),
        ("{.build=zoom}", "Unknown entrance '{.build=zoom}'"),
    ],
)
def test_wrong_markers_raise(line: str, reason: str) -> None:
    with pytest.raises(MarkerError, match=reason.replace(".", r"\.").replace("{", r"\{")):
        read(line)


def test_a_marker_paragraph_goes_and_marks_the_next_block() -> None:
    tokens = parse("Text\n\n{.build}\n\n- a\n- b\n")
    assert texts(tokens) == ["Text", "a", "b"]
    assert marked(tokens) == [("bullet_list_open", Marker("build", "fade", "{.build}"))]


@pytest.mark.parametrize(
    ("source", "kind"),
    [
        ("{.build}\n- a\n", "bullet_list_open"),
        ("{.build}\n| a |\n|---|\n| 1 |\n", "table_open"),
        ("{.frag}\n::: panel\nText\n:::\n", "container_layout_open"),
        ("{.frag}\n```python\nx = 1\n```\n", "fence"),
        ("{.frag}\n> quoted\n", "blockquote_open"),
        ("{.frag}\n### Subheadline\n", "heading_open"),
    ],
)
def test_a_marker_right_above_a_block_marks_it(source: str, kind: str) -> None:
    tokens = parse(source)
    assert [k for k, _ in marked(tokens)] == [kind]
    assert "{" not in "".join(texts(tokens))


def test_a_marker_as_first_line_marks_its_paragraph() -> None:
    tokens = parse("{.frag=wipe}\nThe text\nof the paragraph\n")
    assert texts(tokens) == ["The text\nof the paragraph"]
    assert marked(tokens) == [("paragraph_open", Marker("frag", "wipe", "{.frag=wipe}"))]
    assert tokens[0].map == [1, 3]


def test_a_marker_as_last_line_marks_the_block_after_it() -> None:
    # In a list item, the marker line before a nested list continues the item's text.
    tokens = parse("- a\n  {.build}\n  - b\n  - c\n")
    assert texts(tokens) == ["a", "b", "c"]
    lists = [t for t in tokens if t.type == "bullet_list_open"]
    assert MARKER not in lists[0].meta and lists[1].meta[MARKER].name == "build"


def test_markers_in_code_stay_code() -> None:
    tokens = parse("```markdown\n{.build}\n- a\n```\n")
    assert tokens[0].content == "{.build}\n- a\n"
    assert marked(tokens) == []


@pytest.mark.parametrize(
    ("source", "line", "reason"),
    [
        ("Text\n\n{.wide}\n", 3, "Unknown block marker '{.wide}'"),
        ("- a\n\n{.build}\n", 3, "The block marker '{.build}' marks nothing"),
        ("::: panel\n{.frag}\n:::\n", 2, "marks nothing"),
        ("Text\n\n{.frag}\n\n---\n", 3, "marks nothing"),
        ("{.frag}\n\n## Slide\n", 1, "before a heading that starts a slide"),
        ("# Deck\n\n{.frag}\n::: notes\nSay\n:::\n", 3, "cannot mark speaker notes"),
        ("{.emphasize}\n| a |\n|---|\n", 1, "turns text PTA blue"),
        ("{.frag}\n\n{.build}\n\n- a\n", 1, "second block marker"),
        ("one\n{.frag}\ntwo\n", 1, "stands within a paragraph"),
        ("{.build}\n3. three\n4. four\n", 1, "does not start at 1 needs a blank line"),
    ],
)
def test_layout_syntax_check_raises_wrong_markers_with_their_line(
    source: str, line: int, reason: str
) -> None:
    tokens = parse(source)
    assert any(ERROR in t.meta for t in tokens)
    with pytest.raises(DocumentConversionError) as caught:
        layout_syntax.check(tokens, DocumentFormat.DOCX, line_offset=0)
    assert caught.value.reason.startswith(f"Line {line}: ")
    assert reason in caught.value.reason


def test_the_valid_markers_are_named_in_one_place() -> None:
    assert ", ".join("{." + name + "}" for name in block_markers.NAMES) == block_markers.VALID
    assert block_markers.ENTRANCES[0] == block_markers.FADE
