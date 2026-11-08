"""E15-S04: the braces after an image land in its token's ``meta``."""

from __future__ import annotations

from markdown_it.token import Token

from pta_documents.markdown.image_attributes import ATTRIBUTES, markdown
from pta_documents.markdown.parser import parse


def children(text: str) -> list[Token]:
    return parse(text)[1].children or []


def test_the_braces_right_after_an_image_are_its_attributes() -> None:
    [image] = children("![a](b.jpg){focus=30%,20% .round}")
    assert image.type == "image"
    assert image.meta[ATTRIBUTES] == "focus=30%,20% .round"


def test_braces_after_a_space_or_after_text_stay_text() -> None:
    image, text = children("![a](b.jpg) {focus=top}")
    assert ATTRIBUTES not in image.meta
    assert text.content == " {focus=top}"
    [plain] = children("Mengen {a, b}")
    assert plain.content == "Mengen {a, b}"


def test_only_the_first_braces_count_and_links_keep_their_image() -> None:
    image, text = children("![a](b.jpg){.grey}{x}")
    assert image.meta[ATTRIBUTES] == ".grey"
    assert text.content == "{x}"
    _, linked, _ = children("[![a](b.jpg){.round}](https://example.org)")
    assert linked.meta[ATTRIBUTES] == ".round"


def test_unclosed_braces_stay_text() -> None:
    image, text = children("![a](b.jpg){focus=top")
    assert ATTRIBUTES not in image.meta
    assert text.content == "{focus=top"


def test_markdown_writes_the_braces() -> None:
    assert markdown(".round") == "{.round}"
    assert markdown("") == ""
