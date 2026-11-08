from __future__ import annotations

import pytest

from pta_documents.markdown.anchors import Anchors, slug


@pytest.mark.parametrize(
    ("text", "anchor"),
    [
        ("Results", "results"),
        ("A sub-heading", "a-sub-heading"),
        ("Größe & Maß", "größe--maß"),
        ("  Kapitel 1.2: Ziele!  ", "kapitel-12-ziele"),
        ("snake_case `code`", "snake_case-code"),
    ],
)
def test_slug_is_the_github_anchor(text: str, anchor: str) -> None:
    assert slug(text) == anchor


def test_repeated_headings_get_numbers() -> None:
    anchors = Anchors()
    assert [anchors.add(t) for t in ("Ziel", "Ziel", "Ziel 1", "Ziel")] == [
        "ziel",
        "ziel-1",
        "ziel-1-1",
        "ziel-2",
    ]
