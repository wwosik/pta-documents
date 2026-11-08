"""E05-S01/E05-S02: the PDF generator — front matter, the layout engine, check and the tools."""

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

from pta_documents.design.word_styles import POINTS_PER_CM
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.check import ReportStats, check
from pta_documents.generation.common.result import NoteCodes
from pta_documents.generation.docx import generator as docx_generator
from pta_documents.generation.pdf import EXTRA_MISSING, PdfGenerator, PdfOptions
from pta_documents.generation.pdf import generator as pdf_generator
from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of
from tests.conftest import REPO_ROOT
from tests.generation.common.visual_blocks import RATING, RISKS, STEPS

CREATED: Final = dt.datetime(2026, 11, 8, 9, 0, tzinfo=dt.UTC)
OPTIONS: Final = PdfOptions(created=CREATED, system_fonts=False)
NO_COVER: Final = "---\nvorlage: hoch-ohne-deckblatt\n---\n"
A4_WIDTH: Final = 21.0 * POINTS_PER_CM
A4_HEIGHT: Final = 29.7 * POINTS_PER_CM


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
    assert (width, height) == pytest.approx((A4_WIDTH, A4_HEIGHT), abs=0.1)
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
    assert lines[:4] == ["1 Einleitung", "Ein Absatz mit fett und code.", "erstens", "zweitens"]
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
    assert (width, height) == pytest.approx((A4_HEIGHT, A4_WIDTH), abs=0.1)


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


def test_typography_and_highlighting_follow_the_front_matter() -> None:
    text = 'Er sagte "ja" - und ging.\n\n```python\nx = 1  # eins\n```\n'
    typeset, _ = generate(NO_COVER + text)
    plain, _ = generate(NO_COVER.replace("---\n", "---\ntypografie: nein\n", 1) + text)
    assert "Er sagte „ja“ – und ging." in pages_text(typeset)[0]
    assert 'Er sagte "ja" - und ging.' in pages_text(plain)[0]
    grey, _ = generate(NO_COVER.replace("---\n", "---\nsyntaxhervorhebung: nein\n", 1) + text)
    assert colours_of(typeset, "eins") != colours_of(grey, "eins")


def colours_of(data: bytes, word: str) -> set[tuple[float, ...]]:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        chars = pdf.pages[0].chars
    text = "".join(c["text"] for c in chars)
    start = text.index(word)
    return {tuple(c["non_stroking_color"]) for c in chars[start : start + len(word)]}


def test_a_qr_code_is_three_centimetres_wide_as_in_word() -> None:
    data, _ = generate(NO_COVER + '![Umfrage](qr:https://www.pta.de/)\n\n![](qr:x "scale=2")\n')
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        widths = [round(float(i["width"]) / POINTS_PER_CM, 2) for i in pdf.pages[0].images]
    assert widths == [3.0, 6.0]


def test_timelines_and_gantt_charts_show_as_their_content_with_a_note() -> None:
    markdown = NO_COVER + "::: timeline\n- 2026-01: Kick-off\n- 2027: Betrieb\n:::\n"
    output = io.BytesIO()
    result = PdfGenerator().generate(MarkdownDocument(markdown), output, OPTIONS)
    assert result.codes() == [NoteCodes.CODE_NOT_DRAWN]
    assert "2026-01: Kick-off" in pages_text(output.getvalue())[0]


@pytest.mark.parametrize("block", [STEPS, RISKS], ids=["steps", "riskmatrix"])
def test_steps_and_risk_matrices_show_as_their_content_with_a_note(block: str) -> None:
    """E15-S02: drawn with E05-S04."""
    output = io.BytesIO()
    result = PdfGenerator().generate(MarkdownDocument(NO_COVER + block), output, OPTIONS)
    assert result.codes() == [NoteCodes.CODE_NOT_DRAWN]
    assert (
        "Analyse" in pages_text(output.getvalue())[0]
        or "Ausfall" in pages_text(output.getvalue())[0]
    )


def test_harvey_balls_are_drawn_in_their_cells() -> None:
    """E15-S02: the PDF's fonts have no ○ ◔ ◑ ◕ ●, so the balls are drawn as small pictures."""
    data, _ = generate(NO_COVER + RATING)
    text = pages_text(data)[0]
    assert "[3/4]" not in text and "Kosten" in text
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        curves = pdf.pages[0].curves
    # A rim per ball, a fill for three of four, a slice for two of them.
    assert len(curves) >= 4
    sizes = {round(float(c["width"]) / POINTS_PER_CM, 2) for c in curves}
    assert 0.4 <= max(sizes) <= 0.45


def test_characters_missing_from_the_code_font_become_question_marks() -> None:
    data, _ = generate(NO_COVER + "`Привет` und\n\n```\nΔ = 1\n```\n")
    assert pages_text(data)[0].split("\n") == ["?????? und", "? = 1"]


def test_the_report_samples_generate_with_only_what_is_not_drawn_yet(review_dir: Path) -> None:
    """Every Word sample is a PDF too; charts, drawings, timelines and Gantt charts stay their
    source with ``code-not-drawn`` until E05-S04."""
    for folder in ("gsb", "funktionen"):
        root = REPO_ROOT / "samples" / folder
        images = tuple(
            DocumentResource(f"images/{p.name}", content_type_of(p.name), p.read_bytes())
            for p in sorted((root / "images").glob("*"))
        )
        for source in sorted(root.glob("*-bericht.md")) + sorted(root.glob("*-dokument.md")):
            output = io.BytesIO()
            document = MarkdownDocument(source.read_text(encoding="utf-8"), images)
            result = PdfGenerator().generate(document, output, OPTIONS)
            assert set(result.codes()) <= {NoteCodes.CODE_NOT_DRAWN}, f"{source.name}:\n{result}"
            assert result.pages and result.pages >= 1
            (review_dir / f"pdf-{source.stem}.pdf").write_bytes(output.getvalue())


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
