"""The font files for PDF and SVG: Segoe UI from the system when complete, otherwise Selawik.

Word and PowerPoint use the installed fonts and embed nothing; only the PDF generator and the
SVG→PNG conversion need font files. Segoe UI, Consolas and Georgia are proprietary and never
shipped; ``resolve()`` takes them from the system when a family is complete and embeddable,
``bundled()`` returns the OFL substitutes shipped as package data:

======================== ================================================= ==================
File                     Origin and version                                SHA-256
======================== ================================================= ==================
``Selawik-Regular.ttf``  Microsoft Selawik 1.01 (release binary, via npm   ``e9d98518…``
                         ``@docx-editor.dev/fonts`` 2.35.0)
``Selawik-Bold.ttf``     as above                                          ``f0db5e17…``
``Selawik-Light.ttf``    Selawik 1.01 compiled with fontmake 3.12.2 from   ``0295c8b6…``
                         ``Source files/UFO/Selawik-Light.ufo`` of tag
                         ``1.01`` (github.com/microsoft/Selawik)
``Inconsolata-Regular``  Inconsolata 3.000, ``fonts/ttf`` of tag ``3.000`` ``127875d2…``
                         (github.com/googlefonts/Inconsolata)
``Inconsolata-Bold.ttf`` as above                                          ``263faa57…``
``Gelasio-Italic.ttf``   Gelasio 1.008, ``fonts/ttf`` of branch ``master`` ``1d8bda4f…``
                         (github.com/SorkinType/Gelasio, 2026-11-08)
======================== ================================================= ==================

The full hashes are in ``tests/design/test_fonts.py``. Licences: ``OFL-Selawik.txt``,
``OFL-Inconsolata.txt``, ``OFL-Gelasio.txt`` (SIL Open Font License 1.1) next to the files.

Selawik has no italic faces: italic and bold italic are the upright faces with
``synthetic_italic`` set, which the PDF engine slants by ``SYNTHETIC_ITALIC_ANGLE`` degrees.
Gelasio (metrically compatible with Georgia) is only for quotes in SVG/PNG of slide content.

Reading the files needs fontTools (extras ``pdf`` and ``svg``); ``bundled()`` itself does not.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from functools import cached_property
from importlib import resources
from pathlib import Path
from typing import Final

from pta_documents.design.fonts.truetype import BMP_END, FontInfo, read_info


class FontFace(StrEnum):
    REGULAR = "regular"
    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold-italic"
    LIGHT = "light"
    MONO = "mono"
    MONO_BOLD = "mono-bold"
    QUOTE = "quote"


SYNTHETIC_ITALIC_ANGLE: Final = 12.0
"""Degrees the PDF engine slants a face with ``synthetic_italic`` (decision 2026-11-07)."""

CSS_FAMILY: Final = "Segoe UI, Selawik, sans-serif"
CSS_MONO_FAMILY: Final = "Consolas, Inconsolata, monospace"
CSS_QUOTE_FAMILY: Final = "Georgia, Gelasio, serif"

BUNDLED_NAME: Final = "Selawik"
SYSTEM_NAME: Final = "Segoe UI"


@dataclass(frozen=True)
class FontFile:
    """The bytes of one face; ``family`` is the family name the file declares."""

    family: str
    content: bytes = field(repr=False)
    synthetic_italic: bool = False

    @cached_property
    def info(self) -> FontInfo:
        """Metrics and properties, read once per file (needs fontTools)."""
        return read_info(self.content)


@dataclass(frozen=True)
class FontSet:
    """One file for every ``FontFace``; ``name`` is the family of the text faces."""

    name: str
    files: Mapping[FontFace, FontFile]

    def __post_init__(self) -> None:
        missing = [face for face in FontFace if face not in self.files]
        if missing:
            raise ValueError(f"font set {self.name!r} lacks the faces {missing}")

    def file(self, face: FontFace) -> FontFile:
        return self.files[face]

    def width(self, text: str, face: FontFace, size_pt: float) -> float:
        """The advance width of ``text`` in points (no kerning); unmapped characters count
        as ``.notdef``."""
        info = self.files[face].info
        units = sum(info.advances.get(ord(c), info.default_advance) for c in text)
        return units * size_pt / info.units_per_em

    def has_glyph(self, code_point: int, face: FontFace) -> bool:
        """Whether ``face`` maps ``code_point``; outside the BMP always ``False``."""
        return code_point <= BMP_END and code_point in self.files[face].info.advances


_BUNDLED: Final = {
    FontFace.REGULAR: ("Selawik-Regular.ttf", "Selawik", False),
    FontFace.BOLD: ("Selawik-Bold.ttf", "Selawik", False),
    FontFace.ITALIC: ("Selawik-Regular.ttf", "Selawik", True),
    FontFace.BOLD_ITALIC: ("Selawik-Bold.ttf", "Selawik", True),
    FontFace.LIGHT: ("Selawik-Light.ttf", "Selawik Light", False),
    FontFace.MONO: ("Inconsolata-Regular.ttf", "Inconsolata", False),
    FontFace.MONO_BOLD: ("Inconsolata-Bold.ttf", "Inconsolata", False),
    FontFace.QUOTE: ("Gelasio-Italic.ttf", "Gelasio", False),
}

BUNDLED_FILES: Final = tuple(sorted({name for name, _, _ in _BUNDLED.values()}))
LICENCE_FILES: Final = ("OFL-Gelasio.txt", "OFL-Inconsolata.txt", "OFL-Selawik.txt")

SYSTEM_FAMILIES: Final[tuple[Mapping[FontFace, str], ...]] = (
    {
        FontFace.REGULAR: "segoeui.ttf",
        FontFace.BOLD: "segoeuib.ttf",
        FontFace.ITALIC: "segoeuii.ttf",
        FontFace.BOLD_ITALIC: "segoeuiz.ttf",
        FontFace.LIGHT: "segoeuil.ttf",
    },
    {FontFace.MONO: "consola.ttf", FontFace.MONO_BOLD: "consolab.ttf"},
    {FontFace.QUOTE: "georgiai.ttf"},
)
"""The system files per family; a family replaces the bundled faces only as a whole."""


def read(name: str) -> bytes:
    """The bytes of a bundled font or licence file."""
    return (resources.files(__name__) / name).read_bytes()


def bundled() -> FontSet:
    """Selawik, Inconsolata and Gelasio from the package data — no network, no system fonts."""
    contents = {name: read(name) for name in BUNDLED_FILES}
    files = {
        face: FontFile(family, contents[name], synthetic_italic=synthetic)
        for face, (name, family, synthetic) in _BUNDLED.items()
    }
    return FontSet(BUNDLED_NAME, files)


def resolve(system_fonts: bool = True, search_dirs: Sequence[Path] | None = None) -> FontSet:
    """Segoe UI, Consolas and Georgia italic from the system where a family is complete,
    embeddable and has TrueType outlines; every other face from ``bundled()``.

    ``search_dirs`` replaces ``default_font_dirs()``; they are searched recursively, file
    names case-insensitively. Nothing is cached: every call looks again.
    """
    fonts = bundled()
    if not system_fonts:
        return fonts
    dirs = default_font_dirs() if search_dirs is None else search_dirs
    wanted = {name for family in SYSTEM_FAMILIES for name in family.values()}
    found = _find(dirs, wanted)
    files = dict(fonts.files)
    name = fonts.name
    for family in SYSTEM_FAMILIES:
        taken = _take(family, found)
        if not taken:
            continue
        files.update(taken)
        if FontFace.REGULAR in taken:
            name = SYSTEM_NAME
    return FontSet(name, files)


def default_font_dirs() -> list[Path]:
    """The font folders of Windows, Linux and macOS that exist on this machine or not."""
    dirs: list[Path] = []
    windir = os.environ.get("WINDIR")
    if windir:
        dirs.append(Path(windir) / "Fonts")
    local = os.environ.get("LOCALAPPDATA")
    if local:
        dirs.append(Path(local) / "Microsoft" / "Windows" / "Fonts")
    dirs += [Path("/usr/share/fonts"), Path("/usr/local/share/fonts")]
    try:
        home: Path | None = Path.home()
    except RuntimeError:
        home = None
    if home is not None:
        dirs += [home / ".local" / "share" / "fonts", home / ".fonts"]
    dirs.append(Path("/Library/Fonts"))
    if home is not None:
        dirs.append(home / "Library" / "Fonts")
    return dirs


def _find(dirs: Iterable[Path], wanted: set[str]) -> dict[str, Path]:
    """The first file per wanted lower-case name, in the order of ``dirs``, then sorted."""
    found: dict[str, Path] = {}
    for root in dirs:
        for folder, subfolders, names in os.walk(root):
            subfolders.sort()
            for file_name in sorted(names):
                key = file_name.lower()
                if key in wanted and key not in found:
                    found[key] = Path(folder) / file_name
    return found


def _take(family: Mapping[FontFace, str], found: Mapping[str, Path]) -> dict[FontFace, FontFile]:
    """The faces of ``family`` from the system; empty if one is missing or unusable."""
    files: dict[FontFace, FontFile] = {}
    for face, file_name in family.items():
        path = found.get(file_name)
        if path is None:
            return {}
        try:
            content = path.read_bytes()
            info = read_info(content)
        except ImportError:
            raise
        except Exception:  # an unreadable or broken system file is skipped like a missing one
            return {}
        if not info.truetype_outlines or not info.embeddable:
            return {}
        files[face] = FontFile(info.family, content)
    return files
