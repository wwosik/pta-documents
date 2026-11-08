"""E15-S04: image attributes in Word — styles as pictures, no crop, errors with the line."""

from __future__ import annotations

import io
import zipfile

import pytest
from PIL import Image

from pta_documents import DocumentConversionError
from pta_documents.conversions.docx import DocxConverter
from pta_documents.generation.common.result import NoteCodes
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument
from tests.generation.docx.conftest import generate, open_docx

REPORT = "---\nvorlage: hoch-ohne-deckblatt\n---\n"
WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"


def photo() -> DocumentResource:
    output = io.BytesIO()
    Image.new("RGB", (300, 150), (0, 100, 200)).save(output, "PNG")
    return DocumentResource("images/foto.png", "image/png", output.getvalue())


RESOURCES = (photo(),)


def media(data: bytes) -> list[Image.Image]:
    archive = zipfile.ZipFile(io.BytesIO(data))
    found: list[Image.Image] = []
    for name in sorted(archive.namelist()):
        if name.startswith("word/media/") and name.endswith(".png"):
            image = Image.open(io.BytesIO(archive.read(name)))
            image.load()
            found.append(image)
    return found


def extents(data: bytes) -> list[tuple[int, int]]:
    root = open_docx(data).element
    return [(int(e.get("cx", "0")), int(e.get("cy", "0"))) for e in root.iter(f"{WP}extent")]


def test_round_is_a_masked_square_and_grey_a_greyscale_picture() -> None:
    data = generate(
        f"{REPORT}\n![a](images/foto.png){{.round}}\n\n![b](images/foto.png){{.grey}}\n",
        resources=RESOURCES,
    )
    shown = [image for image in media(data) if image.size != (300, 150) or image.mode == "L"]
    modes = sorted((image.mode, image.size) for image in shown)
    assert modes == [("L", (300, 150)), ("RGBA", (150, 150))]
    [circle] = [image for image in shown if image.mode == "RGBA"]
    assert circle.getpixel((0, 0))[3] == 0  # type: ignore[index]
    assert circle.getpixel((75, 75))[3] == 255  # type: ignore[index]
    round_size, _ = extents(data)
    assert round_size[0] == round_size[1]


def test_focus_and_fit_change_nothing_in_word() -> None:
    plain = generate(f"{REPORT}\n![a](images/foto.png)\n", resources=RESOURCES)
    given = generate(
        f"{REPORT}\n![a](images/foto.png){{focus=top fit=contain}}\n", resources=RESOURCES
    )
    assert extents(plain) == extents(given)


def test_scale_in_the_braces_scales_and_the_title_works_with_a_note() -> None:
    full = extents(generate(f"{REPORT}\n![a](images/foto.png)\n", resources=RESOURCES))[0]
    half = extents(generate(f"{REPORT}\n![a](images/foto.png){{scale=0.5}}\n", resources=RESOURCES))
    assert half[0][0] == pytest.approx(full[0] / 2, abs=2)
    output = io.BytesIO()
    result = DocxGenerator().generate(
        MarkdownDocument(f'{REPORT}\n![a](images/foto.png "Foto scale=0.5")\n', RESOURCES), output
    )
    assert [n.code for n in result.notes] == [NoteCodes.IMAGE_SCALE_IN_TITLE]
    assert result.notes[0].line == 5
    assert extents(output.getvalue())[0][0] == pytest.approx(full[0] / 2, abs=2)
    assert "Abbildung 1: Foto" in [p.text for p in open_docx(output.getvalue()).paragraphs]


def test_an_unknown_attribute_is_an_error_with_its_line() -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate(f"{REPORT}\nText\n\n![a](images/foto.png){{.shadow}}\n", resources=RESOURCES)
    assert error.value.reason.startswith("Line 7: Unknown image attribute '.shadow'")


def test_the_round_trip_gives_the_styled_picture_without_attributes() -> None:
    data = generate(f"{REPORT}\n![Foto](images/foto.png){{.round}}\n", resources=RESOURCES)
    document = DocxConverter().convert(data)
    assert "![Foto](images/" in document.text and "{.round}" not in document.text
    [resource] = document.resources
    with Image.open(io.BytesIO(resource.content)) as image:
        assert image.mode == "RGBA" and image.size == (150, 150)
