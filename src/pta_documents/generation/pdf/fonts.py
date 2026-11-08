"""The fonts of the PDF: measuring for the layout, embedding for the renderer.

The files come from ``design.fonts`` (E01-S03): Segoe UI, Consolas and Georgia from the system
when complete, otherwise Selawik, Inconsolata and Gelasio. The faces are those of
``design.fonts.FontFace``; tables use the text faces, as in Word.

reportlab keeps a process-wide list of registered fonts. Each file is registered under a name
made from its content hash (``PTA-<sha8>``), so whatever else is registered there never changes
a document, and the same file is registered — and embedded — once.
"""

from __future__ import annotations

import hashlib
import io
from typing import Final, Protocol

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from pta_documents.design.fonts import FontFace, FontFile, FontSet

NAME_PREFIX: Final = "PTA-"


class FontMetrics(Protocol):
    """What the layout needs to know about the fonts; tests pass invented widths."""

    def width(self, text: str, face: FontFace, size: float) -> float:
        """The advance width of ``text`` in points, without kerning."""
        ...

    def has_glyph(self, char: str, face: FontFace) -> bool:
        """Whether ``face`` can show ``char`` (one character)."""
        ...


def registered_name(file: FontFile) -> str:
    """The reportlab name of ``file``: ``PTA-`` and the first 8 hex digits of its SHA-256."""
    return NAME_PREFIX + hashlib.sha256(file.content).hexdigest()[:8]


class PdfFonts:
    """A ``FontSet`` measured for the layout and registered with reportlab for the renderer."""

    def __init__(self, fonts: FontSet) -> None:
        self.fonts = fonts
        self._names: dict[FontFace, str] = {}
        known = set(pdfmetrics.getRegisteredFontNames())
        for face in FontFace:
            file = fonts.file(face)
            name = registered_name(file)
            if name not in known:
                pdfmetrics.registerFont(TTFont(name, io.BytesIO(file.content)))
                known.add(name)
            self._names[face] = name

    def width(self, text: str, face: FontFace, size: float) -> float:
        return self.fonts.width(text, face, size)

    def has_glyph(self, char: str, face: FontFace) -> bool:
        return len(char) == 1 and self.fonts.has_glyph(ord(char), face)

    def name(self, face: FontFace) -> str:
        """The name the renderer sets the face by."""
        return self._names[face]

    def synthetic_italic(self, face: FontFace) -> bool:
        """Whether the renderer must slant the face (Selawik has no italics)."""
        return self.fonts.file(face).synthetic_italic
