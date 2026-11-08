"""E08-S02: check() and ./run.sh check — the generators' findings, style notes, statistics."""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
from types import ModuleType

import pytest

from pta_documents.errors import DocumentFormat
from pta_documents.generation.common.check import (
    CheckOptions,
    DeckStats,
    ReportStats,
    check,
)
from pta_documents.generation.common.result import NoteCodes
from pta_documents.generation.common.style_rules import StyleCodes
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of
from tests.diagrams.support import drawable

REPO = Path(__file__).resolve().parents[3]
PPTX = DocumentFormat.PPTX
DOCX = DocumentFormat.DOCX
WORD: str = "---\nvorlage: hoch-ohne-deckblatt\n---\n"
"""Front matter of a Word document without a cover (so it needs no title)."""


def resources(folder: Path) -> tuple[DocumentResource, ...]:
    return tuple(
        DocumentResource(f"images/{p.name}", content_type_of(p.name), p.read_bytes())
        for p in sorted((folder / "images").glob("*"))
    )


def test_the_notes_are_those_of_generate_plus_style_notes() -> None:
    markdown = "# Deck\n\n## Folie\n\n<b>Fett</b>\n\n- Eins.\n- Zwei\n"
    generated = PptxGenerator().generate(MarkdownDocument(markdown), io.BytesIO())
    result = check(MarkdownDocument(markdown), PPTX)
    assert result.ok
    assert generated.codes() == [NoteCodes.RAW_HTML]
    assert result.codes() == [NoteCodes.RAW_HTML, StyleCodes.PUNCTUATION]


def test_errors_are_those_of_generate() -> None:
    result = check(MarkdownDocument("# Deck\n\n::: card\nText\n:::\n"), PPTX)
    assert not result.ok
    assert result.errors[0].startswith("Line 3: Unknown container")
    assert result.stats is None


def test_the_generators_accept_the_front_matter_key() -> None:
    result = check(
        MarkdownDocument("---\ntitel: T\npruefung: aus\n---\n# Kapitel\n\nText.\n"), DOCX
    )
    assert result.ok, result.errors


def test_deck_statistics() -> None:
    notes = "::: notes\n" + " ".join(["Wort"] * 240) + "\n:::\n"
    markdown = (
        "# Deck\n\n# Kapitel\n\n## Eins\n\nDrei kurze Wörter.\n\n"
        f"## Zwei\n\n- a b\n- c\n\n{notes}\n# Danke {{.closing}}\n"
    )
    stats = check(MarkdownDocument(markdown), PPTX).stats
    assert isinstance(stats, DeckStats)
    assert (stats.slides, stats.title, stats.chapters, stats.content, stats.closing) == (
        5,
        1,
        1,
        2,
        1,
    )
    assert (stats.words_min, stats.words_median, stats.words_max) == (3, 3, 3)
    assert stats.notes_words == 240
    assert stats.minutes == 2 * 2 + 2
    assert len(stats.lines()) == 2


def test_code_in_the_notes_is_not_spoken() -> None:
    """E08-S03: the Markdown source in the notes does not count; inline code does."""
    markdown = (
        "# Deck\n\n## Eins\n\nText.\n\n::: notes\nSag `drei` Wörter.\n\n"
        "```markdown\n## Eins\n\nText und noch mehr.\n```\n:::\n"
    )
    stats = check(MarkdownDocument(markdown), PPTX).stats
    assert isinstance(stats, DeckStats)
    assert stats.notes_words == 3


def test_continued_slides_are_counted() -> None:
    markdown = "# Deck\n\n## Lang\n\n" + "\n".join(f"- Punkt {i}" for i in range(40)) + "\n"
    stats = check(MarkdownDocument(markdown), PPTX, CheckOptions(skip=StyleCodes.ALL)).stats
    assert isinstance(stats, DeckStats)
    assert stats.continued >= 1
    assert stats.content == stats.continued + 1


def test_report_statistics() -> None:
    markdown = WORD + (
        "# Kapitel\n\nEin Satz mit sechs Wörtern hier.\n\n## Teil\n\n| A | B |\n| - | - |\n"
        "| 1 | 2 |\n\n```python\nnot = counted\n```\n"
    )
    stats = check(MarkdownDocument(markdown), DOCX).stats
    assert isinstance(stats, ReportStats)
    assert (stats.headings, stats.tables, stats.figures) == (2, 1, 0)
    assert stats.words == 1 + 6 + 1 + 4
    assert stats.pages == 1


@pytest.mark.parametrize("folder", ["gsb", "funktionen"])
def test_the_samples_pass_the_check_without_notes(folder: str) -> None:
    root = REPO / "samples" / folder
    images = resources(root)
    sources = (root / "QUELLEN.md").is_file()
    for source in sorted(root.glob("*.md")):
        if source.name in ("README.md", "QUELLEN.md"):
            continue
        if not drawable(source.read_text(encoding="utf-8")):
            continue  # Mermaid without mermaid-cli: tests/diagrams covers it
        format = PPTX if source.stem.endswith(("-praesentation", "-folien")) else DOCX
        result = check(
            MarkdownDocument(source.read_text(encoding="utf-8"), images),
            format,
            CheckOptions(sources=sources),
        )
        assert result.ok and result.notes == (), f"{source.name}: {result}"


def load_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_tool", REPO / "tools/check/check.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_tool_writes_nothing_and_reports_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "kunde-praesentation.md"
    source.write_text("# Deck\n\n## Folie\n\n- Eins.\n- Zwei\n", encoding="utf-8")
    tool = load_tool()
    assert tool.main([str(tmp_path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert [n["code"] for n in report["files"][0]["notes"]] == [StyleCodes.PUNCTUATION]
    assert report["files"][0]["stats"]["minutes"] == 2
    assert sorted(p.name for p in tmp_path.iterdir()) == ["kunde-praesentation.md"]
    assert tool.main([str(source), "--strict"]) == 1
    assert tool.main([str(source), "--strict", "--skip", StyleCodes.PUNCTUATION]) == 0
    out = capsys.readouterr().out
    assert f"OK {source}" in out and "[style-punctuation]" in out


def test_the_tool_fails_on_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "kunde-bericht.md"
    source.write_text(WORD + "# Kapitel\n\n::: card\nText\n:::\n", encoding="utf-8")
    assert load_tool().main([str(source)]) == 1
    assert f"ERROR {source}: Line 6" in capsys.readouterr().out
