"""The bundled fonts, the choice of system fonts and the measuring of text."""

from __future__ import annotations

import hashlib
import io
import re
import subprocess
import sys
from pathlib import Path

import pytest

from pta_documents.design import fonts
from pta_documents.design.fonts import FontFace, FontFile, FontSet, truetype
from pta_documents.generation.common import text_metrics
from tests.conftest import REPO_ROOT

SHA256 = {
    "Selawik-Regular.ttf": "e9d98518d8ac2817782a9a382430463a2e0793ea68350b695bb727d9a830ee1c",
    "Selawik-Bold.ttf": "f0db5e174a90e0956ad7d2844bdca1d5e6da92ec65b2c04e57ba9b180668c904",
    "Selawik-Light.ttf": "0295c8b6cca1804bce0abe8e9ab04809fe953cdbbe0f26093ed429daf38869e3",
    "Inconsolata-Regular.ttf": "127875d255d4c5973ca57267a43bb9d1c04397e6c7d236984a595b6cdcb12b7c",
    "Inconsolata-Bold.ttf": "263faa57f6c00c43a04e77df7abd5cb5cd4aae9f93507002c1217e02641fc7e6",
    "Gelasio-Italic.ttf": "1d8bda4ff258bb8251eae4f7d7500c8d97d084136192bb264bc2305168765d1b",
}
FONT_DIR = REPO_ROOT / "src" / "pta_documents" / "design" / "fonts"
SENTENCE = "Die PTA berät Unternehmen und Behörden seit 1969 in Fragen der IT – 12 % mehr."


def test_the_bundled_files_are_the_recorded_ones() -> None:
    assert set(fonts.BUNDLED_FILES) == set(SHA256)
    for name, digest in SHA256.items():
        assert hashlib.sha256(fonts.read(name)).hexdigest() == digest, name


@pytest.mark.parametrize("name", sorted(SHA256))
def test_every_bundled_file_loads_with_truetype_outlines_and_allows_embedding(name: str) -> None:
    info = truetype.read_info(fonts.read(name))
    assert info.truetype_outlines
    assert info.embeddable
    assert info.advances


def test_bundled_has_all_eight_faces_with_the_declared_family_names() -> None:
    bundled = fonts.bundled()
    assert bundled.name == "Selawik"
    assert set(bundled.files) == set(FontFace)
    for face, file in bundled.files.items():
        assert file.family == file.info.family, face
    assert bundled.file(FontFace.LIGHT).family == "Selawik Light"
    assert bundled.file(FontFace.MONO).family == "Inconsolata"
    assert bundled.file(FontFace.QUOTE).family == "Gelasio"


def test_selawik_has_no_italic_so_italic_is_slanted_upright() -> None:
    bundled = fonts.bundled()
    italic, bold_italic = bundled.file(FontFace.ITALIC), bundled.file(FontFace.BOLD_ITALIC)
    assert italic.synthetic_italic and bold_italic.synthetic_italic
    assert italic.content == bundled.file(FontFace.REGULAR).content
    assert bold_italic.content == bundled.file(FontFace.BOLD).content
    others = set(FontFace) - {FontFace.ITALIC, FontFace.BOLD_ITALIC}
    assert not any(bundled.file(face).synthetic_italic for face in others)
    assert fonts.SYNTHETIC_ITALIC_ANGLE == 12.0


def test_the_licences_lie_next_to_the_fonts() -> None:
    for name in fonts.LICENCE_FILES:
        assert "SIL Open Font License, Version 1.1" in fonts.read(name).decode("utf-8")
    assert "Reserved Font Name Selawik" in fonts.read("OFL-Selawik.txt").decode("utf-8")


def test_no_proprietary_font_lies_in_the_repo() -> None:
    proprietary = {name for family in fonts.SYSTEM_FAMILIES for name in family.values()}
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    names = {Path(path).name.lower() for path in tracked}
    assert not names & proprietary
    assert not [n for n in names if n.startswith(("segoe", "consola", "georgia"))]
    font_files = {p.name for p in FONT_DIR.iterdir() if p.suffix in {".ttf", ".otf"}}
    assert font_files == set(SHA256)


def test_without_system_fonts_resolve_is_bundled() -> None:
    assert fonts.resolve(system_fonts=False) == fonts.bundled()


def test_resolve_without_any_font_folder_is_bundled(tmp_path: Path) -> None:
    assert fonts.resolve(search_dirs=[tmp_path / "missing"]) == fonts.bundled()


def test_resolve_with_default_folders_gives_a_complete_set() -> None:
    assert set(fonts.resolve().files) == set(FontFace)


def _segoe_copies(folder: Path, faces: dict[str, str]) -> None:
    """Selawik copies under the file names of Segoe UI (in upper case, to test the case)."""
    folder.mkdir(parents=True, exist_ok=True)
    for target, source in faces.items():
        (folder / target.upper()).write_bytes(fonts.read(source))


SEGOE = {
    "segoeui.ttf": "Selawik-Regular.ttf",
    "segoeuib.ttf": "Selawik-Bold.ttf",
    "segoeuii.ttf": "Selawik-Regular.ttf",
    "segoeuiz.ttf": "Selawik-Bold.ttf",
    "segoeuil.ttf": "Selawik-Light.ttf",
}


def test_a_complete_segoe_ui_is_taken_from_the_system(tmp_path: Path) -> None:
    _segoe_copies(tmp_path / "nested" / "deeper", SEGOE)
    resolved = fonts.resolve(search_dirs=[tmp_path])
    assert resolved.name == "Segoe UI"
    for face in (FontFace.REGULAR, FontFace.BOLD, FontFace.ITALIC, FontFace.BOLD_ITALIC):
        assert not resolved.file(face).synthetic_italic
        assert resolved.file(face).family == "Selawik"  # the copies declare their real name
    bundled = fonts.bundled()
    for face in (FontFace.MONO, FontFace.MONO_BOLD, FontFace.QUOTE):
        assert resolved.file(face) == bundled.file(face)


def test_an_incomplete_segoe_ui_is_not_mixed_in(tmp_path: Path) -> None:
    three = {k: v for k, v in SEGOE.items() if k in {"segoeui.ttf", "segoeuib.ttf", "segoeuii.ttf"}}
    _segoe_copies(tmp_path, three)
    assert fonts.resolve(search_dirs=[tmp_path]) == fonts.bundled()


def test_segoe_ui_without_light_is_not_mixed_in(tmp_path: Path) -> None:
    _segoe_copies(tmp_path, {k: v for k, v in SEGOE.items() if k != "segoeuil.ttf"})
    assert fonts.resolve(search_dirs=[tmp_path]) == fonts.bundled()


def test_consolas_and_georgia_are_taken_per_family(tmp_path: Path) -> None:
    (tmp_path / "consola.ttf").write_bytes(fonts.read("Inconsolata-Regular.ttf"))
    (tmp_path / "consolab.ttf").write_bytes(fonts.read("Inconsolata-Bold.ttf"))
    (tmp_path / "georgiai.ttf").write_bytes(fonts.read("Gelasio-Italic.ttf"))
    resolved = fonts.resolve(search_dirs=[tmp_path])
    assert resolved.name == "Selawik"
    assert resolved.file(FontFace.MONO).content == fonts.read("Inconsolata-Regular.ttf")
    assert resolved.file(FontFace.QUOTE).content == fonts.read("Gelasio-Italic.ttf")


def test_consolas_without_bold_is_not_taken(tmp_path: Path) -> None:
    (tmp_path / "consola.ttf").write_bytes(fonts.read("Inconsolata-Regular.ttf"))
    assert fonts.resolve(search_dirs=[tmp_path]) == fonts.bundled()


def _restricted(content: bytes) -> bytes:
    from fontTools.ttLib import TTFont

    font = TTFont(io.BytesIO(content))
    setattr(font["OS/2"], "fsType", truetype.FS_TYPE_RESTRICTED)  # noqa: B010 (untyped table)
    out = io.BytesIO()
    font.save(out)
    return out.getvalue()


def test_a_face_that_must_not_be_embedded_drops_its_family(tmp_path: Path) -> None:
    _segoe_copies(tmp_path, SEGOE)
    (tmp_path / "SEGOEUIB.TTF").write_bytes(_restricted(fonts.read("Selawik-Bold.ttf")))
    assert fonts.resolve(search_dirs=[tmp_path]) == fonts.bundled()


def test_a_broken_file_drops_its_family(tmp_path: Path) -> None:
    _segoe_copies(tmp_path, SEGOE)
    (tmp_path / "SEGOEUIL.TTF").write_bytes(b"not a font")
    assert fonts.resolve(search_dirs=[tmp_path]) == fonts.bundled()


def test_the_first_folder_wins(tmp_path: Path) -> None:
    _segoe_copies(tmp_path / "a", SEGOE)
    _segoe_copies(tmp_path / "b", {k: "Selawik-Light.ttf" for k in SEGOE})
    resolved = fonts.resolve(search_dirs=[tmp_path / "a", tmp_path / "b"])
    assert resolved.file(FontFace.REGULAR).content == fonts.read("Selawik-Regular.ttf")


def test_width_is_close_to_the_estimate_of_the_slides() -> None:
    bundled = fonts.bundled()
    for face, bold in ((FontFace.REGULAR, False), (FontFace.BOLD, True)):
        measured = bundled.width(SENTENCE, face, 10)
        estimated = text_metrics.width(SENTENCE, 10, bold) / text_metrics.EMU_PER_POINT
        assert measured == pytest.approx(estimated, rel=0.15), face


def test_width_scales_with_size_and_mono_is_fixed() -> None:
    bundled = fonts.bundled()
    assert bundled.width("Text", FontFace.REGULAR, 20) == pytest.approx(
        2 * bundled.width("Text", FontFace.REGULAR, 10)
    )
    assert bundled.width("iiii", FontFace.MONO, 10) == bundled.width("MMMM", FontFace.MONO, 10)
    assert bundled.width("", FontFace.REGULAR, 10) == 0


def test_has_glyph_only_in_the_bmp() -> None:
    bundled = fonts.bundled()
    assert bundled.has_glyph(ord("ä"), FontFace.REGULAR)
    assert bundled.has_glyph(ord("€"), FontFace.LIGHT)
    assert not bundled.has_glyph(0x1F600, FontFace.REGULAR)
    assert not bundled.has_glyph(0x4E2D, FontFace.REGULAR)
    # Selawik has no no-break space; the PDF generator has to fall back for U+00A0 (E05).
    assert not bundled.has_glyph(0xA0, FontFace.REGULAR)


def test_a_set_needs_every_face() -> None:
    file = FontFile("Selawik", fonts.read("Selawik-Regular.ttf"))
    with pytest.raises(ValueError, match="lacks the faces"):
        FontSet("Selawik", {FontFace.REGULAR: file})


def test_css_families_name_the_system_font_first() -> None:
    assert fonts.CSS_FAMILY == "Segoe UI, Selawik, sans-serif"
    assert fonts.CSS_MONO_FAMILY == "Consolas, Inconsolata, monospace"
    assert fonts.CSS_QUOTE_FAMILY == "Georgia, Gelasio, serif"


def test_without_fonttools_the_error_names_the_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "fontTools.ttLib", None)
    assert fonts.bundled().file(FontFace.REGULAR).content  # bytes need no fontTools
    with pytest.raises(ImportError, match=r"extras 'pdf' and 'svg'"):
        truetype.read_info(fonts.read("Selawik-Regular.ttf"))


def test_the_core_imports_neither_fonttools_nor_this_module() -> None:
    script = (
        "import sys\n"
        "import pta_documents, pta_documents.conversions, pta_documents.design\n"
        "import pta_documents.generation.docx, pta_documents.generation.pptx\n"
        "from pta_documents.generation.common import check\n"
        "own = ('fontTools', 'pta_documents.design.fonts')\n"
        "bad = [m for m in sys.modules if m.startswith(own)]\n"
        "print(bad)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True, cwd=REPO_ROOT
    )
    assert result.stdout.strip() == "[]"


def test_only_this_package_and_tests_name_fonttools() -> None:
    sources = (REPO_ROOT / "src" / "pta_documents").rglob("*.py")
    pattern = re.compile(r"^\s*(import|from) fontTools|[\"']fontTools[.\"']", re.MULTILINE)
    users = {p for p in sources if pattern.search(p.read_text(encoding="utf-8"))}
    assert users == {FONT_DIR / "truetype.py"}
