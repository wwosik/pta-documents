"""E15-S04: focus, fit and the image styles in PowerPoint."""

from __future__ import annotations

import io
from typing import Any

import pytest
from PIL import Image

from pta_documents.conversions.pptx import PptxConverter
from pta_documents.generation.common.result import NoteCodes
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument
from tests.generation.pptx.conftest import generate, open_pptx

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def photo(size: tuple[int, int]) -> DocumentResource:
    output = io.BytesIO()
    Image.new("RGB", size, (0, 100, 200)).save(output, "PNG")
    return DocumentResource("images/foto.png", "image/png", output.getvalue())


TALL = (photo((880, 1000)),)
"""Taller than the picture placeholder of "Titel, Text und Bild 01" (about 1.14 : 1)."""
WIDE = (photo((3000, 1000)),)


def slide(image: str) -> str:
    return f"# Deck\n\n## Folie\n\nText.\n\n{image}\n"


def pictures(data: bytes) -> list[Any]:
    return [
        shape
        for page in open_pptx(data).slides
        for shape in page.shapes
        if type(shape).__name__ in ("Picture", "PlaceholderPicture")
    ]


def crop(picture: Any) -> tuple[float, float, float, float]:
    return (
        round(picture.crop_left, 3),
        round(picture.crop_top, 3),
        round(picture.crop_right, 3),
        round(picture.crop_bottom, 3),
    )


def geometry(picture: Any) -> str | None:
    found = picture._element.spPr.find(f"{A}prstGeom")
    return None if found is None else found.get("prst")


def test_the_crop_keeps_the_focus_in_view() -> None:
    [top] = pictures(generate(slide("![F](images/foto.png){focus=top}"), resources=TALL))
    [centre] = pictures(generate(slide("![F](images/foto.png)"), resources=TALL))
    [bottom] = pictures(generate(slide("![F](images/foto.png){focus=bottom}"), resources=TALL))
    left, cut_top, right, cut_bottom = crop(centre)
    assert left == right == 0 and cut_top == cut_bottom > 0
    assert crop(top) == pytest.approx((0, 0, 0, cut_top * 2), abs=0.002)
    assert crop(bottom) == pytest.approx((0, cut_top * 2, 0, 0), abs=0.002)


def test_a_point_as_focus_moves_the_crop_to_it() -> None:
    [picture] = pictures(generate(slide("![F](images/foto.png){focus=0%,50%}"), resources=WIDE))
    left, top, right, bottom = crop(picture)
    assert left == 0 and top == bottom == 0 and right > 0.5


def test_fit_contain_does_not_crop() -> None:
    data = generate(slide("![F](images/foto.png){fit=contain}"), resources=WIDE)
    [picture] = pictures(data)
    assert crop(picture) == (0, 0, 0, 0)
    assert int(picture.width) / int(picture.height) == pytest.approx(3, rel=0.01)


def test_round_is_a_square_in_an_ellipse_in_the_placeholder() -> None:
    data = generate(slide("![F](images/foto.png){.round}"), resources=WIDE)
    [picture] = pictures(data)
    assert geometry(picture) == "ellipse"
    assert int(picture.width) == int(picture.height)
    assert crop(picture) == (round(1 / 3, 3), 0, round(1 / 3, 3), 0)


def test_round_in_a_picture_row_is_a_square_in_an_ellipse() -> None:
    data = generate(
        "# Deck\n\n## Folie\n\n![a](images/foto.png){.round focus=left} ![b](images/foto.png)\n",
        resources=WIDE,
    )
    first, second = pictures(data)
    assert geometry(first) == "ellipse" and geometry(second) != "ellipse"
    assert int(first.width) == int(first.height)
    assert crop(first) == (0, 0, round(2 / 3, 3), 0)


def test_grey_places_a_greyscale_picture() -> None:
    [picture] = pictures(generate(slide("![F](images/foto.png){.grey}"), resources=WIDE))
    with Image.open(io.BytesIO(picture.image.blob)) as placed:
        assert placed.mode == "L"


def notes(markdown: str, resources: tuple[DocumentResource, ...]) -> list[str]:
    result = PptxGenerator().generate(MarkdownDocument(markdown, resources), io.BytesIO())
    return [n.message for n in result.notes if n.code == NoteCodes.IMAGE_CROPPED]


def test_the_cropping_note_suggests_focus_only_when_none_is_written() -> None:
    [without] = notes(slide("![F](images/foto.png)"), WIDE)
    assert "{focus=top}" in without and "{fit=contain}" in without
    [given] = notes(slide("![F](images/foto.png){focus=left}"), WIDE)
    assert "focus" not in given
    assert notes(slide("![F](images/foto.png){fit=contain}"), WIDE) == []
    assert notes(slide("![F](images/foto.png){.round}"), WIDE) == []


def test_round_comes_back_from_powerpoint() -> None:
    data = generate(slide("![Foto](images/foto.png){.round}"), resources=WIDE)
    text = PptxConverter().convert(data).text
    assert "{.round}" in text
    assert text.count("![Foto](") == 1


def test_scale_in_the_braces_shrinks_a_picture_in_a_row() -> None:
    """A placeholder crops to fill itself; ``scale`` shrinks pictures that are fitted."""
    markdown = "# Deck\n\n## Folie\n\n![a](images/foto.png){{scale={}}} ![b](images/foto.png)\n"
    full = pictures(generate(markdown.format(1), resources=WIDE))[0]
    half = pictures(generate(markdown.format(0.5), resources=WIDE))[0]
    assert int(half.width) == pytest.approx(int(full.width) / 2, abs=2)
