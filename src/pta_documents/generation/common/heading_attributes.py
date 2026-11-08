"""Attributes at the end of a heading: ``# Danke {.closing}``, ``## Folie {.dark kicker="Why"}``.

Port of DocLibs ``HeadingAttributes``. Only a trailing ``{…}`` made of classes and
``key="value"`` pairs counts; any other braces stay text (``## Sets {a, b}``). Which heading
takes which attribute is ``check_level``'s business: ``.closing`` goes on ``#``, ``.dark``,
``kicker`` and the PTA slide kinds (``.agenda``, ``.interim``, ``.quote``, ``.contact``, E04-S04)
on ``##``, ``layout``, ``uebergang`` (the slide transition, E09-S03) and ``.internal`` (the
chapter or slide only in the internal and trainer version, E16-S01) on both.
``dauer=5`` (minutes, or ``1h30``; the one value that needs no quotes) plans the time of a slide
or chapter, ``.break`` makes a ``##`` a break of the training schedule (a slide kind, E16-S02,
``training_schedule``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.durations import parse_minutes
from pta_documents.generation.common.slide_transition import SlideTransition

AGENDA: Final = "agenda"
"""PTA: ``## Agenda {.agenda}``, the agenda slide (never made without it, E04-S04)."""
INTERIM: Final = "interim"
"""PTA: ``## Statement {.interim}``, the interim conclusion slide (Zwischenfazit)."""
QUOTE: Final = "quote"
"""PTA: ``## Quote {.quote}``, the quote slide (Zitat)."""
CONTACT: Final = "contact"
"""PTA: ``## Contacts {.contact}``, the contact slide (one ``###`` per person)."""
BREAK: Final = "break"
"""``## Pause {.break dauer=15}``: a break of the training schedule (E16-S02), shown on the
interim conclusion layout as "Pause · 15 min"."""
SLIDE_KINDS: Final = (AGENDA, INTERIM, QUOTE, CONTACT, BREAK)
"""The PTA slide kinds of a ``##`` heading: one at most, not with ``.dark`` or ``kicker``."""

VALID: Final = (
    '.closing, .dark, kicker="…", layout="…", uebergang="…", .agenda, .interim, .quote, .contact, '
    ".internal, dauer=…, .break"
)
"""Every heading attribute, as it is written, for error messages."""
VALID_ON_SECTION: Final = '.closing, layout="…", uebergang="…", .internal, dauer=…'
"""The attributes of a ``#`` heading."""
VALID_ON_SLIDE: Final = (
    '.dark, kicker="…", layout="…", uebergang="…", .agenda, .interim, .quote, .contact, .internal'
    ", dauer=…, .break"
)
"""The attributes of a ``##`` heading."""

DURATION: Final = "dauer"
"""``dauer=5``: the only attribute whose value may go without quotes (E16-S02)."""
_BARE: Final = rf'{DURATION}=[^\s"{{}}]+'
_BLOCK: Final = re.compile(
    rf'\s*\{{((?:\s*(?:\.[A-Za-z][\w-]*|[A-Za-z][\w-]*="[^"]*"|{_BARE}))+)\s*\}}\s*$'
)
_TOKEN: Final = re.compile(
    r'\.(?P<cls>[A-Za-z][\w-]*)|(?P<key>[A-Za-z][\w-]*)="(?P<value>[^"]*)"'
    rf'|(?P<bare_key>{DURATION})=(?P<bare>[^\s"{{}}]+)'
)
DURATION_EXAMPLE: Final = "dauer=5 or dauer=1h30"


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
    internal: bool = False
    """``.internal`` (E16-S01): the chapter (``#``) or slide (``##``) only in the internal and
    the trainer version (``generation.common.audience``)."""
    duration: int | None = None
    """``dauer=5`` (E16-S02): the minutes planned for the slide, or for the chapter (``#``), whose
    slides without one share what is left; None: not planned."""
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
    closing = dark = internal = False
    layout: str | None = None
    kicker: str | None = None
    kind: str | None = None
    transition: SlideTransition | None = None
    duration: int | None = None
    for token in _TOKEN.finditer(match.group(1)):
        name = (
            "." + token.group("cls")
            if token.group("cls")
            else token.group("key") or token.group("bare_key")
        )
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
            case ".internal":
                internal = True
            case "layout":
                layout = token.group("value")
            case "kicker":
                kicker = token.group("value")
            case "uebergang":
                transition = SlideTransition.parse(token.group("value"), format)
            case "dauer":
                value = token.group("value") if token.group("key") else token.group("bare")
                duration = parse_minutes(value, f"The heading attribute dauer={value}", format)
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
        internal=internal,
        duration=duration,
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
    if attributes.kind == BREAK and attributes.duration is None:
        raise DocumentConversionError(
            format,
            f"The break in '{attributes.block}' needs its length: '## Pause {{.break dauer=15}}'.",
        )
    if attributes.closing and attributes.duration is not None:
        raise DocumentConversionError(
            format,
            f"The closing slide '{attributes.block}' comes after the schedule; leave out dauer.",
        )
    if attributes.kind is not None and (attributes.dark or attributes.kicker is not None):
        other = ".dark" if attributes.dark else "kicker"
        raise DocumentConversionError(
            format,
            f"The slide kind .{attributes.kind} in '{attributes.block}' has the PTA layout's "
            f"own design and takes no {other}. Leave out {other}.",
        )
