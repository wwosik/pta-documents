from __future__ import annotations

from pta_documents.errors import DocumentFormat
from pta_documents.markdown.front_matter import FrontMatter
from pta_documents.markdown.parser import line_of, parse

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
