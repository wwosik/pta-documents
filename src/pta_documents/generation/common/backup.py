"""Backup slides and appendices (E16-S04): ``# Backup {.backup}`` and ``# Glossar {.appendix}``.

Both attributes go on a ``#`` heading and make it and every chapter after it something else: in a
deck the backup behind the closing slide (no chapter number, not on the agenda), in Word and PDF
the appendices lettered A, B, C. Each format ignores the other's attribute with the note
``attribute-ignored``; ``check`` (called by ``layout_syntax.check``) rejects the same mistakes in
every format: either attribute twice, one inside a container, a closing slide after the backup,
and a break or ``dauer`` (E16-S02) behind the closing slide or in the backup, which the training
schedule does not plan.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final, NoReturn

from markdown_it.token import Token

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import heading_attributes
from pta_documents.generation.common.result import NoteCodes, Notes
from pta_documents.markdown.parser import line_of

BACKUP: Final = ".backup"
APPENDIX: Final = ".appendix"


def check(tokens: Sequence[Token], format: DocumentFormat, line_offset: int = 0) -> None:
    """Raise, with the line in front (``Line 12: …``), for ``{.backup}`` or ``{.appendix}``
    named twice or on a heading in a container, for a ``{.closing}`` after ``{.backup}``, and for
    ``{.break}`` or ``dauer=…`` from the closing slide or the backup on."""
    backup: int | None = None
    appendix: int | None = None
    behind: str | None = None
    """What ends the training schedule (E16-S02): the closing slide or the backup."""
    for i, token in enumerate(tokens):
        if token.type != "heading_open" or token.tag not in ("h1", "h2"):
            continue
        children = tokens[i + 1].children or []
        if not children or children[-1].type != "text":
            continue
        _, attributes = heading_attributes.split(children[-1].content, format)
        if attributes is None:
            continue
        line = line_of(token, line_offset) or 0
        if token.level == 0 and behind is None:
            if attributes.closing:
                behind = "behind the closing slide {.closing}"
            elif attributes.backup:
                behind = "in the backup {.backup}"
        if token.level == 0 and behind is not None:
            _check_unplanned(attributes, behind, format, line)
        if token.tag != "h1":
            continue
        for name, flag, first in (
            (BACKUP, attributes.backup, backup),
            (APPENDIX, attributes.appendix, appendix),
        ):
            if not flag:
                continue
            if token.level != 0:
                _raise(
                    format,
                    line,
                    f"{{{name}}} goes on a '#' heading of the document itself, not on one in a "
                    "container.",
                )
            if first is not None:
                what = "backup" if name == BACKUP else "appendix"
                _raise(
                    format,
                    line,
                    f"{{{name}}} is on line {first} already. It goes on the first chapter of the "
                    f"{what} only: every chapter after it belongs to the {what}.",
                )
        if attributes.backup and backup is None:
            backup = line
        if attributes.appendix and appendix is None:
            appendix = line
        if attributes.closing and backup is not None:
            _raise(
                format,
                line,
                f"The closing slide {{.closing}} goes before the backup ({{.backup}} on line "
                f"{backup}): the backup slides stand behind the closing slide.",
            )


def _check_unplanned(
    attributes: heading_attributes.HeadingAttributes,
    behind: str,
    format: DocumentFormat,
    line: int,
) -> None:
    """Raise for a break or a ``dauer`` behind the closing slide or in the backup: the training
    schedule (E16-S02) ends before them, so it would plan neither (Entscheidung 2026-11-08: a
    mistake rather than silently left out)."""
    if attributes.kind == heading_attributes.BREAK:
        _raise(
            format,
            line,
            f"The break '{attributes.block}' stands {behind}, where nothing is planned any "
            "more: put it before the closing slide, or make it an ordinary slide.",
        )
    if attributes.duration is not None and not attributes.closing:
        _raise(
            format,
            line,
            f"The heading attributes '{attributes.block}' plan a length {behind}, where the "
            "schedule has ended: backup slides get no time. Leave out dauer.",
        )


def _raise(format: DocumentFormat, line: int, reason: str) -> NoReturn:
    prefix = f"Line {line}: " if line else ""
    raise DocumentConversionError(format, prefix + reason)


def note_ignored(
    notes: Notes, attributes: heading_attributes.HeadingAttributes, line: int | None, slides: bool
) -> None:
    """The note ``attribute-ignored`` for the attribute of the other kind of document:
    ``{.appendix}`` on ``slides``, ``{.backup}`` in Word and PDF."""
    if slides and attributes.appendix:
        notes.add(
            NoteCodes.ATTRIBUTE_IGNORED,
            line,
            "{.appendix} letters the chapters A, B, C in Word and PDF; slides have no "
            "appendices, the chapters stay chapters. For slides behind the closing slide use "
            "{.backup}.",
        )
    if not slides and attributes.backup:
        notes.add(
            NoteCodes.ATTRIBUTE_IGNORED,
            line,
            "{.backup} puts the chapters behind the closing slide of a deck; Word and PDF have "
            "no closing slide, the chapters stay chapters. For appendices A, B, C use "
            "{.appendix}.",
        )


def letters(number: int) -> str:
    """The number of an appendix as Word's ``upperLetter`` writes it: A … Z, then AA, BB …"""
    if number < 1:
        raise ValueError(number)
    return chr(ord("A") + (number - 1) % 26) * ((number - 1) // 26 + 1)
