"""E15-S03, E05-S04: an icon in the text is a small picture standing on the baseline."""

from __future__ import annotations

import io

import pdfplumber

from pta_documents.generation.common.result import Notes
from tests.generation.pdf.layout.support import Pdf, make_pdf


def test_an_icon_is_a_picture_as_high_as_the_text() -> None:
    notes = Notes()
    data = make_pdf("Der Server :icon-server: läuft.\n", notes=notes)
    line = Pdf(data).line("Der Server")
    assert line.text == "Der Server läuft."
    assert len(notes) == 0
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        (icon,) = pdf.pages[0].images
    assert round(float(icon["height"]), 1) == 10.0
    baseline = float(line.chars[0]["matrix"][5])  # PDF coordinates, as the image's y0
    assert abs(float(icon["y0"]) - baseline) < 0.5
