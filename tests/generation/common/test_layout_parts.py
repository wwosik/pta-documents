"""E02-S02: the parts of the slide-layout syntax on their own (attributes, containers, alerts,
coloured words, token shapes)."""

from __future__ import annotations

from dataclasses import dataclass, replace

import pytest
from markdown_it.token import Token

from pta_documents.design.colors import StatusCategory
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import coloured_words, heading_attributes, layout_syntax
from pta_documents.generation.common import layout_tokens as shapes
from pta_documents.markdown.parser import parse

F = DocumentFormat.PPTX


def test_heading_attributes_are_split_off() -> None:
    text, attributes = heading_attributes.split('Titel {.dark kicker="Warum"}', F)
    assert text == "Titel"
    assert attributes == heading_attributes.HeadingAttributes(
        dark=True, kicker="Warum", block='{.dark kicker="Warum"}'
    )
    text, attributes = heading_attributes.split('Danke {.closing layout="Abbschlussfolie"}', F)
    assert attributes is not None and attributes.closing and attributes.layout == "Abbschlussfolie"


@pytest.mark.parametrize("text", ["Sets {a, b}", "Code {x}", "{.dark} am Anfang", "A {.dark"])
def test_other_braces_are_no_attributes(text: str) -> None:
    assert heading_attributes.split(text, F) == (text, None)


@pytest.mark.parametrize(
    ("text", "level", "message"),
    [
        ("T {.wide}", 2, "Unknown heading attribute '.wide' in '{.wide}'. Valid attributes: "),
        ("T {.dark .dark}", 2, "The heading attributes '{.dark .dark}' name .dark twice."),
        ('T {layout="a" layout="b"}', 2, "name layout twice"),
        ("T {.closing}", 2, "{.closing} goes on a '#' heading"),
        ("T {.dark}", 1, "'.dark' in '{.dark}' goes on a '##' heading"),
        ('T {kicker="K"}', 1, "'kicker' in '{kicker=\"K\"}' goes on a '##' heading"),
    ],
)
def test_heading_attribute_mistakes(text: str, level: int, message: str) -> None:
    with pytest.raises(DocumentConversionError) as error:
        _, attributes = heading_attributes.split(text, F)
        assert attributes is not None
        heading_attributes.check_level(attributes, level, F)
    assert message in error.value.reason


def test_layout_goes_on_both_levels() -> None:
    _, attributes = heading_attributes.split('T {layout="Nur Titel"}', F)
    assert attributes is not None
    heading_attributes.check_level(attributes, 1, F)
    heading_attributes.check_level(attributes, 2, F)


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("cards", ""),
        ("rows", ""),
        ("panel", ""),
        ("panel", "dark"),
        ("statement", ""),
        ("columns", ""),
        ("columns", "1:2"),
        ("columns", "1:1:2"),
    ],
)
def test_valid_containers(name: str, arguments: str) -> None:
    layout_syntax.check_container(name, arguments, F)


def test_column_widths() -> None:
    assert layout_syntax.column_widths("1:2") == [1, 2]
    assert layout_syntax.column_widths("2:3:5") == [2, 3, 5]
    for wrong in ("1", "1:2:3:4", "0:1", "1:100", "a:b", "1.5:2", "-1:2", ""):
        assert layout_syntax.column_widths(wrong) is None, wrong
    assert layout_syntax.columns(2, False, "", F) == [1, 1]
    assert layout_syntax.columns(3, False, "1:1:2", F) == [1, 1, 2]
    with pytest.raises(DocumentConversionError, match="two or three columns"):
        layout_syntax.columns(1, False, "", F)
    with pytest.raises(DocumentConversionError, match="two or three columns"):
        layout_syntax.columns(2, True, "", F)
    with pytest.raises(DocumentConversionError, match="gives 2 widths for 3 columns"):
        layout_syntax.columns(3, False, "1:2", F)


def test_alert_kinds() -> None:
    assert [layout_syntax.is_important(k, F) for k in layout_syntax.ALERT_KINDS] == [
        False,
        False,
        True,
        True,
        True,
    ]
    assert layout_syntax.is_important("warning", F)
    with pytest.raises(DocumentConversionError, match=r"Unknown alert '\[!HINT\]'"):
        layout_syntax.is_important("HINT", F)


def test_check_names_the_line_with_front_matter() -> None:
    with pytest.raises(DocumentConversionError) as error:
        layout_syntax.check(parse("## T\n\nText\n\n::: card\nx\n:::\n"), F, line_offset=3)
    assert error.value.reason.startswith("Line 8: Unknown container '::: card'.")


def test_check_accepts_attribute_braces_that_look_like_coloured_words() -> None:
    layout_syntax.check(parse("## [Titel]{.dark}\n"), F)


@dataclass(frozen=True)
class R:
    """A run as a generator might have it."""

    text: str
    code: bool = False
    status: StatusCategory | None = None


def apply(runs: list[R]) -> list[R]:
    return coloured_words.apply(
        runs,
        lambda r: r.text,
        lambda r: r.code,
        lambda r, text: replace(r, text=text),
        lambda r, category: replace(r, status=category),
        F,
    )


def test_coloured_words_across_runs() -> None:
    result = apply([R("Status: [on "), R("schedule"), R("]{.success} and [x]{.Danger}.")])
    assert result == [
        R("Status: "),
        R("on ", status=StatusCategory.SUCCESS),
        R("schedule", status=StatusCategory.SUCCESS),
        R(" and "),
        R("x", status=StatusCategory.DANGER),
        R("."),
    ]


def test_coloured_words_never_in_or_across_code_and_breaks() -> None:
    runs = [R("[a"), R("b", code=True), R("]{.success}"), R("\n"), R("[c\nd]{.info}")]
    assert apply(runs) == runs
    assert apply([R("[a]{.success}", code=True)]) == [R("[a]{.success}", code=True)]


def test_an_unknown_colour_raises_with_the_valid_ones() -> None:
    with pytest.raises(DocumentConversionError) as error:
        apply([R("[late]{.red}")])
    assert error.value.reason == (
        "'[late]{.red}' names no colour. "
        "Valid: {.success}, {.warning}, {.danger}, {.info}, {.neutral}."
    )


def inline_of(markdown: str, n: int = 0) -> Token:
    return [t for t in parse(markdown) if t.type == "inline"][n]


def test_tags() -> None:
    assert shapes.tags(inline_of("`a` `b`\n`c`\n")) == ["a", "b", "c"]
    assert shapes.tags(inline_of("`a`\n")) is None
    assert shapes.tags(inline_of("`a` and `b`\n")) is None


def test_labelled_tags() -> None:
    tokens = parse("- `x` first\n- `yy` **second**\n")
    items = shapes.labelled_tags(tokens, 0)
    assert items is not None
    assert [label for label, _ in items] == ["x", "yy"]
    assert items[0][1][0].content == "first"
    assert shapes.labelled_tags(parse("- `x` first\n- plain\n"), 0) is None
    assert shapes.labelled_tags(parse("- `x`\n"), 0) is None
    assert shapes.labelled_tags(parse("- `x` a\n\n  more\n"), 0) is None
    nested = parse("- `x` a\n  - `y` b\n")
    assert shapes.labelled_tags(nested, 0) is None


def test_label_cells_and_marked_rows() -> None:
    tokens = parse("| a | b |\n| - | - |\n| ==x== | `Done` |\n| ==y== z | `a` `b` |\n")
    cells = [t for t in tokens if t.type == "inline"]
    assert shapes.label_cell(cells[3]) == "Done"
    assert shapes.label_cell(cells[5]) is None
    assert shapes.label_cell(cells[0]) is None
    assert shapes.marked_row(cells[2:4])
    assert not shapes.marked_row(cells[4:6])
    assert not shapes.marked_row([])
    assert not shapes.is_marked(inline_of("==a== and ==b==\n"))


def test_only_images() -> None:
    images = shapes.only_images(inline_of("![A](a.png) ![B](b.png)\n"))
    assert images is not None and [i.attrs["src"] for i in images] == ["a.png", "b.png"]
    assert shapes.only_images(inline_of("![A](a.png)\n")) is None
    assert shapes.only_images(inline_of("![A](a.png) text ![B](b.png)\n")) is None
