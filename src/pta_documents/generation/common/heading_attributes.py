"""Attributes at the end of a heading: ``# Danke {.closing}``, ``## Folie {.dark kicker="Why"}``.

Port of DocLibs ``HeadingAttributes``. Only a trailing ``{…}`` made of classes and
``key="value"`` pairs counts; any other braces stay text (``## Sets {a, b}``). Which heading
takes which attribute is ``check_level``'s business: ``.closing`` goes on ``#``, ``.dark``,
``kicker`` and the PTA slide kinds (``.agenda``, ``.interim``, ``.quote``, ``.contact``, E04-S04)
on ``##``, ``layout`` and ``uebergang`` (the slide transition, E09-S03) on both.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.slide_transition import SlideTransition

AGENDA: Final = "agenda"
"""PTA: ``## Agenda {.agenda}``, the agenda slide (never made without it, E04-S04)."""
INTERIM: Final = "interim"
"""PTA: ``## Statement {.interim}``, the interim conclusion slide (Zwischenfazit)."""
QUOTE: Final = "quote"
"""PTA: ``## Quote {.quote}``, the quote slide (Zitat)."""
CONTACT: Final = "contact"
"""PTA: ``## Contacts {.contact}``, the contact slide (one ``###`` per person)."""
SLIDE_KINDS: Final = (AGENDA, INTERIM, QUOTE, CONTACT)
"""The PTA slide kinds of a ``##`` heading: one at most, not with ``.dark`` or ``kicker``."""

VALID: Final = (
    '.closing, .dark, kicker="…", layout="…", uebergang="…", .agenda, .interim, .quote, .contact'
)
"""Every heading attribute, as it is written, for error messages."""
VALID_ON_SECTION: Final = '.closing, layout="…", uebergang="…"'
"""The attributes of a ``#`` heading."""
VALID_ON_SLIDE: Final = (
    '.dark, kicker="…", layout="…", uebergang="…", .agenda, .interim, .quote, .contact'
)
"""The attributes of a ``##`` heading."""

_BLOCK: Final = re.compile(r'\s*\{((?:\s*(?:\.[A-Za-z][\w-]*|[A-Za-z][\w-]*="[^"]*"))+)\s*\}\s*$')
_TOKEN: Final = re.compile(r'\.(?P<cls>[A-Za-z][\w-]*)|(?P<key>[A-Za-z][\w-]*)="(?P<value>[^"]*)"')


@dataclass(frozen=True)
class HeadingAttributes:
    closing: bool = False
    """On a ``#`` heading: the closing slide, on the template's closing layout."""
    layout: str | None = None
    """The template's layout to put the slide on, by its name; None: by kind of slide."""
    dark: bool = False
    """On a ``##`` heading: the slide on a dark background."""
    kicker: str | None = None
    """On a ``##`` heading: the small label above the title."""
    kind: str | None = None
    """On a ``##`` heading: the PTA slide kind (one of ``SLIDE_KINDS``); None: an ordinary
    slide."""
    transition: SlideTransition | None = None
    """``uebergang="…"`` (E09-S03): how the slide comes in; on a ``#`` heading for its slide and
    every slide of the chapter. None: the chapter's, else the deck's."""
    block: str = ""
    """The attributes as written (``{.dark kicker="Why"}``), for error messages."""


def split(text: str, format: DocumentFormat) -> tuple[str, HeadingAttributes | None]:
    """The heading text without its attributes, and the attributes (None if there are none).

    Raises ``DocumentConversionError`` for an unknown attribute or one named twice.
    """
    match = _BLOCK.search(text)
    if match is None:
        return text, None
    block = match.group(0).strip()
    seen: set[str] = set()
    closing = dark = False
    layout: str | None = None
    kicker: str | None = None
    kind: str | None = None
    transition: SlideTransition | None = None
    for token in _TOKEN.finditer(match.group(1)):
        name = "." + token.group("cls") if token.group("cls") else token.group("key")
        if name in seen:
            raise DocumentConversionError(
                format, f"The heading attributes '{block}' name {name} twice."
            )
        seen.add(name)
        match name:
            case ".closing":
                closing = True
            case ".dark":
                dark = True
            case "layout":
                layout = token.group("value")
            case "kicker":
                kicker = token.group("value")
            case "uebergang":
                transition = SlideTransition.parse(token.group("value"), format)
            case _ if name[1:] in SLIDE_KINDS and name.startswith("."):
                if kind is not None:
                    raise DocumentConversionError(
                        format,
                        f"The heading attributes '{block}' name the slide kinds .{kind} and "
                        f"{name}; a slide is one of them at most.",
                    )
                kind = name[1:]
            case _:
                raise DocumentConversionError(
                    format,
                    f"Unknown heading attribute '{name}' in '{block}'. Valid attributes: {VALID}.",
                )
    attributes = HeadingAttributes(
        closing=closing,
        layout=layout,
        dark=dark,
        kicker=kicker,
        kind=kind,
        transition=transition,
        block=block,
    )
    return text[: match.start()].rstrip(), attributes


def check_level(attributes: HeadingAttributes, level: int, format: DocumentFormat) -> None:
    """Raise for an attribute the heading ``level`` (1 for ``#``, 2 for ``##``) does not take."""
    if level == 1 and (attributes.dark or attributes.kicker is not None or attributes.kind):
        name = (
            ".dark" if attributes.dark else "kicker" if attributes.kicker is not None else ""
        ) or f".{attributes.kind}"
        raise DocumentConversionError(
            format,
            f"The heading attribute '{name}' in '{attributes.block}' goes on a '##' heading. "
            f"Valid attributes on '#': {VALID_ON_SECTION}.",
        )
    if level == 2 and attributes.closing:
        raise DocumentConversionError(
            format,
            f"{{.closing}} goes on a '#' heading: the closing slide. "
            f"Valid attributes on '##': {VALID_ON_SLIDE}.",
        )
    if attributes.kind is not None and (attributes.dark or attributes.kicker is not None):
        other = ".dark" if attributes.dark else "kicker"
        raise DocumentConversionError(
            format,
            f"The slide kind .{attributes.kind} in '{attributes.block}' has the PTA layout's "
            f"own design and takes no {other}. Leave out {other}.",
        )
