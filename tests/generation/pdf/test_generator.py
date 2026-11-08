"""E05-S01: the PDF generator — front matter, the interim layout, check and the tools."""

from __future__ import annotations

import datetime as dt
import importlib.util
import io
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Final

import pdfplumber
import pikepdf
import pytest

from pta_documents.design.fonts import FontFace
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.check import ReportStats, check
from pta_documents.generation.common.result import NoteCodes
from pta_documents.generation.docx import generator as docx_generator
from pta_documents.generation.pdf import EXTRA_MISSING, PdfGenerator, PdfOptions
from pta_documents.generation.pdf import generator as pdf_generator
from pta_documents.generation.pdf.body import BodySource
from pta_documents.generation.pdf.fonts import FontMetrics
from pta_documents.generation.pdf.page_model import (
    A4_HEIGHT,
    A4_WIDTH,
    LaidOutPage,
    Layout,
    PageGeometry,
    TextItem,
)
from pta_documents.markdown import MarkdownDocument
from tests.conftest import REPO_ROOT

CREATED: Final = dt.datetime(2026, 11, 8, 9, 0, tzinfo=dt.UTC)
OPTIONS: Final = PdfOptions(created=CREATED, system_fonts=False)
NO_COVER: Final = "---\nvorlage: hoch-ohne-deckblatt\n---\n"


def generate(markdown: str, options: PdfOptions = OPTIONS, **metadata: str) -> tuple[bytes, int]:
    output = io.BytesIO()
    result = PdfGenerator().generate(MarkdownDocument(markdown, metadata=metadata), output, options)
    assert result.pages is not None
    return output.getvalue(), result.pages


def pages_text(data: bytes) -> list[str]:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]


def test_an_empty_document_gives_one_empty_page() -> None:
    data, pages = generate(NO_COVER)
    assert pages == 1
    with pikepdf.open(io.BytesIO(data)) as pdf:
        assert len(pdf.pages) == 1
        assert pdf.open_metadata()["pdfaid:part"] == "2"
        width, height = (float(v) for v in pdf.pages[0].mediabox[2:])
    assert (width, height) == pytest.approx((A4_WIDTH, A4_HEIGHT))
    assert pages_text(data) == [""]


def test_the_text_of_the_document_comes_back() -> None:
    markdown = (
        "---\ntitel: Bericht\nautor: Anna Nowak\n---\n# Einleitung\n\n"
        "Ein Absatz mit **fett** und `code`.\n\n- erstens\n- zweitens\n\n"
        "1. eins\n\n> Zitat\n\n```python\nprint('hallo')\n```\n\n"
        "| Spalte | Wert |\n| --- | --- |\n| a | 1 |\n"
    )
    data, _ = generate(markdown)
    (text,) = pages_text(data)
    lines = text.split("\n")
    assert lines[:4] == ["Einleitung", "Ein Absatz mit fett und code.", "– erstens", "– zweitens"]
    assert "1. eins" in lines and "Zitat" in lines and "print('hallo')" in lines
    assert "Spalte Wert" in text.replace("   ", " ")
    with pikepdf.open(io.BytesIO(data)) as pdf:
        meta = pdf.open_metadata()
        assert meta["dc:title"] == "Bericht" and meta["dc:creator"] == ["Anna Nowak"]


def test_long_documents_continue_on_further_pages() -> None:
    paragraph = "Wort " * 120
    data, pages = generate(NO_COVER + "\n\n".join([paragraph] * 12))
    assert pages > 1
    assert len(pages_text(data)) == pages


def test_the_cover_templates_need_a_title_as_in_word() -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate("# Ohne Titel\n")
    assert error.value.format is DocumentFormat.PDF
    assert "titel:" in error.value.reason
    data, _ = generate("Text\n", title="Aus den Metadaten", author="Konverter")
    with pikepdf.open(io.BytesIO(data)) as pdf:
        assert str(pdf.docinfo["/Title"]) == "Aus den Metadaten"
        assert str(pdf.docinfo["/Author"]) == "Konverter"


def test_the_front_matter_keys_are_those_of_word() -> None:
    assert set(pdf_generator.VALID_KEYS) <= set(docx_generator.VALID_KEYS)
    with pytest.raises(DocumentConversionError) as error:
        generate("---\nfusszeile: x\n---\nText\n")
    assert error.value.format is DocumentFormat.PDF and "fusszeile" in error.value.reason
    with pytest.raises(DocumentConversionError) as error:
        generate("---\nvorlage: breit\n---\nText\n")
    assert error.value.format is DocumentFormat.PDF and "hoch-ohne-deckblatt" in error.value.reason
    generate(NO_COVER.replace("---\n", "---\npruefung: aus\nfirma: X\ndatum: 2026-11-08\n", 1))


def test_template_orientation_and_language_reach_the_pdf() -> None:
    data, _ = generate("---\nvorlage: quer-ohne-deckblatt\nsprache: en\n---\nText\n")
    with pikepdf.open(io.BytesIO(data)) as pdf:
        width, height = (float(v) for v in pdf.pages[0].mediabox[2:])
        assert str(pdf.Root.Lang) == "en"
    assert (width, height) == pytest.approx((A4_HEIGHT, A4_WIDTH))


def test_missing_characters_are_replaced_and_noted() -> None:
    output = io.BytesIO()
    result = PdfGenerator().generate(
        MarkdownDocument(NO_COVER + "Привет, Selawik.\n"), output, OPTIONS
    )
    assert set(result.codes()) == {NoteCodes.CHARACTER_MISSING}
    assert result.notes[0].line == 4
    (text,) = pages_text(output.getvalue())
    assert text == "??????, Selawik."


def test_equal_input_and_created_give_equal_bytes() -> None:
    markdown = NO_COVER + "# Titel\n\nZażółć gęślą jaźń.\n"
    assert generate(markdown)[0] == generate(markdown)[0]
    later = PdfOptions(created=CREATED + dt.timedelta(seconds=1), system_fonts=False)
    assert generate(markdown, later)[0] != generate(markdown)[0]


def test_the_body_layout_is_a_seam(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[BodySource] = []

    def three_pages(source: BodySource, fonts: FontMetrics) -> Layout:
        seen.append(source)
        assert fonts.has_glyph("a", FontFace.REGULAR)
        page = LaidOutPage((TextItem(50, 50, "eigene Engine", FontFace.REGULAR, 10),))
        return Layout(PageGeometry(300, 200, 10, 10, 10, 10), (page, page, page))

    monkeypatch.setattr(pdf_generator, "BODY_LAYOUT", three_pages)
    data, pages = generate(NO_COVER + "# Kapitel\n\nText\n")
    assert pages == 3 and pages_text(data) == ["eigene Engine"] * 3
    (source,) = seen
    assert [t.type for t in source.tokens][:3] == ["heading_open", "inline", "heading_close"]
    assert source.front.body_line == 3 and source.texts.page == "Seite"


def test_check_takes_pdf_and_counts_the_pages() -> None:
    result = check(
        MarkdownDocument(NO_COVER + "# Kapitel\n\nEins.\n\n- a.\n- b\n"), DocumentFormat.PDF
    )
    assert result.ok, result.errors
    assert isinstance(result.stats, ReportStats)
    assert result.stats.counted_pages == 1 and result.stats.pages == 1
    assert "1 pages (counted on the trial PDF)" in result.stats.lines()[1]
    assert "style-punctuation" in result.codes()
    failed = check(MarkdownDocument("# Ohne Titel\n"), DocumentFormat.PDF)
    assert not failed.ok and failed.stats is None


def load_tool(name: str) -> ModuleType:
    path = REPO_ROOT / "tools" / name / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"{name}_tool", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_tools_take_pdf(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "kunde-bericht.md"
    source.write_text("---\ntitel: Kunde\n---\n# Kapitel\n\nText.\n", encoding="utf-8")
    assert load_tool("generate").main([str(source), "--pdf"]) == 0
    assert (tmp_path / "kunde-bericht.pdf").read_bytes().startswith(b"%PDF-1.7")
    assert load_tool("check").main([str(source), "--pdf"]) == 0
    out = capsys.readouterr().out
    assert f"OK {source}" in out and "counted on the trial PDF" in out


def test_without_the_extra_the_import_names_it() -> None:
    script = (
        "import sys\n"
        "sys.modules['reportlab'] = None\n"
        "try:\n"
        "    import pta_documents.generation.pdf\n"
        "except ImportError as error:\n"
        "    print(error)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True, cwd=REPO_ROOT
    )
    assert result.stdout.strip() == EXTRA_MISSING
