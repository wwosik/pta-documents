"""The front matter: a ``---`` block of ``key: value`` lines at the very top of the Markdown.

It looks like YAML but is only a flat subset: no nesting, no lists. An opening ``---`` followed
by a blank line is a thematic break, not front matter. Keys are matched case-insensitively.
Keys and values are German (decision 2026-11-06); mistakes raise ``DocumentConversionError``
with the generator's format and the list of valid keys or values.
"""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Final

from pta_documents.design.colors import StatusCategory
from pta_documents.errors import DocumentConversionError, DocumentFormat


class Keys:
    """The front matter keys the generators know."""

    TEMPLATE: Final = "vorlage"
    TITLE: Final = "titel"
    SUBTITLE: Final = "untertitel"
    AUTHOR: Final = "autor"
    LOCATION: Final = "ort"
    DATE: Final = "datum"
    COMPANY: Final = "firma"
    LANGUAGE: Final = "sprache"
    TOC: Final = "inhaltsverzeichnis"
    FOOTER: Final = "fusszeile"
    TITLE_SLIDE: Final = "titelfolie"
    TYPOGRAPHY: Final = "typografie"
    HIGHLIGHT: Final = "syntaxhervorhebung"
    MARKING: Final = "kennzeichnung"
    """``vertraulich``, ``intern``, ``entwurf`` or ``kein`` (``design.variants.Marking``); on
    slides the sticker (E04-S05)."""
    CHECK: Final = "pruefung"
    """``./run.sh check``: ``aus`` turns the style rules off, a list of ``style-…`` codes only
    those (E08-S02); the generators accept and ignore it."""
    BUILD: Final = "aufbau"
    """``listen``: on slides every list not inside another appears item by item (E09-S02);
    ``nein`` (the default): only what ``{.build}`` marks."""
    BUILD_LISTS: Final = "listen"
    TRANSITION: Final = "uebergang"
    """On slides the transition of every slide (E09-S03): ``none`` (the default), ``fade``,
    ``push`` … (``generation.common.slide_transition``)."""
    PROGRESS: Final = "fortschritt"
    """Only in the HTML deck (E10-S01): ``ja`` (the default) shows the progress bar."""
    CHAPTERS: Final = "kapitelanzeige"
    """Only in the HTML deck (E10-S01): ``ja`` (the default) shows the chapters above the
    slide, the current one marked."""
    STATUS_PREFIX: Final = "status."


YES: Final = "ja"
NO: Final = "nein"

_ENTRY = re.compile(r"^\s*([A-Za-z][A-Za-z0-9.]*)\s*:(.*)$")
_ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_GERMAN_DATE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$")


@dataclass(frozen=True)
class FrontMatter:
    body: str
    """The Markdown without the front matter."""
    body_line: int
    """How many lines the front matter takes: line n of ``body`` is line n + body_line."""
    entries: tuple[tuple[str, str], ...]
    format: DocumentFormat

    @classmethod
    def read(cls, markdown: str, format: DocumentFormat) -> FrontMatter:
        lines = markdown.split("\n")
        if len(lines) < 2 or _line(lines[0]) != "---" or not _line(lines[1]).strip():
            return cls(markdown, 0, (), format)
        entries: list[tuple[str, str]] = []
        for i in range(1, len(lines)):
            line = _line(lines[i])
            if line in ("---", "..."):
                return cls("\n".join(lines[i + 1 :]), i + 1, tuple(entries), format)
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            match = _ENTRY.match(line)
            if match is None:
                raise DocumentConversionError(
                    format, f"The front matter line '{line.strip()}' is not 'key: value'."
                )
            key = match.group(1)
            if any(k.lower() == key.lower() for k, _ in entries):
                raise DocumentConversionError(
                    format, f"The front matter key '{key}' appears twice."
                )
            value = _unquote(match.group(2).strip())
            if not value:
                raise DocumentConversionError(format, f"The front matter key '{key}' has no value.")
            entries.append((key, value))
        raise DocumentConversionError(
            format, "The front matter that starts on the first line is never closed by '---'."
        )

    def get(self, key: str) -> str | None:
        return next((v for k, v in self.entries if k.lower() == key.lower()), None)

    def check_keys(self, valid: Sequence[str], allow_status: bool = False) -> None:
        """Raise for a key that is not in ``valid`` (or ``status.*`` when allowed)."""
        for key, _ in self.entries:
            if allow_status and key.lower().startswith(Keys.STATUS_PREFIX):
                continue
            if key.lower() not in (v.lower() for v in valid):
                listed = [*valid, *([Keys.STATUS_PREFIX + "<kategorie>"] if allow_status else [])]
                raise self.error(
                    f"The front matter key '{key}' is not supported here. "
                    f"Valid keys: {', '.join(listed)}."
                )

    def boolean(self, key: str) -> bool | None:
        value = self.get(key)
        if value is None:
            return None
        return self.one_of(key, value, ((YES, True), (NO, False)))

    def one_of[T](self, key: str, value: str, choices: Iterable[tuple[str, T]]) -> T:
        choices = list(choices)
        for choice, result in choices:
            if choice.lower() == value.strip().lower():
                return result
        expected = " or ".join(f"'{c}'" for c, _ in choices)
        raise self.error(
            f"The front matter key '{key}' has the value '{value}'; expected {expected}."
        )

    def date(self, key: str = Keys.DATE) -> dt.date | None:
        """A date written as ``JJJJ-MM-TT`` or ``TT.MM.JJJJ``."""
        value = self.get(key)
        if value is None:
            return None
        try:
            if match := _ISO_DATE.match(value):
                return dt.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            if match := _GERMAN_DATE.match(value):
                return dt.date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
        except ValueError:
            pass
        raise self.error(
            f"The front matter key '{key}' has the value '{value}'; "
            "expected a date like '2026-11-06' or '06.11.2026'."
        )

    def status_labels(self) -> dict[str, StatusCategory]:
        """Label texts assigned by ``status.<kategorie>: Text; Text`` keys."""
        labels: dict[str, StatusCategory] = {}
        for key, value in self.entries:
            if not key.lower().startswith(Keys.STATUS_PREFIX):
                continue
            name = key[len(Keys.STATUS_PREFIX) :].lower()
            category = next((c for c in StatusCategory if c.value == name), None)
            if category is None:
                valid = ", ".join(Keys.STATUS_PREFIX + c.value for c in StatusCategory)
                raise self.error(
                    f"The front matter key '{key}' names no status category. Valid keys: {valid}."
                )
            for label in (part.strip() for part in value.split(";")):
                if not label:
                    continue
                if label in labels:
                    raise self.error(
                        f"The label '{label}' is assigned to two categories in the front matter."
                    )
                labels[label] = category
        return labels

    def error(self, reason: str) -> DocumentConversionError:
        return DocumentConversionError(self.format, reason)


def _line(line: str) -> str:
    return line.rstrip("\r").rstrip()


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
        return value[1:-1]
    return value
