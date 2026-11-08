"""E15-S04: ``.grey`` and ``.round`` with Pillow, as new resources beside the original."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from pta_documents import DocumentConversionError
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common.generated_images import add_generated
from pta_documents.generation.common.image_attributes import Focus
from pta_documents.generation.common.image_styles import grey, round_png
from pta_documents.markdown import DocumentResource, MarkdownDocument
from pta_documents.markdown.parser import parse

RED = (220, 0, 0)
BLUE = (0, 0, 200)


def picture(size: tuple[int, int] = (200, 100), mode: str = "RGB") -> bytes:
    """Left half red, right half blue (with alpha: opaque)."""
    image = Image.new(mode, size, (*RED, 255) if mode == "RGBA" else RED)
    image.paste((*BLUE, 255) if mode == "RGBA" else BLUE, (size[0] // 2, 0, *size))
    output = io.BytesIO()
    image.save(output, "PNG", dpi=(150, 150))
    return output.getvalue()


def opened(content: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(content))
    image.load()
    return image


def test_grey_is_a_greyscale_png_with_the_same_size_and_dpi() -> None:
    result = opened(grey(picture()))
    assert result.format == "PNG" and result.mode == "L"
    assert result.size == (200, 100)
    assert result.info["dpi"] == pytest.approx((150, 150), abs=0.1)
    left, right = result.getpixel((10, 50)), result.getpixel((190, 50))
    assert isinstance(left, int) and isinstance(right, int) and left != right


def test_grey_keeps_transparency() -> None:
    source = Image.new("RGBA", (10, 10), (*RED, 0))
    output = io.BytesIO()
    source.save(output, "PNG")
    result = opened(grey(output.getvalue()))
    assert result.mode == "LA"
    assert result.getpixel((5, 5)) == (result.getpixel((5, 5))[0], 0)  # type: ignore[index]


def test_round_is_a_square_around_the_focus_with_transparent_corners() -> None:
    centre = opened(round_png(picture(), Focus(0.5, 0.5)))
    assert centre.mode == "RGBA" and centre.size == (100, 100)
    assert centre.getpixel((0, 0)) == (*RED, 0)  # corner outside the circle
    assert centre.getpixel((99, 99))[3] == 0  # type: ignore[index]
    assert centre.getpixel((25, 50)) == (*RED, 255)
    assert centre.getpixel((75, 50)) == (*BLUE, 255)
    left = opened(round_png(picture(), Focus(0.0, 0.5)))
    assert left.getpixel((75, 50)) == (*RED, 255)  # all of the square is the red half
    right = opened(round_png(picture(), Focus(1.0, 0.5)))
    assert right.getpixel((25, 50)) == (*BLUE, 255)


def test_round_of_a_tall_image() -> None:
    result = opened(round_png(picture((100, 300)), Focus(0.5, 0.0)))
    assert result.size == (100, 100)


def styled(text: str, format: DocumentFormat = DocumentFormat.DOCX) -> MarkdownDocument:
    document = MarkdownDocument(
        text, (DocumentResource("images/foto.png", "image/png", picture()),)
    )
    tokens = parse(text)
    result = add_generated(document, tokens, format, 0)
    sources = [
        str(c.attrs["src"])
        for t in tokens
        if t.type == "inline"
        for c in t.children or []
        if c.type == "image"
    ]
    return MarkdownDocument("\n".join(sources), result.resources)


def test_styles_become_resources_beside_the_original_and_the_image_points_at_them() -> None:
    result = styled(
        "![a](images/foto.png){.grey}\n\n![b](images/foto.png){.round}\n\n"
        "![c](images/foto.png){.grey .round}\n\n![d](images/foto.png)\n\n"
        "![e](images/foto.png){.grey focus=top}\n"
    )
    assert result.text.split("\n") == [
        "images/foto-grey.png",
        "images/foto-round.png",
        "images/foto-grey-round.png",
        "images/foto.png",
        "images/foto-grey.png",  # the same picture: one resource
    ]
    assert [r.path for r in result.resources] == [
        "images/foto.png",
        "images/foto-grey.png",
        "images/foto-round.png",
        "images/foto-grey-round.png",
    ]
    assert all(r.content_type == "image/png" for r in result.resources)
    both = opened(result.resources[3].content)
    assert both.mode == "RGBA" and both.size == (100, 100)


def test_another_focus_makes_another_round_picture() -> None:
    result = styled("![a](images/foto.png){.round focus=left}\n\n![b](images/foto.png){.round}\n")
    assert result.text.split("\n") == ["images/foto-round.png", "images/foto-round-2.png"]


def test_powerpoint_keeps_round_for_its_geometry() -> None:
    result = styled(
        "![a](images/foto.png){.round}\n\n![b](images/foto.png){.round .grey}\n",
        DocumentFormat.PPTX,
    )
    assert result.text.split("\n") == ["images/foto.png", "images/foto-grey.png"]


def test_a_style_on_an_svg_is_an_error_with_its_line() -> None:
    svg = DocumentResource(
        "images/plan.svg", "image/svg+xml", b"<svg xmlns='http://www.w3.org/2000/svg'/>"
    )
    text = "Text\n\n![a](images/plan.svg){.grey}\n"
    with pytest.raises(DocumentConversionError) as error:
        add_generated(MarkdownDocument(text, (svg,)), parse(text), DocumentFormat.DOCX, 0)
    assert error.value.reason.startswith(
        "Line 3: The image 'images/plan.svg' is a image/svg+xml; .grey takes PNG, JPEG"
    )


def test_a_missing_resource_is_left_to_the_writer() -> None:
    text = "![a](images/none.png){.grey}\n"
    document = MarkdownDocument(text)
    assert add_generated(document, parse(text), DocumentFormat.DOCX, 0) is document
