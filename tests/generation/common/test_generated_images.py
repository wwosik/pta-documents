"""E11-S04: QR codes from ``![…](qr:…)`` in Word and PowerPoint."""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from pta_documents import DocumentConversionError
from pta_documents.conversions.docx import DocxConverter
from pta_documents.conversions.pptx import PptxConverter
from pta_documents.design import colors
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common import generated_images
from pta_documents.generation.common.generated_images import (
    EDGE_PIXELS,
    MAX_CHARACTERS,
    SCALE,
    add_generated,
    is_generated,
    qr_content,
    qr_png,
    resolve,
)
from pta_documents.generation.common.style_rules import StyleCodes, style_notes
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument
from pta_documents.markdown.parser import parse
from tests.expected import UPDATE_VARIABLE
from tests.generation.docx.conftest import generate as generate_docx
from tests.generation.docx.conftest import open_docx
from tests.generation.pptx.conftest import generate as generate_pptx
from tests.generation.pptx.conftest import open_pptx

SAMPLES = Path(__file__).parent / "samples"
URL = "https://umfrage.example/abc"
EMU_PER_CM = 360_000
DOCX = DocumentFormat.DOCX
PPTX = DocumentFormat.PPTX
REPORT = "---\nvorlage: hoch-ohne-deckblatt\n---\n"
WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"


def rgb(hex_colour: str) -> tuple[int, int, int]:
    return (int(hex_colour[0:2], 16), int(hex_colour[2:4], 16), int(hex_colour[4:6], 16))


def pixels(png: bytes) -> tuple[tuple[int, int], bytes]:
    with Image.open(io.BytesIO(png)) as image:
        return image.size, image.convert("RGB").tobytes()


# ---------------------------------------------------------------------- the PNG


def test_the_png_matches_the_expected_file() -> None:
    """No decoder in the tests (answer to question 1): the PNG of a known link is compared
    pixel by pixel with one a phone scanner read."""
    expected = SAMPLES / "qr-umfrage.expected.png"
    png = qr_png(URL)
    if os.environ.get(UPDATE_VARIABLE) == "1":
        expected.write_bytes(png)
    assert pixels(png) == pixels(expected.read_bytes())


def test_the_png_is_pta_blue_on_white_and_3_cm_wide() -> None:
    png = qr_png(URL)
    with Image.open(io.BytesIO(png)) as image:
        width, height = image.size
        used = {colour for _, colour in image.convert("RGB").getcolors() or []}
        dpi = float(image.info["dpi"][0])
    assert width == height >= EDGE_PIXELS
    assert width < EDGE_PIXELS * 1.1
    assert used == {rgb(colors.PTA_BLUE), rgb(colors.WHITE)}
    assert width / dpi * 2.54 == pytest.approx(3.0, abs=0.01)


def test_the_quiet_zone_is_white_and_short_content_is_no_micro_qr_code() -> None:
    with Image.open(io.BytesIO(qr_png("A"))) as image:
        size = image.size[0]
        module = size // 29  # version 1 (21 modules) and 4 modules of quiet zone on each side
        assert size == 29 * module
        rgb_image = image.convert("RGB")
        border = {rgb_image.getpixel((x, x)) for x in range(4 * module)}
    assert border == {rgb(colors.WHITE)}


# ---------------------------------------------------------------------- references


@pytest.mark.parametrize(
    ("reference", "generated"),
    [
        ("qr:https://x.example", True),
        ("QR:tel:+49301234", True),
        (" qr:text", True),
        ("images/qr.png", False),
        ("https://x.example/qr:a", False),
        ("foto:portrait", False),
    ],
)
def test_only_the_qr_scheme_is_generated(reference: str, generated: bool) -> None:
    assert is_generated(reference) is generated


@pytest.mark.parametrize(
    ("reference", "content"),
    [
        ("qr:https://x.example/a%20b", "https://x.example/a%20b"),
        (
            "qr:mailto:info@pta.example?subject=Hallo%20PTA",
            "mailto:info@pta.example?subject=Hallo%20PTA",
        ),
        ("qr:WIFI:T:WPA;S:Mein%20Netz;P:geheim;;", "WIFI:T:WPA;S:Mein Netz;P:geheim;;"),
        ("qr:tel:+49%2030%201234", "tel:+49 30 1234"),
    ],
)
def test_urls_stay_encoded_other_contents_are_decoded(reference: str, content: str) -> None:
    assert qr_content(reference) == content


def test_a_resource_is_made_under_the_reference() -> None:
    resource = resolve(f"qr:{URL}", DOCX)
    assert (resource.path, resource.content_type) == (f"qr:{URL}", "image/png")
    assert resource.content == qr_png(URL)


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("x" * (MAX_CHARACTERS + 1), f"Line 7: The QR code has {MAX_CHARACTERS + 1} characters"),
        ("", "Line 7: The QR code has no content"),
    ],
)
def test_too_long_or_empty_content_is_an_error_with_its_line(content: str, expected: str) -> None:
    with pytest.raises(DocumentConversionError) as error:
        resolve(f"qr:{content}", DOCX, 7)
    assert error.value.reason.startswith(expected)
    resolve(f"qr:{'x' * MAX_CHARACTERS}", DOCX, 7)


def test_add_generated_adds_each_code_once_and_keeps_given_resources() -> None:
    given = DocumentResource("qr:given", "image/png", b"own")
    text = "![a](qr:one)\n\n![b](qr:one) ![c](qr:given)\n\n![d](images/a.png)\n"
    document = MarkdownDocument(text, (given,))
    result = add_generated(document, parse(text), DOCX, 0)
    assert [r.path for r in result.resources] == ["qr:given", "qr:one"]
    assert result.find_resource("qr:given") is given
    unchanged = MarkdownDocument("![d](images/a.png)\n")
    assert add_generated(unchanged, parse(unchanged.text), DOCX, 0) is unchanged


def test_scale_moves_from_the_title_into_the_meta() -> None:
    tokens = parse('![a](qr:x "Umfrage scale=0,5 heute")\n\n![b](qr:x "scale=2")\n')
    add_generated(MarkdownDocument(""), tokens, DOCX, 0)
    first, second = (t.children[0] for t in tokens if t.type == "inline" and t.children)
    assert first.attrs["title"] == "Umfrage heute"
    assert first.meta[SCALE] == 0.5
    assert "title" not in second.attrs
    assert generated_images.scale_of(second) == 2.0


@pytest.mark.parametrize("scale", ["0", "-1", "abc", "6", ""])
def test_a_broken_scale_is_an_error_with_its_line(scale: str) -> None:
    text = f'Text\n\n![a](qr:x "scale={scale}")\n'
    with pytest.raises(DocumentConversionError) as error:
        add_generated(MarkdownDocument(text), parse(text), DOCX, 2)
    assert error.value.reason.startswith(f"Line 5: 'scale={scale}' is no scale")


def test_scale_in_the_title_of_an_ordinary_image_stays_text() -> None:
    tokens = parse('![a](images/a.png "Foto scale=0.5")\n')
    add_generated(MarkdownDocument(""), tokens, DOCX, 0)
    image = tokens[1].children[0] if tokens[1].children else None
    assert image is not None and image.attrs["title"] == "Foto scale=0.5"


# ---------------------------------------------------------------------- Word


def extents(data: bytes) -> list[tuple[int, int]]:
    root = open_docx(data).element
    return [(int(e.get("cx", "0")), int(e.get("cy", "0"))) for e in root.iter(f"{WP}extent")]


def test_word_shows_a_qr_code_3_cm_wide_with_its_caption() -> None:
    data = generate_docx(f'{REPORT}\n![Zur Umfrage](qr:{URL} "Feedback zur Schulung")\n')
    [(width, height)] = extents(data)
    assert width == height
    assert width == pytest.approx(3 * EMU_PER_CM, rel=0.01)
    texts = [p.text for p in open_docx(data).paragraphs]
    assert "Abbildung 1: Feedback zur Schulung" in texts


def test_word_scales_a_qr_code_and_leaves_scale_out_of_the_caption() -> None:
    data = generate_docx(
        f'{REPORT}\n![Zur Umfrage](qr:{URL} "{URL} scale=0.5")\n\n![Groß](qr:{URL} "scale=2")\n'
    )
    [(small, _), (large, _)] = extents(data)
    assert small == pytest.approx(1.5 * EMU_PER_CM, rel=0.01)
    assert large == pytest.approx(6 * EMU_PER_CM, rel=0.01)
    texts = [p.text for p in open_docx(data).paragraphs]
    assert f"Abbildung 1: {URL}" in texts
    assert "Abbildung 2: Groß" in texts


@pytest.mark.parametrize(
    ("generate", "markdown", "expected"),
    [
        (
            generate_docx,
            f"{REPORT}\n![a](foto:portrait)\n",
            "'foto:portrait' (line 5) is not among",
        ),
        (
            generate_pptx,
            "# D\n\n## F\n\n![a](foto:portrait)\n",
            "'foto:portrait' is not among the document's resources (line 5)",
        ),
        (generate_docx, f"{REPORT}\n![a](qr:{'x' * 1001})\n", "Line 5: The QR code has 1001"),
        (generate_pptx, f"# D\n\n## F\n\n![a](qr:{'x' * 1001})\n", "Line 5: The QR code has"),
    ],
)
def test_an_unknown_scheme_or_a_too_long_code_is_an_error_with_its_line(
    generate: Any, markdown: str, expected: str
) -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate(markdown)
    assert expected in error.value.reason


def test_word_round_trips_the_qr_code_as_an_ordinary_image() -> None:
    data = generate_docx(f'{REPORT}\n![Zur Umfrage](qr:{URL} "Feedback")\n')
    document = DocxConverter().convert(data)
    [resource] = document.resources
    assert f"![Zur Umfrage]({resource.path}" in document.text
    assert resource.path.startswith("images/") and resource.path.endswith(".png")
    assert pixels(resource.content) == pixels(qr_png(URL))


# ---------------------------------------------------------------------- PowerPoint


def pictures(data: bytes) -> list[Any]:
    return [
        shape
        for slide in open_pptx(data).slides
        for shape in slide.shapes
        if type(shape).__name__ in ("Picture", "PlaceholderPicture")
    ]


def test_a_slide_fits_the_qr_code_into_the_picture_placeholder_without_cropping() -> None:
    data = generate_pptx(
        f"# Deck\n\n## Feedback\n\nScannen Sie den Code.\n\n![Umfrage](qr:{URL})\n"
    )
    [picture] = pictures(data)
    assert (picture.crop_left, picture.crop_right, picture.crop_top, picture.crop_bottom) == (
        0,
        0,
        0,
        0,
    )
    left, top, width, height = box(picture)
    assert width == height
    layout = open_pptx(data).slides[1].slide_layout
    [room] = [
        box(p)
        for p in layout.placeholders
        if p.placeholder_format.idx == picture.placeholder_format.idx
    ]
    room_left, room_top, room_width, room_height = room
    assert room_left <= left and left + width <= room_left + room_width + 1
    assert room_top <= top and top + height <= room_top + room_height + 1
    assert width == min(room_width, room_height)


def box(shape: Any) -> tuple[int, int, int, int]:
    return (int(shape.left), int(shape.top), int(shape.width), int(shape.height))


def test_scale_shrinks_the_qr_code_on_a_slide() -> None:
    full = box(pictures(generate_pptx(f"# D\n\n## F\n\nText.\n\n![U](qr:{URL})\n"))[0])
    half = box(pictures(generate_pptx(f'# D\n\n## F\n\nText.\n\n![U](qr:{URL} "scale=0.5")\n'))[0])
    assert half[2] == pytest.approx(full[2] / 2, abs=2)
    assert half[0] + half[2] // 2 == pytest.approx(full[0] + full[2] // 2, abs=2)


def test_a_qr_code_on_a_slide_needs_no_notes_and_round_trips_as_an_image() -> None:
    markdown = f"# Deck\n\n## Feedback\n\nScannen Sie den Code.\n\n![Umfrage](qr:{URL})\n"
    output = io.BytesIO()
    result = PptxGenerator().generate(MarkdownDocument(markdown), output)
    assert result.notes == ()
    document = PptxConverter().convert(output.getvalue())
    [resource] = document.resources
    assert f"![Umfrage]({resource.path})" in document.text
    assert pixels(resource.content) == pixels(qr_png(URL))


# ---------------------------------------------------------------------- style rules


@pytest.mark.parametrize("format", [DOCX, PPTX], ids=lambda f: f.value)
def test_a_qr_code_names_no_source(format: DocumentFormat) -> None:
    markdown = f"# Deck\n\n## Feedback\n\nText.\n\n![Umfrage](qr:{URL})\n"
    notes = style_notes(MarkdownDocument(markdown), format, sources=True)
    assert StyleCodes.IMAGE_SOURCE not in [n.code for n in notes]
    photo = markdown.replace(f"qr:{URL}", "images/foto.jpg")
    notes = style_notes(MarkdownDocument(photo), format, sources=True)
    assert StyleCodes.IMAGE_SOURCE in [n.code for n in notes]
