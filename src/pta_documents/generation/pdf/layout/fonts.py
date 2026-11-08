"""The faces of a ``FontSet`` registered with reportlab, under names from their content.

reportlab keeps registered fonts in a process-wide table. Each face is registered under
``PTA-<first 8 hex digits of the SHA-256 of its file>`` (a slanted face: of the slanted file), so
the same file always has the same name and two font sets never clash: the table never changes
what a document looks like. Registering a face twice is a no-op.

Before registering, ``ALIASES`` lend missing characters the glyph of a similar one. Characters
the faces lack all the same go to ``PdfFonts.replace`` grapheme cluster by grapheme cluster
(``replace_unsupported``, E05-S04); without it they are an error. Faces with
``synthetic_italic`` (Selawik has no italics) are slanted by
``SYNTHETIC_ITALIC_ANGLE`` with ``truetype.slanted``, because reportlab's paragraphs cannot slant
text themselves.
"""

from __future__ import annotations

import hashlib
import io
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import cache
from typing import Final

from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from pta_documents.design.fonts import SYNTHETIC_ITALIC_ANGLE, FontFace, FontFile, FontSet, truetype
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.graphemes import clusters, code_points

type Replacement = Callable[[str], str]
"""Takes a grapheme cluster the fonts lack (``👍🏽`` is one) and returns what to show instead."""

PREFIX: Final = "PTA-"
MISSING: Final = "?"
"""What a character the faces lack becomes by default: PDF/A forbids ``.notdef`` (the generator
notes it, ``character-missing``)."""


def question_mark(cluster: str) -> str:
    """The default ``replace_unsupported``: every cluster the fonts lack is ``MISSING``."""
    return MISSING


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
    replace: Replacement | None = question_mark
    """Asked once per grapheme cluster the faces lack; None: such a cluster is an error."""
    replaced: dict[tuple[str, bool], str] = field(
        default_factory=dict[tuple[str, bool], str], compare=False, repr=False
    )
    """The answers of ``replace`` so far (one document: the hook is asked once per cluster)."""

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
        """``text`` with every grapheme cluster the text faces (``code``: the code face) lack
        replaced (``replace``), white space as a space, invisible format characters left out.

        Raises ``DocumentConversionError`` naming the character, its code points and the font
        when there is no ``replace`` or its replacement is not in the faces either."""
        faces = CODE_FACES if code else TEXT_FACES
        if all(self._has(c, faces) for c in text):
            return text
        parts: list[str] = []
        for cluster in clusters(text):
            needed = [c for c in cluster if not _ignorable(c)]
            if needed and all(self._has(c, faces) for c in needed):
                parts.append("".join(c for c in cluster if self._has(c, faces)))
            elif cluster.isspace():
                parts.append(" ")
            elif not needed or all(unicodedata.category(c) in ("Cc", "Cf") for c in cluster):
                continue  # invisible: a control or format character
            else:
                parts.append(self._replacement(cluster, code))
        return "".join(parts)

    def family(self, code: bool = False) -> str:
        """The family name of the text faces (``code``: of the code face)."""
        return self.fonts.file(FontFace.MONO).family if code else self.fonts.name

    def _replacement(self, cluster: str, code: bool) -> str:
        key = (cluster, code)
        known = self.replaced.get(key)
        if known is not None:
            return known
        where = f"'{cluster}' ({code_points(cluster)})"
        if self.replace is None:
            raise DocumentConversionError(
                DocumentFormat.PDF,
                f"The character {where} is not in the font ({self.family(code)}). Leave it out, "
                "write it in words or pass replace_unsupported to PdfOptions.",
            )
        value = self.replace(cluster)
        faces = CODE_FACES if code else TEXT_FACES
        if not all(c.isspace() or self._has(c, faces) for c in value):
            raise DocumentConversionError(
                DocumentFormat.PDF,
                f"The replacement '{value}' of the character {where} is not in the font "
                f"({self.family(code)}) either.",
            )
        value = "".join(" " if c.isspace() else c for c in value)
        self.replaced[key] = value
        return value

    def _has(self, char: str, faces: tuple[FontFace, ...]) -> bool:
        code = ord(char)
        return all(self.has_glyph(code, face) for face in faces)


def _ignorable(char: str) -> bool:
    """Characters that only modify how the cluster looks: variation selectors and the
    zero-width joiner. A cluster the faces have but for them shows without them."""
    code = ord(char)
    return 0xFE00 <= code <= 0xFE0F or 0xE0100 <= code <= 0xE01EF or code == 0x200D


def register(fonts: FontSet, replace: Replacement | None = question_mark) -> PdfFonts:
    """Register every face of ``fonts`` (and the families) with reportlab; ``replace`` takes
    the characters they lack (``PdfFonts.replace``)."""
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
    return PdfFonts(fonts, names, text, mono, replace)


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
