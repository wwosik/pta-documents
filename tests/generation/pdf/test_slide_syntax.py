"""E05-S04: the slide-layout syntax in the PDF, shown plainly as in Word (port of DocLibs
``SlideLayoutSyntaxTests``; the sample and the mistakes run in
``tests/generation/common/test_layout_syntax.py`` for every format)."""

from __future__ import annotations

from pta_documents.generation.common.result import NoteCodes, Notes
from tests.generation.pdf.layout.support import Pdf, make_pdf


def test_a_statement_is_bold_and_columns_lose_their_rules() -> None:
    markdown = (
        "::: statement\nDer Kern der Sache.\n\nDie Begründung.\n:::\n\n"
        "::: columns\nLinks.\n\n---\n\nRechts.\n:::\n"
    )
    notes = Notes()
    data = make_pdf(markdown, notes=notes)
    pdf = Pdf(data)
    assert "Bold" in pdf.line("Der Kern").font
    assert "Bold" not in pdf.line("Die Begründung").font
    assert pdf.line("Links.").text == "Links." and pdf.line("Rechts.").text == "Rechts."
    assert len(notes) == 0


def test_alerts_start_with_their_kind_in_bold_and_notes_are_left_out() -> None:
    notes = Notes()
    data = make_pdf(
        "## T\n\n> [!WARNING]\n> Vorsicht, Stufe.\n\n::: notes\nGeheim.\n:::\n", notes=notes
    )
    pdf = Pdf(data)
    line = pdf.line("Warnung:")
    assert line.text == "Warnung: Vorsicht, Stufe."
    assert "Bold" in line.font
    assert [n.code for n in notes.to_tuple()] == [NoteCodes.NOTES_DROPPED]
