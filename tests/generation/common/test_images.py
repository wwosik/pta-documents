"""E02-S04: image converters in DOCX and PPTX (port of the converter cases of DocLibs
``GenerationTests`` and ``SvgConverterTests``)."""

from __future__ import annotations

import io
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field

import docx
import pptx
import pytest
from PIL import Image

from pta_documents import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.images import (
    GENERATOR_SCALE,
    ConvertedImage,
    ImageConverter,
    convert_image,
    default_converters,
)
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import DocumentResource, MarkdownDocument

WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
SVG = DocumentResource("images/logo.svg", "image/svg+xml", b"<svg/>")


def png(width: int, height: int) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (0, 111, 185)).save(buffer, "PNG")
    return buffer.getvalue()


@dataclass
class SvgConverter:
    """Takes ``image/svg+xml``: a PNG of ``scale`` × 200 × 100 pixels, natural size 200 × 100."""

    error: Exception | None = None
    calls: list[tuple[str, float]] = field(default_factory=lambda: list[tuple[str, float]]())
    format: str | None = "SVG"

    def convert(self, image: DocumentResource, scale: float) -> ConvertedImage | None:
        self.calls.append((image.path, scale))
        if image.content_type != "image/svg+xml":
            return None
        if self.error is not None:
            raise self.error
        return ConvertedImage(png(int(200 * scale), int(100 * scale)), "image/png", 200, 100)


@dataclass
class Nothing:
    format: str | None = None

    def convert(self, image: DocumentResource, scale: float) -> ConvertedImage | None:
        return None


Generate = Callable[[str, tuple[ImageConverter, ...]], bytes]


def generate_docx(markdown: str, converters: tuple[ImageConverter, ...]) -> bytes:
    output = io.BytesIO()
    options = DocxOptions(image_converters=converters)
    DocxGenerator().generate(MarkdownDocument(markdown, (SVG,)), output, options)
    return output.getvalue()


def generate_pptx(markdown: str, converters: tuple[ImageConverter, ...]) -> bytes:
    output = io.BytesIO()
    options = PptxOptions(image_converters=converters)
    PptxGenerator().generate(MarkdownDocument(markdown, (SVG,)), output, options)
    return output.getvalue()


GENERATORS = pytest.mark.parametrize(
    ("generate", "format"),
    [(generate_docx, DocumentFormat.DOCX), (generate_pptx, DocumentFormat.PPTX)],
    ids=["docx", "pptx"],
)
ONE = "---\ntitel: T\n---\n\n## A\n\n![Logo](images/logo.svg)\n"
ROW = "---\ntitel: T\n---\n\n## A\n\n![Logo](images/logo.svg) ![Noch eins](images/logo.svg)\n"


def media(data: bytes) -> list[bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return [archive.read(n) for n in archive.namelist() if "/media/" in n]


@GENERATORS
@pytest.mark.parametrize("markdown", [ONE, ROW], ids=["one", "row"])
def test_a_converter_makes_an_svg_placeable(
    generate: Generate, format: DocumentFormat, markdown: str
) -> None:
    converter = SvgConverter()
    data = generate(markdown, (converter,))
    assert converter.calls[0] == ("images/logo.svg", GENERATOR_SCALE)
    sizes = {Image.open(io.BytesIO(m)).size for m in media(data) if m.startswith(b"\x89PNG")}
    assert (400, 200) in sizes


def test_docx_places_a_converted_image_at_its_natural_size() -> None:
    data = generate_docx(ONE, (SvgConverter(),))
    root = docx.Document(io.BytesIO(data)).element
    extent = next(root.iter(f"{WP}extent"))
    assert (int(extent.get("cx", "0")), int(extent.get("cy", "0"))) == (200 * 9525, 100 * 9525)


def test_pptx_keeps_the_alt_text_of_a_converted_image() -> None:
    data = generate_pptx(ROW, (SvgConverter(),))
    deck = pptx.Presentation(io.BytesIO(data))
    alts = [
        str(c.get("descr"))
        for slide in deck.slides
        for picture in slide._element.iter(f"{P}pic")
        for c in picture.iter(f"{P}cNvPr")
    ]
    assert alts == ["Logo", "Noch eins"]


@GENERATORS
def test_the_first_conversion_wins(generate: Generate, format: DocumentFormat) -> None:
    first, second = SvgConverter(), SvgConverter()
    generate(ONE, (Nothing(), first, second))
    assert first.calls and not second.calls


@GENERATORS
@pytest.mark.parametrize("markdown", [ONE, ROW], ids=["one", "row"])
def test_an_svg_without_converter_stays_an_error(
    generate: Generate, format: DocumentFormat, markdown: str
) -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate(markdown, ())
    assert error.value.format is format
    assert "'images/logo.svg'" in error.value.reason
    assert "is a image/svg+xml" in error.value.reason
    assert "converter" not in error.value.reason


@GENERATORS
def test_an_svg_no_converter_takes_says_so(generate: Generate, format: DocumentFormat) -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate(ONE, (Nothing(),))
    assert "no image converter takes it" in error.value.reason


@GENERATORS
def test_a_foreign_error_becomes_a_document_conversion_error(
    generate: Generate, format: DocumentFormat
) -> None:
    cause = OSError("resvg failed")
    with pytest.raises(DocumentConversionError) as error:
        generate(ONE, (SvgConverter(error=cause),))
    assert error.value.format is format
    assert error.value.reason == "The image 'images/logo.svg' cannot be converted: resvg failed"
    assert error.value.__cause__ is cause


@GENERATORS
def test_a_document_conversion_error_passes_unchanged(
    generate: Generate, format: DocumentFormat
) -> None:
    original = DocumentConversionError(DocumentFormat.SVG, "The SVG has no size.")
    with pytest.raises(DocumentConversionError) as error:
        generate(ONE, (SvgConverter(error=original),))
    assert error.value is original


@GENERATORS
def test_supported_images_do_not_go_to_converters(
    generate: Generate, format: DocumentFormat
) -> None:
    converter = SvgConverter()
    output = io.BytesIO()
    image = DocumentResource("a.png", "image/png", png(300, 200))
    markdown = MarkdownDocument("---\ntitel: T\n---\n\n## A\n\n![A](a.png)\n", (image,))
    if format is DocumentFormat.DOCX:
        DocxGenerator().generate(markdown, output, DocxOptions(image_converters=(converter,)))
    else:
        PptxGenerator().generate(markdown, output, PptxOptions(image_converters=(converter,)))
    assert converter.calls == []


def test_convert_image_keeps_the_path() -> None:
    conversion = convert_image((SvgConverter(),), SVG, 1.0, DocumentFormat.DOCX)
    assert conversion is not None
    assert (conversion.image.path, conversion.image.content_type) == (SVG.path, "image/png")
    assert (conversion.width, conversion.height) == (200, 100)
    assert convert_image((), SVG, 1.0, DocumentFormat.DOCX) is None


def test_the_options_default_to_the_available_converters() -> None:
    assert DocxOptions().image_converters == default_converters()
    assert PptxOptions().image_converters == default_converters()
