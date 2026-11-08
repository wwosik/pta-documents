"""E15-S04: image styles and ``{scale=N}`` in the PDF."""

from __future__ import annotations

import io

import pdfplumber
import pikepdf
import pytest
from PIL import Image

from pta_documents.generation.pdf.generator import PdfGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument

REPORT = "---\nvorlage: hoch-ohne-deckblatt\n---\n"


def photo() -> DocumentResource:
    output = io.BytesIO()
    Image.new("RGB", (300, 150), (0, 100, 200)).save(output, "PNG")
    return DocumentResource("images/foto.png", "image/png", output.getvalue())


def generate(markdown: str) -> bytes:
    output = io.BytesIO()
    PdfGenerator().generate(MarkdownDocument(REPORT + markdown, (photo(),)), output)
    return output.getvalue()


def test_round_has_a_soft_mask_and_grey_is_grey() -> None:
    data = generate("\n![a](images/foto.png){.round}\n\n![b](images/foto.png){.grey}\n")
    with pikepdf.open(io.BytesIO(data)) as pdf:
        found = [
            (int(item.Width), int(item.Height), item.get("/SMask") is not None, item.ColorSpace)
            for page in pdf.pages
            for _, item in page.obj.Resources.XObject.items()
        ]
    assert sorted(found) == [(150, 150, True, "/DeviceRGB"), (300, 150, False, "/DeviceGray")]


def widths(data: bytes) -> list[float]:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return [round(float(image["width"]), 1) for page in pdf.pages for image in page.images]


@pytest.mark.parametrize(
    "markdown", ["![a](images/foto.png){scale=0.5}", '![a](images/foto.png "scale=0.5")']
)
def test_scale_in_the_braces_or_the_title_scales(markdown: str) -> None:
    [full] = widths(generate("\n![a](images/foto.png)\n"))
    [half] = widths(generate(f"\n{markdown}\n"))
    assert half == pytest.approx(full / 2, abs=0.2)
