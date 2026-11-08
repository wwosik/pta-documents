"""E10-S02: ``./run.sh preview`` (``tools/preview/preview.py``)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

from tests.conftest import REPO_ROOT


def load_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "preview_tool", REPO_ROOT / "tools/preview/preview.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TOOL: Final = load_tool()
DECK: Final = "# Deck\n\n## Eins\n\nText\n\n## Zwei\n\n- a\n- b\n"


def test_a_slide_list_takes_numbers_and_ranges() -> None:
    assert TOOL.parse_slides("3,7-9") == {3, 7, 8, 9}
    assert TOOL.parse_slides(" 2 ") == {2}


@pytest.mark.parametrize("text", ["", "a", "0", "9-7", "3,,4"])
def test_a_wrong_slide_list_is_a_usage_error(text: str) -> None:
    with pytest.raises(TOOL.UsageError):
        TOOL.parse_slides(text)


@pytest.mark.parametrize("args", [["--scale", "0", "x.md"], ["--slides", "x"], ["--colour"]])
def test_wrong_switches_stop_with_exit_code_2(args: list[str]) -> None:
    assert TOOL.main(args) == 2


def test_a_word_document_has_no_preview(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "thema-bericht.md"
    source.write_text("# Bericht\n", encoding="utf-8")
    assert TOOL.main([str(tmp_path)]) == 0
    assert "no preview for Word" in capsys.readouterr().out
    assert not (tmp_path / "vorschau").exists()


@pytest.mark.usefixtures("browser")
def test_a_folder_gets_a_picture_per_slide_and_a_contact_sheet(tmp_path: Path) -> None:
    (tmp_path / "thema-praesentation.md").write_text(DECK, encoding="utf-8")
    folder = tmp_path / "vorschau" / "thema-praesentation"
    folder.mkdir(parents=True)
    (folder / "folie-09.png").write_bytes(b"old")
    assert TOOL.main([str(tmp_path), "--html"]) == 0
    assert sorted(p.name for p in folder.iterdir()) == [
        "folie-01.png",
        "folie-02.png",
        "folie-03.png",
        "thema-praesentation.html",
        "uebersicht.png",
    ]
    assert TOOL.main([str(tmp_path / "thema-praesentation.md"), "--slides", "2"]) == 0
    assert sorted(p.name for p in folder.iterdir()) == ["folie-02.png", "uebersicht.png"]


@pytest.mark.usefixtures("browser")
def test_a_mistake_in_the_deck_is_an_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "x-folien.md").write_text("---\nvorlage: bunt\n---\n# D\n", encoding="utf-8")
    assert TOOL.main([str(tmp_path)]) == 1
    assert "ERROR" in capsys.readouterr().err


def test_a_wrong_audience_is_a_usage_error() -> None:
    assert TOOL.main(["--audience", "chef", "x.md"]) == 2


@pytest.mark.usefixtures("browser")
def test_the_audience_chooses_the_version_and_its_folder(tmp_path: Path) -> None:
    """E16-S03: ``--audience`` as in ``generate``; the internal slide only for PTA."""
    deck = DECK + "\n## Intern {.internal}\n\nText\n"
    (tmp_path / "thema-praesentation.md").write_text(deck, encoding="utf-8")
    assert TOOL.main([str(tmp_path), "--audience", "trainer"]) == 0
    assert TOOL.main([str(tmp_path)]) == 0
    trainer = tmp_path / "vorschau" / "thema-praesentation-trainer"
    customer = tmp_path / "vorschau" / "thema-praesentation"
    assert len(list(trainer.glob("folie-*.png"))) == len(list(customer.glob("folie-*.png"))) + 1
