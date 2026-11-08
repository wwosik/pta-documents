"""The faces of a ``FontSet`` registered with reportlab, under names from their content.

reportlab keeps registered fonts in a process-wide table. Each face is registered under
``PTA-<first 8 hex digits of the SHA-256 of its file>`` (a slanted face: of the slanted file), so
the same file always has the same name and two font sets never clash: the table never changes
what a document looks like. Registering a face twice is a no-op.

Before registering, ``ALIASES`` lend missing characters the glyph of a similar one. Faces with
``synthetic_italic`` (Selawik has no italics) are slanted by
``SYNTHETIC_ITALIC_ANGLE`` with ``truetype.slanted``, because reportlab's paragraphs cannot slant
text themselves.
"""

from __future__ import annotations

import hashlib
import io
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from typing import Final

from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from pta_documents.design.fonts import SYNTHETIC_ITALIC_ANGLE, FontFace, FontFile, FontSet, truetype

PREFIX: Final = "PTA-"
MISSING: Final = "?"
"""What a character the faces lack becomes: PDF/A forbids ``.notdef`` (the generator notes
it, ``character-missing``; E05-S04 brings ``replace_unsupported``)."""
TEXT_FACES: Final = (FontFace.REGULAR, FontFace.BOLD)
CODE_FACES: Final = (FontFace.MONO,)
ALIASES: Final = {0x00A0: 0x0020, 0x202F: 0x0020, 0x2011: 0x002D}
"""Characters a face may lack that look like others: no-break spaces like the space, the
no-break hyphen like the hyphen (the typography of E17-S02 sets U+00A0, which Selawik lacks).
They keep their meaning for the line breaking; only the glyph is borrowed."""


@dataclass(frozen=True)
class PdfFonts:
    """The reportlab names of the faces of ``fonts``; ``text`` and ``mono`` are the family
    names paragraph markup (``<b>``, ``<i>``) resolves over."""

    fonts: FontSet
    names: Mapping[FontFace, str]
    text: str
    mono: str

    def name(self, face: FontFace) -> str:
        return self.names[face]

    def width(self, text: str, face: FontFace, size_pt: float) -> float:
        """The width of ``text`` in points as reportlab sets it."""
        return pdfmetrics.stringWidth(text, self.names[face], size_pt)

    def line_height(self, face: FontFace = FontFace.REGULAR) -> float:
        """A single line of ``face`` as a multiple of the font size, as Word measures it."""
        return self.fonts.file(face).info.line_height

    def has_glyph(self, code_point: int, face: FontFace) -> bool:
        return code_point in ALIASES or self.fonts.has_glyph(code_point, face)

    def shown(self, text: str, code: bool = False) -> str:
        """``text`` with every character the text faces (``code``: the code face) lack as
        ``MISSING``, white space as a space."""
        faces = CODE_FACES if code else TEXT_FACES
        if all(self._has(c, faces) for c in text):
            return text
        return "".join(
            c if self._has(c, faces) else (" " if c.isspace() else MISSING) for c in text
        )

    def _has(self, char: str, faces: tuple[FontFace, ...]) -> bool:
        code = ord(char)
        return all(self.has_glyph(code, face) for face in faces)


def register(fonts: FontSet) -> PdfFonts:
    """Register every face of ``fonts`` (and the families) with reportlab."""
    names = {face: _register(fonts.file(face)) for face in FontFace}
    text = names[FontFace.REGULAR]
    mono = names[FontFace.MONO]
    _family(text, names[FontFace.REGULAR], names[FontFace.BOLD])
    addMapping(text, 0, 1, names[FontFace.ITALIC])
    addMapping(text, 1, 1, names[FontFace.BOLD_ITALIC])
    _family(mono, names[FontFace.MONO], names[FontFace.MONO_BOLD])
    # Inconsolata has no italic: italic code stays upright.
    addMapping(mono, 0, 1, names[FontFace.MONO])
    addMapping(mono, 1, 1, names[FontFace.MONO_BOLD])
    return PdfFonts(fonts, names, text, mono)


def _family(family: str, regular: str, bold: str) -> None:
    addMapping(family, 0, 0, regular)
    addMapping(family, 1, 0, bold)


def _register(file: FontFile) -> str:
    content = _prepared(file.content, file.synthetic_italic)
    name = PREFIX + hashlib.sha256(content).hexdigest()[:8]
    if name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(name, io.BytesIO(content)))
    return name


@cache
def _prepared(content: bytes, slant: bool) -> bytes:
    """The file with ``ALIASES`` and, if ``slant``, slanted (cached: the result depends on
    nothing but the arguments)."""
    content = truetype.with_aliases(content, ALIASES)
    return truetype.slanted(content, SYNTHETIC_ITALIC_ANGLE) if slant else content
