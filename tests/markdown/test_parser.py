from __future__ import annotations

from pta_documents.errors import DocumentFormat
from pta_documents.markdown.front_matter import FrontMatter
from pta_documents.markdown.parser import (
    ALERT,
    CONTAINER_CLOSE,
    CONTAINER_OPEN,
    container,
    line_of,
    parse,
)

SAMPLE = """---
titel: Beispiel
---
# Kapitel

Text mit **fett**, *kursiv*, ~~weg~~, `code` und [Link](https://pta.de)[^1].

- eins
- [x] erledigt

1. erste

| A | B |
|---|--:|
| 1 | 2 |

![Bild](images/a.png "Titel")

```python
print("x")
```

> Zitat

Begriff
: Erklärung

[^1]: Fußnote.
"""


def test_all_block_types_are_parsed_with_lines() -> None:
    front = FrontMatter.read(SAMPLE, DocumentFormat.DOCX)
    tokens = parse(front.body)
    types = {t.type for t in tokens}
    for expected in (
        "heading_open",
        "paragraph_open",
        "bullet_list_open",
        "ordered_list_open",
        "table_open",
        "fence",
        "blockquote_open",
        "dl_open",
        "footnote_block_open",
    ):
        assert expected in types, expected
    heading = next(t for t in tokens if t.type == "heading_open")
    assert line_of(heading, front.body_line) == 4
    inline = [t for t in tokens if t.type == "inline"][1]
    children = {c.type for c in inline.children or []}
    assert {
        "strong_open",
        "em_open",
        "s_open",
        "code_inline",
        "link_open",
        "footnote_ref",
    } <= children


def test_raw_html_is_text() -> None:
    tokens = parse("<b>x</b>\n")
    assert all(t.type != "html_block" for t in tokens)


def test_containers_of_any_name_nest_with_longer_fences() -> None:
    tokens = parse(":::: panel\n**F**\n\n::: cards dark\n- a\n:::\n::::\n\n:::\nno name\n:::\n")
    opened = [container(t) for t in tokens if t.type == CONTAINER_OPEN]
    assert opened == [("panel", ""), ("cards", "dark")]
    assert sum(t.type == CONTAINER_CLOSE for t in tokens) == 2
    # A fence without a name is no container but text.
    assert any(t.type == "inline" and t.content.startswith(":::") for t in tokens)


def test_marks_are_tokens() -> None:
    inline = next(
        t for t in parse("Some ==marked== text, a=b and ===x===.\n") if t.type == "inline"
    )
    children = inline.children or []
    assert [c.type for c in children][:5] == ["text", "mark_open", "text", "mark_close", "text"]
    assert children[2].content == "marked"
    assert "a=b" in "".join(c.content for c in children)


def test_alerts_lose_their_marker_and_keep_the_kind() -> None:
    tokens = parse("> [!note]\n> **Fair:** text\n\n> [!WARNING]\n>\n> later\n\n> [!TIP] inline\n")
    quotes = [t for t in tokens if t.type == "blockquote_open"]
    assert [q.meta.get(ALERT) for q in quotes] == ["NOTE", "WARNING", None]
    inlines = [t for t in tokens if t.type == "inline"]
    assert inlines[0].content == "**Fair:** text"
    assert inlines[0].map == [1, 2]
    assert inlines[1].content == "later"
    assert inlines[2].content == "[!TIP] inline"
