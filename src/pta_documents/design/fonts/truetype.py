"""Reading TrueType files: port of the needed parts of DocLibs ``TrueTypeInfo``.

Only what choosing and measuring a face needs: whether the outlines are TrueType (``glyf``),
the family name (name ID 1, else 16), the embedding permissions (``OS/2 fsType``), the
character map and the advance widths (``hmtx``). The parsing itself is fontTools, which comes
with the extras ``pdf`` and ``svg``; the core of the library never imports this module.
"""

from __future__ import annotations

import importlib
import io
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final

FS_TYPE_RESTRICTED: Final = 0x0002
"""``OS/2 fsType``: restricted licence embedding — the face must not be embedded."""

BMP_END: Final = 0xFFFF
"""Like DocLibs, only the Basic Multilingual Plane is measured and checked."""

FONTTOOLS_MISSING: Final = (
    "pta_documents.design.fonts needs fontTools, which comes with the extras 'pdf' and 'svg': "
    "pip install 'pta-documents[pdf]' or 'pta-documents[svg]'."
)


@dataclass(frozen=True)
class FontInfo:
    """What the library reads from a TrueType file."""

    family: str
    truetype_outlines: bool
    """``glyf`` outlines; CFF outlines are not used."""
    fs_type: int
    units_per_em: int
    advances: Mapping[int, int]
    """Advance width in font units per BMP code point the font maps."""
    default_advance: int
    """Advance width of ``.notdef``, used for characters the font does not map."""
    line_units: int = 0
    """The height of a single line in font units as Word takes it: ``OS/2`` Windows ascent
    plus descent (``hhea`` ascender − descender without ``OS/2``)."""

    @property
    def line_height(self) -> float:
        """A single line as a multiple of the font size (Segoe UI and Selawik: about 1.33)."""
        return self.line_units / self.units_per_em

    @property
    def embeddable(self) -> bool:
        return not self.fs_type & FS_TYPE_RESTRICTED


def _ttfont_class() -> Any:
    try:
        module = importlib.import_module("fontTools.ttLib")
    except ImportError as error:
        raise ImportError(FONTTOOLS_MISSING) from error
    return module.TTFont


def read_info(content: bytes) -> FontInfo:
    """Read ``content`` (a TrueType or OpenType file); fontTools errors pass through."""
    font = _ttfont_class()(io.BytesIO(content), lazy=True)
    try:
        names = font["name"]
        family = names.getDebugName(1) or names.getDebugName(16) or ""
        fs_type = int(font["OS/2"].fsType) if "OS/2" in font else 0
        metrics = font["hmtx"].metrics
        cmap: dict[int, str] = font.getBestCmap() or {}
        advances = {
            int(code): int(metrics[glyph][0]) for code, glyph in cmap.items() if code <= BMP_END
        }
        notdef = font.getGlyphOrder()[0]
        if "OS/2" in font:
            os2 = font["OS/2"]
            line_units = int(os2.usWinAscent) + int(os2.usWinDescent)
        else:
            line_units = int(font["hhea"].ascent) - int(font["hhea"].descent)
        return FontInfo(
            family=str(family),
            truetype_outlines="glyf" in font,
            fs_type=fs_type,
            units_per_em=int(font["head"].unitsPerEm),
            advances=advances,
            default_advance=int(metrics[notdef][0]),
            line_units=line_units,
        )
    finally:
        font.close()


def slanted(content: bytes, angle: float) -> bytes:
    """``content`` (a TrueType file) with every outline slanted by ``angle`` degrees to the
    right: the synthetic italic of a family without italic faces, for engines that cannot
    slant text themselves (reportlab's paragraphs, E05-S02).

    Composite glyphs are decomposed (each part would be slanted twice), hinting is dropped
    (it would not fit the new outlines), ``post.italicAngle`` and the italic bits are set, the
    PostScript name gets ``-Slanted`` (PDF readers tell embedded fonts apart by it), and
    the timestamps are kept, so equal input gives equal bytes.
    """
    font = _ttfont_class()(io.BytesIO(content), recalcTimestamp=False)
    try:
        pens = importlib.import_module("fontTools.pens.ttGlyphPen")
        transform = importlib.import_module("fontTools.pens.transformPen")
        recording = importlib.import_module("fontTools.pens.recordingPen")
        skew = math.tan(math.radians(angle))
        glyph_set = font.getGlyphSet()
        glyf = font["glyf"]
        hmtx = font["hmtx"]
        outlines: dict[str, Any] = {}
        for name in font.getGlyphOrder():
            recorder = recording.DecomposingRecordingPen(glyph_set)
            glyph_set[name].draw(recorder)
            pen = pens.TTGlyphPen(None)
            recorder.replay(transform.TransformPen(pen, (1, 0, skew, 1, 0, 0)))
            outlines[name] = pen.glyph()
        for name, glyph in outlines.items():
            glyf[name] = glyph
            glyph.recalcBounds(glyf)
            advance = hmtx[name][0]
            hmtx[name] = (advance, int(getattr(glyph, "xMin", 0)))
        for table in ("fpgm", "prep", "cvt ", "hdmx", "LTSH", "VDMX"):
            if table in font:
                del font[table]
        names = font["name"]
        postscript = str(names.getDebugName(6) or "Font")
        for record in list(names.names):
            if record.nameID == 6:
                names.setName(
                    f"{postscript}-Slanted", 6, record.platformID, record.platEncID, record.langID
                )
        font["post"].italicAngle = -angle
        font["head"].macStyle |= 0x02
        if "OS/2" in font:
            os2 = font["OS/2"]
            os2.fsSelection = (os2.fsSelection | 0x01) & ~0x40
        output = io.BytesIO()
        font.save(output)
        return output.getvalue()
    finally:
        font.close()


def with_aliases(content: bytes, aliases: Mapping[int, int]) -> bytes:
    """``content`` with each code point of ``aliases`` the font lacks mapped to the glyph of
    its value (U+00A0 → the glyph of the space: Selawik has no no-break space); ``content``
    itself when nothing is missing. Timestamps are kept, so equal input gives equal bytes."""
    font = _ttfont_class()(io.BytesIO(content), recalcTimestamp=False)
    try:
        best: dict[int, str] = font.getBestCmap() or {}
        added = {
            code: best[target]
            for code, target in aliases.items()
            if code not in best and target in best
        }
        if not added:
            return content
        for table in font["cmap"].tables:
            if table.isUnicode():
                for code, glyph in added.items():
                    if code <= BMP_END or table.format in (12, 13):
                        table.cmap.setdefault(code, glyph)
        output = io.BytesIO()
        font.save(output)
        return output.getvalue()
    finally:
        font.close()
