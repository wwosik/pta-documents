"""E06-S01: the ``chart`` renderer."""

from __future__ import annotations

import pytest

from pta_documents.charts.renderer import ChartRenderer
from pta_documents.design import colors
from pta_documents.design.variants import Language
from pta_documents.drawing import DrawingText
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.renderers import (
    ChartGraphic,
    CodeBlockRequest,
    default_renderers,
    render,
)
from tests.charts.test_parser import ORDERS


def request(
    info: str,
    code: str = ORDERS,
    format: DocumentFormat = DocumentFormat.DOCX,
    dark: bool = False,
) -> CodeBlockRequest:
    return CodeBlockRequest(info, code, 3, format, Language.DE, dark)


def test_only_chart_blocks_without_regard_to_case() -> None:
    renderer = ChartRenderer()
    assert renderer.render(request("mermaid", "graph TD")) is None
    assert renderer.render(request("plantuml", "a -> b")) is None
    graphic = renderer.render(request("Chart"))
    assert isinstance(graphic, ChartGraphic)
    assert graphic.chart.colors == colors.ACCENTS
    assert graphic.chart.title == "Orders by month"


def test_the_drawing_has_the_text_colour_of_the_format() -> None:
    def text_colours(format: DocumentFormat = DocumentFormat.DOCX, dark: bool = False) -> set[str]:
        graphic = ChartRenderer().render(request("chart", format=format, dark=dark))
        assert isinstance(graphic, ChartGraphic)
        return {i.color for i in graphic.drawing.items if isinstance(i, DrawingText)}

    assert text_colours() == {colors.TEXT_WORD}
    assert text_colours(format=DocumentFormat.PPTX) == {colors.TEXT_SLIDES}
    assert text_colours(format=DocumentFormat.PPTX, dark=True) == {colors.WHITE}


def test_words_after_chart_are_a_mistake() -> None:
    with pytest.raises(ValueError, match=r"^Line 3: .*'bar' after ```chart is not read"):
        ChartRenderer().render(request("chart bar"))


def test_a_mistake_becomes_a_document_conversion_error_with_its_line() -> None:
    with pytest.raises(DocumentConversionError) as error:
        render((ChartRenderer(),), request("chart", "x, a\n1, lots\n", format=DocumentFormat.PPTX))
    assert error.value.format is DocumentFormat.PPTX
    assert error.value.reason.startswith("Line 5: The chart block cannot be drawn: 'lots'")
    assert isinstance(error.value.__cause__, ValueError)


def test_the_generators_have_it_by_default_with_an_authoring_guide() -> None:
    assert ChartRenderer() in default_renderers()
    guide = ChartRenderer().authoring_guide
    assert guide is not None and guide.startswith("## Charts") and "```chart" in guide
