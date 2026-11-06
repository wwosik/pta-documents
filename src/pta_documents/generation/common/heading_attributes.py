"""Attributes at the end of a heading: ``# Danke {.closing}``, ``## Folie {layout="Nur Titel"}``.

Port of DocLibs ``HeadingAttributes``; the flow-layout attributes (``.dark``, ``kicker``) come
with E04-S03.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from pta_documents.errors import DocumentConversionError, DocumentFormat

VALID: Final = '.closing, layout="…"'

_BLOCK: Final = re.compile(r'\s*\{((?:\s*(?:\.[A-Za-z][\w-]*|[A-Za-z][\w-]*="[^"]*"))+)\s*\}\s*$')
_TOKEN: Final = re.compile(r'\.(?P<cls>[A-Za-z][\w-]*)|(?P<key>[A-Za-z][\w-]*)="(?P<value>[^"]*)"')


@dataclass(frozen=True)
class HeadingAttributes:
    closing: bool = False
    layout: str | None = None


def split(text: str, format: DocumentFormat) -> tuple[str, HeadingAttributes | None]:
    """The heading text without its attributes, and the attributes (None if there are none)."""
    match = _BLOCK.search(text)
    if match is None:
        return text, None
    closing = False
    layout: str | None = None
    for token in _TOKEN.finditer(match.group(1)):
        name = "." + token.group("cls") if token.group("cls") else token.group("key")
        if name == ".closing":
            closing = True
        elif name == "layout" and layout is None:
            layout = token.group("value")
        elif name == "layout":
            raise DocumentConversionError(
                format, f"The heading attributes '{match.group(0).strip()}' name layout twice."
            )
        else:
            raise DocumentConversionError(
                format,
                f"Unknown heading attribute '{name}' in '{match.group(0).strip()}'. "
                f"Valid attributes: {VALID}.",
            )
    return text[: match.start()].rstrip(), HeadingAttributes(closing, layout)
