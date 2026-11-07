"""E02-S04: code-block renderers in DOCX and PPTX (port of the renderer cases of DocLibs
``PptxGeneratorTests`` and ``GenerationTests``)."""

from __future__ import annotations

import io
from collections.abc import Callable
from dataclasses import dataclass, field

import docx
import pptx
import pytest
from PIL import Image

from pta_documents import DocumentConversionError, DocumentFormat, NoteCodes
from pta_documents.charts import ChartKind, ChartSeries, ChartSpec
from pta_documents.design.variants import Language
from pta_documents.generation.common.renderers import (
    ChartGraphic,
    CodeBlockGraphic,
    CodeBlockRenderer,
    CodeBlockRequest,
    DrawingGraphic,
    ImageGraphic,
    default_renderers,
    render,
)
from pta_documents.generation.common.result import GenerationResult
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import DocumentResource, MarkdownDocument

WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"


def png(width: int = 120, height: int = 80) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (0, 111, 185)).save(buffer, "PNG")
    return buffer.getvalue()


@dataclass
class Recorder:
    """Takes only ``language``; returns ``graphic`` (or raises ``error``) and records requests."""

    language: str = "testbild"
    graphic: CodeBlockGraphic | None = None
    error: Exception | None = None
    requests: list[CodeBlockRequest] = field(default_factory=lambda: list[CodeBlockRequest]())
    authoring_guide: str | None = None

    def render(self, request: CodeBlockRequest) -> CodeBlockGraphic | None:
        self.requests.append(request)
        if request.info.split()[0] != self.language:
            return None
        if self.error is not None:
            raise self.error
        return self.graphic


def sample_graphic() -> ImageGraphic:
    return ImageGraphic(DocumentResource("testbild.png", "image/png", png()))


Generate = Callable[[str, tuple[CodeBlockRenderer, ...]], tuple[bytes, GenerationResult]]


def generate_docx(
    markdown: str, renderers: tuple[CodeBlockRenderer, ...]
) -> tuple[bytes, GenerationResult]:
    output = io.BytesIO()
    options = DocxOptions(code_block_renderers=renderers)
    result = DocxGenerator().generate(MarkdownDocument(markdown), output, options)
    return output.getvalue(), result


def generate_pptx(
    markdown: str, renderers: tuple[CodeBlockRenderer, ...]
) -> tuple[bytes, GenerationResult]:
    output = io.BytesIO()
    options = PptxOptions(code_block_renderers=renderers)
    result = PptxGenerator().generate(MarkdownDocument(markdown), output, options)
    return output.getvalue(), result


GENERATORS = pytest.mark.parametrize(
    ("generate", "format"),
    [(generate_docx, DocumentFormat.DOCX), (generate_pptx, DocumentFormat.PPTX)],
    ids=["docx", "pptx"],
)

DECK = "---\ntitel: T\n---\n\n## A\n```testbild groß\nZeile 1\n```\n"
"""The fence opens in line 6, front matter included."""


def pictures_docx(data: bytes) -> list[str]:
    """The alt texts of the pictures in the body."""
    root = docx.Document(io.BytesIO(data)).element
    return [str(p.get("descr")) for p in root.iter(f"{WP}docPr")]


def pictures_pptx(data: bytes) -> list[str]:
    deck = pptx.Presentation(io.BytesIO(data))
    return [
        str(c.get("descr"))
        for slide in deck.slides
        for picture in slide._element.iter(f"{P}pic")
        for c in picture.iter(f"{P}cNvPr")
    ]


def pictures(data: bytes, format: DocumentFormat) -> list[str]:
    return pictures_docx(data) if format is DocumentFormat.DOCX else pictures_pptx(data)


@GENERATORS
def test_a_renderer_gets_info_code_and_line_after_front_matter(
    generate: Generate, format: DocumentFormat
) -> None:
    renderer = Recorder()
    generate(DECK, (renderer,))
    [request] = renderer.requests
    assert (request.info, request.code, request.line) == ("testbild groß", "Zeile 1\n", 6)
    assert (request.format, request.language, request.dark) == (format, Language.DE, False)


@GENERATORS
def test_an_image_graphic_takes_the_place_of_the_code_block(
    generate: Generate, format: DocumentFormat
) -> None:
    data, result = generate(DECK, (Recorder(graphic=sample_graphic()),))
    assert pictures(data, format) == ["testbild groß"]
    assert NoteCodes.CODE_NOT_DRAWN not in [n.code for n in result.notes]
    if format is DocumentFormat.DOCX:
        text = "\n".join(p.text for p in docx.Document(io.BytesIO(data)).paragraphs)
        assert "Zeile 1" not in text
        assert "Abbildung" not in text  # no caption: it comes with E03-S04 from the title


@GENERATORS
def test_none_leaves_the_block_as_code(generate: Generate, format: DocumentFormat) -> None:
    data, result = generate(DECK.replace("testbild", "mermaid"), (Recorder(),))
    assert pictures(data, format) == []
    assert [n.code for n in result.notes] == [NoteCodes.CODE_NOT_DRAWN]


@GENERATORS
def test_a_drawn_block_is_not_noted(generate: Generate, format: DocumentFormat) -> None:
    renderer = Recorder("mermaid", sample_graphic())
    _, result = generate(DECK.replace("testbild", "mermaid"), (renderer,))
    assert NoteCodes.CODE_NOT_DRAWN not in [n.code for n in result.notes]


@GENERATORS
def test_the_first_graphic_wins(generate: Generate, format: DocumentFormat) -> None:
    first = Recorder(graphic=sample_graphic())
    second = Recorder(graphic=sample_graphic())
    data, _ = generate(DECK, (Recorder("other"), first, second))
    assert len(first.requests) == 1
    assert second.requests == []
    assert len(pictures(data, format)) == 1


@GENERATORS
def test_fences_without_info_and_indented_code_do_not_go_to_renderers(
    generate: Generate, format: DocumentFormat
) -> None:
    renderer = Recorder(graphic=sample_graphic())
    generate("---\ntitel: T\n---\n\n## A\n```\nx\n```\n\n    indented\n", (renderer,))
    assert renderer.requests == []


@GENERATORS
def test_a_foreign_error_becomes_a_document_conversion_error(
    generate: Generate, format: DocumentFormat
) -> None:
    cause = ValueError("broken diagram")
    with pytest.raises(DocumentConversionError) as error:
        generate(DECK, (Recorder(error=cause),))
    assert error.value.format is format
    assert error.value.reason == "broken diagram"
    assert error.value.__cause__ is cause


@GENERATORS
def test_a_document_conversion_error_passes_unchanged(
    generate: Generate, format: DocumentFormat
) -> None:
    original = DocumentConversionError(DocumentFormat.SVG, "line 2: unknown arrow")
    with pytest.raises(DocumentConversionError) as error:
        generate(DECK, (Recorder(error=original),))
    assert error.value is original


CHART = ChartGraphic(ChartSpec(ChartKind.BAR, ("a",), (ChartSeries("s", (1.0,)),)), object())


@pytest.mark.parametrize(
    ("generate", "format", "graphic"),
    [
        (generate_docx, DocumentFormat.DOCX, DrawingGraphic(object())),
        (generate_pptx, DocumentFormat.PPTX, DrawingGraphic(object())),
        (generate_docx, DocumentFormat.DOCX, CHART),
    ],
    ids=["docx-drawing", "pptx-drawing", "docx-chart"],
)
def test_drawings_and_charts_are_not_supported_yet(
    generate: Generate, format: DocumentFormat, graphic: CodeBlockGraphic
) -> None:
    """Drawings follow with E02-S03/E06-S02, charts in Word with E06-S01; PowerPoint places
    charts since E04-S04 (``tests/generation/pptx/test_kinds.py``)."""
    with pytest.raises(DocumentConversionError) as error:
        generate(DECK, (Recorder(graphic=graphic),))
    assert error.value.format is format
    assert error.value.reason.startswith("Line 6: The `testbild` block was rendered as a ")
    assert "does not support yet" in error.value.reason


def test_a_dark_slide_asks_for_a_dark_graphic() -> None:
    renderer = Recorder()
    generate_pptx(
        "# D\n\n## Hell\n```testbild\n1\n```\n\n## Dunkel {.dark}\n```testbild\n2\n```\n",
        (renderer,),
    )
    assert [r.dark for r in renderer.requests] == [False, True]


def test_the_document_language_reaches_the_renderer() -> None:
    renderer = Recorder()
    generate_docx("---\ntitel: T\nsprache: en\n---\n```testbild\n1\n```\n", (renderer,))
    assert renderer.requests[0].language is Language.EN


def test_render_without_renderers_is_none() -> None:
    request = CodeBlockRequest("chart", "", 1, DocumentFormat.DOCX, Language.DE)
    assert render((), request) is None


def test_the_options_default_to_the_available_renderers() -> None:
    assert DocxOptions().code_block_renderers == default_renderers()
    assert PptxOptions().code_block_renderers == default_renderers()


def test_chart_spec_defaults_to_the_pta_accents() -> None:
    spec = ChartSpec(ChartKind.LINE, ("Q1", "Q2"), (ChartSeries("Umsatz", (1.0, None)),))
    assert spec.colors[0] == "006FB9"
    assert not spec.stacked and spec.title is None and spec.unit is None
