"""Reading TrueType files: port of the needed parts of DocLibs ``TrueTypeInfo``.

Only what choosing and measuring a face needs: whether the outlines are TrueType (``glyf``),
the family name (name ID 1, else 16), the embedding permissions (``OS/2 fsType``), the
character map and the advance widths (``hmtx``). The parsing itself is fontTools, which comes
with the extras ``pdf`` and ``svg``; the core of the library never imports this module.
"""

from __future__ import annotations

import importlib
import io
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
        return FontInfo(
            family=str(family),
            truetype_outlines="glyf" in font,
            fs_type=fs_type,
            units_per_em=int(font["head"].unitsPerEm),
            advances=advances,
            default_advance=int(metrics[notdef][0]),
        )
    finally:
        font.close()
