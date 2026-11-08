from __future__ import annotations

from markdown_it.token import Token

from pta_documents.design.variants import TEXTS, Language
from pta_documents.generation.common import block_shapes
from pta_documents.markdown.parser import parse


def inline(markdown: str) -> Token:
    return next(t for t in parse(markdown) if t.type == "inline")


def test_only_strong() -> None:
    assert block_shapes.only_strong(inline("**ganz fett**").children or [])
    assert not block_shapes.only_strong(inline("**fett** und nicht").children or [])
    assert not block_shapes.only_strong(inline("**a** **b**").children or [])


def test_only_images() -> None:
    assert block_shapes.only_images(inline("![a](a.png)").children or [])
    assert block_shapes.only_images(inline("![a](a.png)\n![b](b.png)").children or [])
    assert not block_shapes.only_images(inline("Text ![a](a.png)").children or [])


def test_captions() -> None:
    texts = TEXTS[Language.EN]
    assert block_shapes.is_table_caption(inline("Tabelle: Werte"), texts)
    assert block_shapes.is_table_caption(inline("Table: Values"), texts)
    assert not block_shapes.is_table_caption(inline("Tabellen sind gut"), texts)
    assert block_shapes.is_figure_caption(inline("Abbildung: Bild"), texts)
    stripped = block_shapes.strip_caption_prefix(inline("Tabelle: **Werte** hier"))
    assert [c.content for c in stripped.children or []][:2] == ["", ""]
    assert (stripped.children or [])[2].content == "Werte"
