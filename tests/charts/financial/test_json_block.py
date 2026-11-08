"""E06-S02: the ``financial-chart`` block — JSON in, the same chart as from Python data."""

from __future__ import annotations

import re

import pytest

from pta_documents.charts import financial
from pta_documents.charts.financial import (
    FinancialChartError,
    FinancialChartLabels,
    FinancialChartOptions,
    GrowthTrendChart,
    TrendMonth,
)
from pta_documents.charts.financial.json_block import camel
from pta_documents.charts.renderer import AUTHORING_GUIDE, ChartRenderer
from pta_documents.design import colors
from pta_documents.design.variants import Language
from pta_documents.drawing import DrawingText, to_svg
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.renderers import (
    CodeBlockRequest,
    DrawingGraphic,
    render,
)
from tests.charts.financial import figures
from tests.charts.financial.test_financial import NAMES, charts


def request(
    code: str,
    info: str = "financial-chart",
    language: Language = Language.DE,
    format: DocumentFormat = DocumentFormat.PPTX,
) -> CodeBlockRequest:
    return CodeBlockRequest(info, code, 9, format, language)


@pytest.mark.parametrize("name", NAMES)
def test_the_block_draws_what_the_python_data_draws(name: str) -> None:
    chart = charts()[name]
    block = financial.to_json(chart, figures.OPTIONS)
    parsed, options = financial.parse(block, 3)
    assert (parsed, options) == (chart, figures.OPTIONS)
    graphic = ChartRenderer().render(request(block, format=DocumentFormat.DOCX))
    assert isinstance(graphic, DrawingGraphic)
    assert to_svg(graphic.drawing) == to_svg(financial.draw(chart, figures.OPTIONS))


def test_keys_are_camel_case_and_options_are_read() -> None:
    assert camel("projection_compared_from") == "projectionComparedFrom"
    block = """{
      // a comment, and trailing commas
      "type": "growth-trend",
      "title": "Wachstum",
      "lastActual": 1,
      "reference": 0.05,
      "months": [{"label": "Jan", "change": 0.06}, {"label": "Feb", "change": null},],
      "options": {"culture": "EN-us", "scale": 1000, "unit": "k", "tolerance": 0.01,
                  "restShare": 0.1, "width": 400, "labels": {"reference": "Target"}},
    }"""
    chart, options = financial.parse(block)
    assert chart == GrowthTrendChart(
        title="Wachstum",
        last_actual=1,
        reference=0.05,
        months=(TrendMonth("Jan", 0.06), TrendMonth("Feb", None)),
    )
    assert options == FinancialChartOptions(
        culture="en-US",
        scale=1000,
        unit="k",
        tolerance=0.01,
        rest_share=0.1,
        width=400,
        labels=FinancialChartLabels(reference="Target"),
    )


def test_the_document_language_is_the_default_culture() -> None:
    block = financial.to_json(figures.growth_trend())
    german = ChartRenderer().render(request(block))
    english = ChartRenderer().render(request(block, language=Language.EN))
    assert isinstance(german, DrawingGraphic) and isinstance(english, DrawingGraphic)
    german_texts = [i.text for i in german.drawing.items if isinstance(i, DrawingText)]
    english_texts = [i.text for i in english.drawing.items if isinstance(i, DrawingText)]
    assert "Plan (+5,0 %)" in german_texts
    assert "Reference (+5.0%)" in english_texts
    culture = block[:-2] + ',\n  "options": {"culture": "de"}\n}'
    forced = ChartRenderer().render(request(culture, language=Language.EN))
    assert isinstance(forced, DrawingGraphic)
    assert "Plan (+5,0 %)" in [i.text for i in forced.drawing.items if isinstance(i, DrawingText)]


def test_slides_take_their_text_colour() -> None:
    block = financial.to_json(figures.growth_trend())

    def title_colour(format: DocumentFormat) -> str:
        graphic = ChartRenderer().render(request(block, format=format))
        assert isinstance(graphic, DrawingGraphic)
        return next(i.color for i in graphic.drawing.items if isinstance(i, DrawingText))

    assert title_colour(DocumentFormat.PPTX) == colors.TEXT_SLIDES
    assert title_colour(DocumentFormat.DOCX) == colors.TEXT_WORD


@pytest.mark.parametrize(
    ("block", "line", "message"),
    [
        ('{"type": "pie"}', 10, "'pie' is not a type; valid: development, growth-by-row"),
        ('{"title": "x"}', 10, 'needs a "type": development, growth-by-row'),
        ('{\n"type": "growth-trend",\n"lastActuals": 3}', 12, "unknown property 'lastActuals'"),
        (
            '{"type": "growth-trend", "months": [\n{"label": "Jan", "change": "viel"}]}',
            11,
            "'months[0].change' must be a number, not the text 'viel'",
        ),
        ('{"type": "growth-trend", "lastActual": 2.5}', 10, "'lastActual' must be a whole"),
        ('{"type": "growth-trend", "months": [{"label": "Jan"}]}', 10, "'months[0].change' is"),
        (
            '{"type": "development", "lowerPanel": "pie"}',
            10,
            "'lowerPanel' must be one of cumulative, growth",
        ),
        (
            '{"type": "growth-trend", "months": [{"label": "Jan", "change": 0.1}],\n'
            '"options": {"culture": "xx-nowhere"}}',
            11,
            "'xx-nowhere' is not a culture of the financial charts; valid: de, de-DE, en",
        ),
        ('{"type": "growth-trend",\n "options": {"labels": {"plan": "x"}}}', 11, "unknown label"),
        ('{"type": "growth-trend", "options": {"scale": 0}}', 10, "must be greater than 0"),
        ("not json", 10, "is not valid JSON: unexpected 'n'"),
        ('{"type": "growth-trend",\n\n "title": "a" "b"}', 12, "is not valid JSON"),
        ('{"type": "x", "type": "y"}', 10, "'type' appears twice"),
        (
            '{"type": "two-year", "months": ["Jan"], "series": [{"label": "a", "values": [1, 2]}]}',
            9,
            "has 2 values for 1 months",
        ),
    ],
)
def test_mistakes_name_the_line_and_the_problem(block: str, line: int, message: str) -> None:
    with pytest.raises(FinancialChartError) as failure:
        ChartRenderer().render(request(block))
    text = str(failure.value)
    assert text.startswith(f"Line {line}: The financial-chart block cannot be drawn: "), text
    assert message in text


def test_words_after_the_language_are_a_mistake() -> None:
    with pytest.raises(ValueError, match=r"^Line 9: .*'growth' after ```financial-chart"):
        ChartRenderer().render(request("{}", info="financial-chart growth"))


def test_a_mistake_becomes_a_document_conversion_error() -> None:
    with pytest.raises(DocumentConversionError) as failure:
        render((ChartRenderer(),), request("{}"))
    assert failure.value.format is DocumentFormat.PPTX
    assert failure.value.reason.startswith("Line 10: The financial-chart block cannot be drawn")


def test_the_authoring_guides_example_draws() -> None:
    match = re.search(r"```financial-chart\n(.*?)```", AUTHORING_GUIDE, re.DOTALL)
    assert match is not None
    graphic = ChartRenderer().render(request(match.group(1)))
    assert isinstance(graphic, DrawingGraphic)
    found = [i.text for i in graphic.drawing.items if isinstance(i, DrawingText)]
    assert "Wachstum Aufträge (Mai 2026)" in found
    assert "Ziel 5 %" in found
