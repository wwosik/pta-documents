"""E05-S04: every graphic the Markdown can hold is drawn in the PDF — charts, financial charts,
Mermaid diagrams, timelines, Gantt charts, steps, risk matrices, icons and SVG images — with no
``code-not-drawn`` left (port of DocLibs ``ChartTests.Pdfs_DrawTheChart`` and
``FinancialChartTests.InAPdf_TheChartIsDrawnWithItsText``)."""

from __future__ import annotations

import dataclasses
import io
from pathlib import Path
from typing import Any, Final

import pdfplumber
import pytest

from pta_documents.design.word_styles import POINTS_PER_CM
from pta_documents.drawing.svg import to_drawing
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.common.renderers import DrawingGraphic
from pta_documents.generation.common.result import GenerationResult
from pta_documents.generation.pdf import PdfGenerator, PdfOptions
from pta_documents.markdown import DocumentResource, MarkdownDocument
from pta_documents.svg import SvgImageConverter
from tests.conftest import REPO_ROOT
from tests.diagrams.support import SAMPLES as MERMAID_SAMPLES
from tests.generation.common.visual_blocks import RISKS, STEPS
from tests.generation.pdf.layout.test_drawings import FunctionRenderer
from tests.generation.pdf.support import type_area
from tests.generation.pdf.test_generator import NO_COVER, OPTIONS

DATED: Final = "---\nvorlage: hoch-ohne-deckblatt\ndatum: 2026-06-15\n---\n"
CHART: Final = (
    "```chart\ntitle: Bestellungen\nsource: Quelle: Vertrieb\n---\n"
    "Monat, 2025, 2026\nJan, 10, 12\nFeb, 14, 9\n```\n"
)
FUNCTIONS: Final = REPO_ROOT / "samples" / "funktionen"


def generate(
    markdown: str,
    options: PdfOptions = OPTIONS,
    resources: tuple[DocumentResource, ...] = (),
) -> tuple[GenerationResult, bytes]:
    output = io.BytesIO()
    result = PdfGenerator().generate(MarkdownDocument(markdown, resources), output, options)
    return result, output.getvalue()


def first_page(data: bytes) -> Any:
    pdf = pdfplumber.open(io.BytesIO(data))
    return type_area(pdf.pages[0])


def test_a_chart_is_drawn_with_its_title_values_and_source(review_dir: Path) -> None:
    result, data = generate(NO_COVER + CHART + "\nAbbildung: Bestellungen je Monat\n")
    (review_dir / "pdf-chart.pdf").write_bytes(data)
    assert result.notes == ()
    page = first_page(data)
    text = page.extract_text()
    for shown in ("Bestellungen", "Jan", "Feb", "2025", "2026", "Quelle: Vertrieb"):
        assert shown in text, shown
    assert "Abbildung 1: Bestellungen je Monat" in text and "type:" not in text
    assert page.images == [] and len(page.rects) >= 4


def test_a_financial_chart_is_drawn_with_its_text() -> None:
    sample = (FUNCTIONS / "funktionen-bericht.md").read_text(encoding="utf-8")
    start = sample.index("```financial-chart\n")
    block = sample[start : sample.index("```\n", start + 4) + 4]
    result, data = generate(NO_COVER + block)
    assert result.notes == ()
    text = first_page(data).extract_text()
    assert "Wachstum Aufträge" in text and "Prognose" in text and '"type"' not in text


def test_a_mermaid_drawing_is_drawn_as_vectors() -> None:
    """The recorded SVG of mermaid-cli, so that the test runs without Node.js."""
    drawing = to_drawing((MERMAID_SAMPLES / "mermaid-flowchart.svg").read_bytes())
    renderer = FunctionRenderer("mermaid", DrawingGraphic(drawing))
    options = dataclasses.replace(OPTIONS, code_block_renderers=(renderer,))
    result, data = generate(NO_COVER + "```mermaid\nflowchart LR\n```\n", options)
    assert result.notes == ()
    page = first_page(data)
    assert page.images == [] and page.curves + page.lines + page.rects
    assert "flowchart" not in page.extract_text()


def test_a_timeline_is_drawn_as_wide_as_the_text() -> None:
    markdown = (
        DATED + "::: timeline\n- 2026-01: Kick-off\n- 2026-09: Go-live\n- 2027: Betrieb\n:::\n"
    )
    result, data = generate(markdown)
    assert result.notes == ()
    page = first_page(data)
    text = page.extract_text()
    assert "Kick-off" in text and "Betrieb" in text and "2026-01: Kick-off" not in text
    assert page.images == [] and page.curves


def test_a_gantt_chart_is_a_table_with_shaded_months_a_diamond_and_today() -> None:
    markdown = DATED + (
        "::: gantt\n"
        "| Vorgang | Start      | Ende       | Wer   |\n"
        "| ------- | ---------- | ---------- | ----- |\n"
        "| Analyse | 2026-01-05 | 2026-02-20 | PTA   |\n"
        "| Bau     | 2026-02-01 | 2026-07-31 | Kunde |\n"
        "| Abnahme | 2026-08-03 | 2026-08-03 | PTA   |\n"
        ":::\n"
    )
    result, data = generate(markdown)
    assert result.notes == ()
    page = first_page(data)
    text = page.extract_text()
    assert "Vorgang Wer Jan 26 Feb" in text and "2026-01-05" not in text
    fills = [tuple(round(v, 2) for v in r["non_stroking_color"]) for r in page.rects]
    blue = (0.0, round(111 / 255, 2), round(185 / 255, 2))
    assert fills.count(blue) >= 3  # the header row and the months of the analysis
    assert any(len(c["pts"]) >= 4 for c in page.curves)  # the milestone's diamond


def test_steps_are_drawn_and_their_texts_follow_as_a_list_when_they_do_not_fit() -> None:
    result, data = generate(NO_COVER + STEPS)
    assert result.notes == ()
    text = first_page(data).extract_text()
    assert "Analyse" in text and "Interviews" in text and "###" not in text
    long = "### Eins\n" + "sehr lange Erklärung " * 30 + "\n### Zwei\nkurz\n### Drei\n"
    _, data = generate(NO_COVER + "::: steps\n" + long + ":::\n")
    text = first_page(data).extract_text()
    assert "Eins: sehr lange" in text and "Zwei: kurz" in text


def test_a_risk_matrix_is_drawn_with_its_legend_as_a_table() -> None:
    result, data = generate(NO_COVER + RISKS)
    assert result.notes == ()
    page = first_page(data)
    text = page.extract_text()
    assert "Auswirkung" in text and "Ausfall Vertretung" in text
    assert len(page.rects) >= 25


def test_icons_are_small_pictures_in_the_text_and_bullets_of_lists() -> None:
    markdown = (
        NO_COVER + "Der Server :icon-server: läuft.\n\n- :icon-check: Eins\n- :icon-x: Zwei\n"
    )
    result, data = generate(markdown)
    assert result.notes == ()
    page = first_page(data)
    text = page.extract_text()
    assert "Der Server läuft." in text and "icon" not in text and "■" not in text
    sizes = sorted(round(float(i["height"]), 1) for i in page.images)
    assert sizes == [10.0, 11.0, 11.0]
    # The bullets hang left of the text of their items.
    bullets = [i for i in page.images if round(float(i["height"])) == 11]
    eins = next(c for c in page.chars if c["text"] == "E")
    assert all(float(b["x1"]) < float(eins["x0"]) for b in bullets)


def test_an_svg_image_is_converted_at_three_times_and_placed_at_its_natural_size() -> None:
    svg = (FUNCTIONS / "images" / "plan.svg").read_bytes()
    resource = DocumentResource("images/plan.svg", "image/svg+xml", svg)
    options = dataclasses.replace(OPTIONS, image_converters=(SvgImageConverter(),))
    result, data = generate(NO_COVER + "![Plan](images/plan.svg)\n", options, (resource,))
    assert result.notes == ()
    (picture,) = first_page(data).images
    assert picture["srcsize"] == (480 * 3, 200 * 3)
    assert float(picture["width"]) == pytest.approx(480 * 0.75, abs=0.01)
    assert float(picture["width"]) / POINTS_PER_CM < 13


def test_without_a_converter_an_svg_image_is_an_error_naming_it() -> None:
    resource = DocumentResource("images/plan.svg", "image/svg+xml", b"<svg/>")
    options = dataclasses.replace(OPTIONS, image_converters=())
    with pytest.raises(DocumentConversionError, match=r"images/plan\.svg"):
        generate(NO_COVER + "![Plan](images/plan.svg)\n", options, (resource,))
