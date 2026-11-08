"""Minutes and clock times as authors write them (E16-S02): ``dauer=5``, ``laenge: 4h``,
``beginn: 09:00``.

A duration is whole minutes (``90``), hours (``4h``) or hours and minutes (``1h30``); a clock
time is ``HH:MM`` on a 24-hour clock. Mistakes raise ``DocumentConversionError`` with an
example of what is meant.
"""

from __future__ import annotations

import re
from typing import Final

from pta_documents.errors import DocumentConversionError, DocumentFormat

_MINUTES: Final = re.compile(r"^\s*(\d+)\s*(?:min)?\s*$", re.IGNORECASE)
_HOURS: Final = re.compile(r"^\s*(\d+)\s*h\s*(?:(\d{1,2})\s*(?:min)?)?\s*$", re.IGNORECASE)
_CLOCK: Final = re.compile(r"^\s*(\d{1,2})[:.](\d{2})\s*(?:uhr)?\s*$", re.IGNORECASE)
MINUTES_PER_HOUR: Final = 60
HOURS_PER_DAY: Final = 24
MINUTES_PER_DAY: Final = HOURS_PER_DAY * MINUTES_PER_HOUR


def parse_minutes(value: str, what: str, format: DocumentFormat) -> int:
    """The minutes of ``value`` (``5``, ``90``, ``4h``, ``1h30``); ``what`` names the value in
    the error (``The heading attribute dauer=x``)."""
    minutes: int | None = None
    if match := _MINUTES.match(value):
        minutes = int(match.group(1))
    elif match := _HOURS.match(value):
        rest = int(match.group(2) or 0)
        if rest < MINUTES_PER_HOUR:
            minutes = int(match.group(1)) * MINUTES_PER_HOUR + rest
    if minutes is None or minutes <= 0:
        raise DocumentConversionError(
            format,
            f"{what} is no length of time; write minutes or hours and minutes, like '5', '90', "
            "'4h' or '1h30' (more than 0).",
        )
    return minutes


def parse_clock(value: str, what: str, format: DocumentFormat) -> int:
    """The minutes after midnight of ``value`` (``09:00``, ``9:30``)."""
    match = _CLOCK.match(value)
    if match is not None:
        hours, minutes = int(match.group(1)), int(match.group(2))
        if hours < HOURS_PER_DAY and minutes < MINUTES_PER_HOUR:
            return hours * MINUTES_PER_HOUR + minutes
    raise DocumentConversionError(
        format, f"{what} is no time of day; write it like '09:00' or '13:30'."
    )


def clock(minutes: int) -> str:
    """``09:05`` for 545 minutes after midnight (past midnight it starts again at 00:00)."""
    minutes %= MINUTES_PER_DAY
    return f"{minutes // MINUTES_PER_HOUR:02d}:{minutes % MINUTES_PER_HOUR:02d}"


def offset(minutes: int) -> str:
    """``+0:15`` for 15 minutes after the start (no start time given)."""
    return f"+{minutes // MINUTES_PER_HOUR}:{minutes % MINUTES_PER_HOUR:02d}"
