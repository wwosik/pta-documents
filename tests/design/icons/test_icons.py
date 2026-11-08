"""E15-S03: the bundled Tabler icons, their licence and their names."""

from __future__ import annotations

from importlib import resources

import pytest

from pta_documents.design import icons
from pta_documents.generation.pptx.generator import PptxGenerator
from tests.conftest import REPO_ROOT


def bundled_files() -> set[str]:
    folder = resources.files(icons.__name__)
    return {p.name.removesuffix(".svg") for p in folder.iterdir() if p.name.endswith(".svg")}


def test_the_list_names_every_bundled_file_and_nothing_else() -> None:
    assert set(icons.ICONS) == bundled_files()
    assert list(icons.ICONS) == sorted(icons.ICONS)
    assert len(icons.ICONS) >= 120


def test_the_licence_of_the_set_is_in_the_package() -> None:
    text = icons.license_text()
    assert text.startswith("MIT License")
    assert "Paweł Kuna" in text


@pytest.mark.parametrize("name", icons.ICONS)
def test_every_icon_is_a_stroked_24_pixel_outline(name: str) -> None:
    data = icons.svg(name).decode("utf-8")
    assert 'viewBox="0 0 24 24"' in data
    assert 'stroke-width="2"' in data and 'fill="none"' in data


def test_unknown_names_are_refused_with_the_closest_names() -> None:
    with pytest.raises(KeyError):
        icons.svg("chek")
    assert icons.suggestions("chek")[0] == "check"
    reason = icons.unknown("chek")
    assert reason.startswith("Unknown icon ':icon-chek:'. Did you mean :icon-check:")
    assert "authoring guide" in icons.unknown("zzzzzzzz")


def test_the_alternative_text_names_the_icon() -> None:
    assert icons.alt("check") == "icon:check"
    assert icons.from_alt("icon:check") == "check"
    assert icons.from_alt("icon:nonsense") is None
    assert icons.from_alt("Ein Bild") is None
    assert icons.from_alt(None) is None


def test_the_svg_takes_the_colour_asked_for() -> None:
    data = icons.colored_svg("check", "006FB9")
    assert b'stroke="#006FB9"' in data and b"currentColor" not in data


def test_the_authoring_guide_names_every_icon() -> None:
    # The list moved from docs/ki-anleitung.md into the guide (E04-S06), which builds it from
    # ICONS; ki-anleitung.md points to ``./run.sh authoring-guide pptx``.
    guide = PptxGenerator().authoring_guide()
    missing = [name for name in icons.ICONS if f"`{name}`" not in guide]
    assert missing == []
    assert "./run.sh authoring-guide pptx" in (REPO_ROOT / "docs" / "ki-anleitung.md").read_text(
        encoding="utf-8"
    )
