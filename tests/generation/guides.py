"""Test helpers for the authoring guides (E02-S05), for the tests of each generator's guide
(E03-S05, E04-S06, E05-S05). Compare a guide with its ``*.expected.md`` through
``tests.expected.assert_matches_expected``."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from typing import Final

from pta_documents.generation.common.authoring_guides import WORD_LIMIT, words

EXAMPLE: Final = re.compile(
    r"^(?P<fence>`{3,})markdown\n(?P<body>.*?)\n(?P=fence)$", re.MULTILINE | re.DOTALL
)
"""A ```` ```markdown ```` block of a guide; the fence may be longer, so that it can hold
blocks of its own (port of the ``ExamplePattern`` of DocLibs)."""


def examples(guide: str) -> list[str]:
    """The Markdown of every ```` ```markdown ```` block of ``guide``, each ending with a line
    break."""
    return [m.group("body") + "\n" for m in EXAMPLE.finditer(guide)]


def assert_examples_generate(
    guide: str, generate: Callable[[str], object], *, at_least: int = 1
) -> None:
    """Generate every example of ``guide`` with ``generate`` (which raises on an error); there
    have to be ``at_least`` of them. Examples that are not documents of their own (only the
    front matter block, a fragment) the caller filters before."""
    found = examples(guide)
    assert len(found) >= at_least, f"{len(found)} examples in the guide"
    for example in found:
        try:
            generate(example)
        except Exception as error:
            raise AssertionError(f"This example of the guide fails: {error}\n{example}") from error


def assert_names_everything(guide: str, names: Iterable[str]) -> None:
    """``guide`` contains every one of ``names`` verbatim (``::: cards``, `` `vorlage` ``)."""
    missing = [name for name in names if name not in guide]
    assert missing == [], f"the authoring guide does not name: {', '.join(missing)}"


def assert_under(guide: str, limit: int = WORD_LIMIT) -> None:
    """``guide`` has fewer than ``limit`` words."""
    count = words(guide)
    assert count < limit, f"the authoring guide has {count} words, {limit} at most"
