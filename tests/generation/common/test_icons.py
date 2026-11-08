"""E15-S03: checking icon names and finding the icons that are figures and bullets."""

from __future__ import annotations

import pytest
from markdown_it.token import Token

from pta_documents.design import colors
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import icons, layout_syntax
from pta_documents.markdown.parser import parse


def inline(text: str) -> Token:
    return next(t for t in parse(text) if t.type == "inline")


def test_unknown_names_are_an_error_with_line_and_suggestions() -> None:
    tokens = parse("Text\n\nDer :icon-sever: läuft.\n")
    with pytest.raises(DocumentConversionError) as error:
        layout_syntax.check(tokens, DocumentFormat.DOCX, line_offset=10)
    assert str(error.value).endswith(
        "Line 13: Unknown icon ':icon-sever:'. "
        "Did you mean :icon-server:, :icon-server-2:, :icon-user:?"
    )


def test_known_names_pass() -> None:
    layout_syntax.check(parse("- :icon-check: a\n"), DocumentFormat.PPTX)


def test_the_leading_icon_and_the_rest() -> None:
    token = inline(" :icon-rocket:  Start **jetzt**")
    assert icons.leading(token) == "rocket"
    rest = icons.without_leading(token)
    assert [c.type for c in rest.children or []][:2] == ["text", "strong_open"]
    assert (rest.children or [])[0].content == "Start "
    assert icons.leading(inline("Start :icon-rocket:")) is None
    plain = inline("Start")
    assert icons.without_leading(plain) is plain


def test_a_list_has_icon_bullets_when_every_item_starts_with_one() -> None:
    tokens = parse("- :icon-check: a\n- :icon-x: b\n  - c\n")
    assert icons.list_icons(tokens, 0) == ["check", "x"]
    assert icons.list_icons(parse("- :icon-check: a\n- b\n"), 0) is None
    assert icons.list_icons(parse("1. :icon-check: a\n"), 0) is None


def test_figures_are_pta_blue_and_white_on_dark_areas() -> None:
    assert icons.color_on(False) == colors.PTA_BLUE
    assert icons.color_on(True) == colors.WHITE
