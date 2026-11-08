"""E15-S03: icons in the PDF are left out with a note until E05-S04 draws them."""

from __future__ import annotations

from pta_documents.generation.common.result import NoteCodes, Notes
from tests.generation.pdf.layout.support import Pdf, make_pdf


def test_an_icon_is_left_out_with_a_note() -> None:
    notes = Notes()
    pdf = Pdf(make_pdf("Der Server :icon-server: läuft.\n", notes=notes))
    assert pdf.line("Der Server").text == "Der Server läuft."
    assert [n.code for n in notes.to_tuple()] == [NoteCodes.CODE_NOT_DRAWN]
    assert "':icon-server:'" in notes.to_tuple()[0].message
