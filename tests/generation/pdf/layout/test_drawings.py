"""E05-S04: drawings of the code-block renderers as vectors in the PDF (port of DocLibs
``PdfGeneratorTests.CodeBlockRenderers_*`` and
``Drawings_AreVectorPaths_WithCurvesDashesAndColours`` and the drawing cases of
``LayoutTests``)."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pdfplumber
import pytest

from pta_documents.design import colors
from pta_documents.drawing import (
    ClosePath,
    CubicTo,
    Drawing,
    DrawingPath,
    DrawingShape,
    DrawingSpan,
    DrawingText,
    LineTo,
    MoveTo,
    TextAnchor,
)
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.common.renderers import (
    CodeBlockGraphic,
    CodeBlockRequest,
    DrawingGraphic,
    ImageGraphic,
)
from pta_documents.generation.common.result import Notes
from pta_documents.generation.pdf.layout import LayoutSettings, prepare
from tests.generation.pdf.layout.support import image, make_pdf

WIDE: Final = 400.0


@dataclass(frozen=True)
class FunctionRenderer:
    """Takes blocks of ``language`` and returns ``graphic`` (DocLibs ``Samples.Renderer``)."""

    language: str
    graphic: CodeBlockGraphic

    def render(self, request: CodeBlockRequest) -> CodeBlockGraphic | None:
        return self.graphic if request.info.split()[0] == self.language else None

    @property
    def authoring_guide(self) -> str | None:
        return None


def sample_drawing(width: float = WIDE, label: str = "Umsatz") -> Drawing:
    curve = DrawingPath((MoveTo(10, 90), CubicTo(60, 10, 120, 10, 170, 90)))
    return Drawing(
        width,
        120,
        (
            DrawingShape(DrawingPath.rectangle(10, 10, 100, 40), colors.PTA_BLUE, None, 0),
            DrawingShape(curve, None, colors.DARK_BLUE, 2, dash=(6, 3)),
            DrawingShape(
                DrawingPath((MoveTo(200, 20), LineTo(260, 20), LineTo(230, 70), ClosePath())),
                colors.LIGHT_BLUE,
                colors.GREY_DARK,
                1,
                round_joins=True,
            ),
            DrawingText(
                200,
                110,
                (DrawingSpan(label, bold=True), DrawingSpan(" 2026", color=colors.PTA_BLUE)),
                14,
                colors.GREY_DARK,
            ),
        ),
    )


def pdf_of(drawing: Drawing, markdown: str = "```zeichnung\nx\n```\n") -> bytes:
    renderer = FunctionRenderer("zeichnung", DrawingGraphic(drawing))
    return make_pdf(markdown, settings=LayoutSettings(code_block_renderers=(renderer,)))


def test_a_drawing_is_vector_paths_with_curves_dashes_colours_and_searchable_text(
    review_dir: Path,
) -> None:
    data = pdf_of(sample_drawing())
    (review_dir / "pdf-drawing.pdf").write_bytes(data)
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        page = pdf.pages[0]
        assert page.images == []
        text = page.extract_text()
        assert "Umsatz 2026" in text and "zeichnung" not in text
        curves = page.curves
        assert any(c.get("dash") and c["dash"][0] for c in curves), curves
        fills = {tuple(round(v, 3) for v in r["non_stroking_color"]) for r in page.rects}
        assert (0.0, round(111 / 255, 3), round(185 / 255, 3)) in fills
        bold = {c["fontname"] for c in page.chars if c["text"] == "U"}
        plain = {c["fontname"] for c in page.chars if c["text"] == "2"}
        assert bold != plain
        span_colours = {
            text: {
                tuple(round(v, 3) for v in c["non_stroking_color"])
                for c in page.chars
                if c["text"] == text
            }
            for text in ("U", "2")
        }
        assert span_colours["2"] == {(0.0, round(111 / 255, 3), round(185 / 255, 3))}
        assert span_colours["U"] != span_colours["2"]


def test_a_drawing_is_placed_at_three_quarters_of_a_point_per_pixel() -> None:
    data = pdf_of(sample_drawing(width=200))
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        rect = pdf.pages[0].rects[0]
    assert float(rect["width"]) == pytest.approx(100 * 0.75, abs=0.01)


def test_a_wide_drawing_shrinks_to_the_width_of_the_text() -> None:
    data = pdf_of(sample_drawing(width=2000))
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        rect = pdf.pages[0].rects[0]
    width = prepare(LayoutSettings()).frame_width
    # 2000 px are 1500 pt: everything shrinks by the width of the type area over that.
    assert float(rect["width"]) == pytest.approx(100 * 0.75 * width / 1500, rel=0.001)


def test_a_label_too_wide_shrinks_to_seventy_percent_and_keeps_its_anchor() -> None:
    long = "Eine sehr lange Beschriftung"
    drawing = Drawing(
        300,
        60,
        (
            DrawingText.line(
                150, 30, long, 20, colors.GREY_DARK, anchor=TextAnchor.MIDDLE, max_width=1
            ),
            DrawingText.line(150, 55, "Mitte", 20, colors.GREY_DARK, anchor=TextAnchor.MIDDLE),
        ),
    )
    data = pdf_of(drawing)
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        chars = pdf.pages[0].chars
    sizes = {round(float(c["size"]), 2) for c in chars if c["text"] == "E"}
    assert sizes == {round(20 * 0.75 * 0.7, 2)}
    middle = [c for c in chars if c["text"] in "Mitte"][-5:]
    centre = (float(middle[0]["x0"]) + float(middle[-1]["x1"])) / 2
    left = min(float(c["x0"]) for c in chars)
    long_chars = [c for c in chars if float(c["size"]) < 11]
    long_centre = (float(long_chars[0]["x0"]) + float(long_chars[-1]["x1"])) / 2
    assert long_centre == pytest.approx(centre, abs=1.0)
    assert left > 0


def test_a_character_the_fonts_lack_in_a_label_follows_replace_unsupported() -> None:
    drawing = sample_drawing(label="Δ")
    renderer = FunctionRenderer("zeichnung", DrawingGraphic(drawing))
    with pytest.raises(DocumentConversionError, match=r"'Δ' \(U\+0394\)"):
        make_pdf(
            "```zeichnung\n```\n",
            settings=LayoutSettings(code_block_renderers=(renderer,), replace_unsupported=None),
        )
    data = make_pdf(
        "```zeichnung\n```\n", settings=LayoutSettings(code_block_renderers=(renderer,))
    )
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        assert "? 2026" in pdf.pages[0].extract_text()


def test_a_figure_paragraph_after_the_block_becomes_its_caption() -> None:
    data = pdf_of(sample_drawing(), "```zeichnung\n```\n\nAbbildung: Der Umsatz\n")
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        text = pdf.pages[0].extract_text()
    assert "Abbildung 1: Der Umsatz" in text and "Abbildung:" not in text


def test_an_image_of_a_renderer_is_placed_like_a_picture() -> None:
    renderer = FunctionRenderer("bild", ImageGraphic(image("bild.png", 200, 100)))
    notes = Notes()
    data = make_pdf(
        "```bild\n```\n", settings=LayoutSettings(code_block_renderers=(renderer,)), notes=notes
    )
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        (picture,) = pdf.pages[0].images
    assert float(picture["width"]) == pytest.approx(150, abs=0.01)
    assert len(notes) == 0
