"""SVG to PNG with resvg (extra ``svg``): any SVG, its text in the PTA fonts.

Port of DocLibs ``SvgConverter.cs``. Every SVG goes through ``sanitizer.clean`` first, so nothing
outside it is loaded — no files, no web addresses, only ``data:`` URIs and its own elements — and
scripts never run (resvg has none). resvg loads no system fonts unless asked: the text is set in
the fonts shipped with the package (``design.fonts.bundled``: Selawik, Inconsolata, Gelasio),
the generic families and every missing family point to Selawik (``monospace`` to Inconsolata),
so the same SVG gives the same PNG on every machine.
"""

from __future__ import annotations

import math
import re
from contextlib import ExitStack
from dataclasses import dataclass
from importlib import resources
from typing import Final

from lxml import etree

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.svg import sanitizer

MAX_PIXELS: Final = 16384
"""The largest side, in pixels, a PNG may have: beyond it the image would take gigabytes."""

DEFAULT_SCALE: Final = 2.0
"""Pixels per pixel of the natural size: sharp on high-density screens and when enlarged."""

SANS_SERIF: Final = "Selawik"
"""The family of ``sans-serif``, of text without a family and of every family that is missing:
resvg sets those in ``serif``, which therefore points here as well (Gelasio, the only serif
face, is italic and only for quotes)."""
MONOSPACE: Final = "Inconsolata"

PIXELS_PER_UNIT: Final = {
    "": 1.0,
    "px": 1.0,
    "pt": 96 / 72,
    "pc": 16.0,
    "mm": 96 / 25.4,
    "cm": 96 / 2.54,
    "in": 96.0,
}
"""CSS pixels (96 dpi) per unit of a ``width`` or ``height``."""

_LENGTH: Final = re.compile(r"\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*([a-zA-Z%]*)\s*")
_COLOR: Final = re.compile(r"[0-9A-Fa-f]{6}")


@dataclass(frozen=True, slots=True)
class PngOptions:
    """How ``to_png`` draws a PNG."""

    scale: float = DEFAULT_SCALE
    """Pixels per pixel of the SVG's natural size."""
    width: int | None = None
    """The PNG's width in pixels, the height following; overrides ``scale``."""
    background: str | None = None
    """A colour filling the PNG first, as ``RRGGBB`` (``design.colors``); None: transparent."""
    system_fonts: bool = False
    """Also load the system's fonts (Segoe UI where installed): the PNG then depends on the
    machine. Default off."""


def natural_size(svg: bytes | str) -> tuple[float, float]:
    """The SVG's natural size in CSS pixels: its ``width`` and ``height`` (px, pt, pc, mm, cm,
    in), else its ``viewBox``; one of them with the ``viewBox``'s proportions.

    Raises ``DocumentConversionError`` (format SVG) when it cannot be read or has no size.
    """
    return _size(_root(sanitizer.clean(svg)))


def to_png(svg: bytes | str, options: PngOptions | None = None) -> bytes:
    """The SVG as a PNG, at ``options.scale`` times its natural size or ``options.width`` wide.

    Raises ``DocumentConversionError`` (format SVG) when it cannot be read or drawn, has no
    size, or would be larger than ``MAX_PIXELS`` a side; ``ValueError`` for a scale that is not
    a positive number or a background that is not ``RRGGBB``.
    """
    options = options or PngOptions()
    clean = sanitizer.clean(svg)
    width, height = _size(_root(clean))
    scale = options.width / width if options.width is not None else options.scale
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError(f"the scale must be a positive number, not {scale}")
    if options.background is not None and not _COLOR.fullmatch(options.background):
        raise ValueError(f"'{options.background}' is not a colour; expected 'RRGGBB'")
    if width * scale > MAX_PIXELS or height * scale > MAX_PIXELS:
        raise _error(
            f"{round(width * scale)} × {round(height * scale)} pixels is larger than "
            f"{MAX_PIXELS} pixels a side"
        )
    import resvg_py  # extra "svg"

    from pta_documents.design import fonts  # not at import: the core never loads it

    with ExitStack() as stack:
        font_files = [
            str(stack.enter_context(resources.as_file(resources.files(fonts) / name)))
            for name in fonts.BUNDLED_FILES
        ]
        try:
            return resvg_py.svg_to_bytes(
                svg_string=clean,
                zoom=None if options.width is not None else scale,
                width=options.width,
                background=f"#{options.background}" if options.background else None,
                skip_system_fonts=not options.system_fonts,
                font_files=font_files,
                font_family=SANS_SERIF,
                sans_serif_family=SANS_SERIF,
                serif_family=SANS_SERIF,
                monospace_family=MONOSPACE,
                cursive_family=SANS_SERIF,
                fantasy_family=SANS_SERIF,
            )
        except ValueError as error:
            raise _error(str(error) or "it could not be drawn") from error


def _root(clean: str) -> etree._Element:
    return etree.fromstring(clean.encode("utf-8"), etree.XMLParser(resolve_entities=False))


def _size(root: etree._Element) -> tuple[float, float]:
    width = _length(root.get("width"))
    height = _length(root.get("height"))
    box = _view_box(root.get("viewBox"))
    if width is None and box is not None:
        width = height * box[0] / box[1] if height is not None else box[0]
    if height is None and box is not None:
        height = width * box[1] / box[0] if width is not None else box[1]
    if width is None or height is None or width <= 0 or height <= 0:
        raise _error("it has no size: give it width and height, or a viewBox")
    return width, height


def _length(value: str | None) -> float | None:
    """A ``width`` or ``height`` in CSS pixels; None when missing, relative (``%``, ``em``) or
    not a length."""
    if value is None:
        return None
    match = _LENGTH.fullmatch(value)
    if match is None:
        return None
    factor = PIXELS_PER_UNIT.get(match.group(2).lower())
    if factor is None:
        return None
    number = float(match.group(1)) * factor
    return number if math.isfinite(number) and number > 0 else None


def _view_box(value: str | None) -> tuple[float, float] | None:
    """Width and height of a ``viewBox``; None when missing or not four numbers."""
    if value is None:
        return None
    parts = value.replace(",", " ").split()
    try:
        numbers = [float(part) for part in parts]
    except ValueError:
        return None
    if len(numbers) != 4 or not all(math.isfinite(n) for n in numbers):
        return None
    if numbers[2] <= 0 or numbers[3] <= 0:
        return None
    return numbers[2], numbers[3]


def _error(reason: str) -> DocumentConversionError:
    return DocumentConversionError(DocumentFormat.SVG, f"The SVG cannot be converted: {reason}.")
