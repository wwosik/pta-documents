"""E15-S03: ``:icon-name:`` as an ``icon`` token."""

from __future__ import annotations

from markdown_it.token import Token

from pta_documents.markdown.icon import ICON, NAME, markdown
from pta_documents.markdown.parser import parse


def children(text: str) -> list[Token]:
    inline = next(t for t in parse(text) if t.type == "inline")
    return list(inline.children or [])


def test_an_icon_is_a_token_with_its_name() -> None:
    kids = children("Der :icon-alert-triangle: Hinweis")
    assert [k.type for k in kids] == ["text", ICON, "text"]
    assert kids[1].meta[NAME] == "alert-triangle"
    assert kids[1].markup == ":icon-alert-triangle:"


def test_code_spans_and_other_colons_stay_text() -> None:
    for text in ("`:icon-check:`", ":icon-:", ":icon-Check:", "icon-check:", ":icon-a--b:"):
        assert ICON not in [k.type for k in children(text)], text


def test_icons_stand_next_to_emphasis_and_text() -> None:
    kids = [k for k in children("**fertig:icon-check:**") if k.type != "text" or k.content]
    assert [k.type for k in kids] == ["strong_open", "text", ICON, "strong_close"]


def test_the_markdown_of_an_icon() -> None:
    assert markdown("check") == ":icon-check:"
