"""E06-S03: the SVG mermaid-cli draws of each supported type, recorded under ``samples/``, as a
drawing — runs without Node.js. With PTA_DOCUMENTS_UPDATE_EXPECTED=1 and mermaid-cli set up,
the SVGs are drawn anew first (``samples/diagramme.md``), then the drawings written."""

from __future__ import annotations

import os

import pytest

from pta_documents.design import colors
from pta_documents.design.variants import Language
from pta_documents.diagrams.mermaid import SUPPORTED, MermaidRenderer, diagram_type
from pta_documents.drawing import DrawingShape, DrawingText, ShapeKind
from pta_documents.drawing.svg import to_drawing
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common.renderers import CodeBlockRequest
from tests.diagrams.support import SAMPLES, block_of, blocks, mermaid_works, write
from tests.expected import UPDATE_VARIABLE, assert_matches_expected

KINDS = [kind for code in blocks() if (kind := diagram_type(code)) in SUPPORTED]


def recorded(kind: str, *, renew: bool = False) -> bytes:
    """The recorded SVG of ``kind``; with ``renew`` (only the snapshot test, since mermaid's
    output varies from run to run) drawn anew when updating and mermaid-cli is set up."""
    path = SAMPLES / f"mermaid-{kind}.svg"
    if renew and os.environ.get(UPDATE_VARIABLE) == "1" and mermaid_works():
        request = CodeBlockRequest(
            "mermaid", block_of(kind), None, DocumentFormat.PPTX, Language.DE
        )
        path.write_bytes(MermaidRenderer().run(request))
    return path.read_bytes()


def test_the_sample_has_every_supported_type_but_graph() -> None:
    assert sorted(KINDS) == sorted(set(SUPPORTED) - {"graph"})


@pytest.mark.parametrize("kind", KINDS)
def test_every_supported_type_matches_its_recorded_drawing(kind: str) -> None:
    drawing = to_drawing(recorded(kind, renew=True))
    assert_matches_expected(SAMPLES / f"mermaid-{kind}.expected.txt", write(drawing))


@pytest.mark.parametrize("kind", KINDS)
def test_every_type_is_in_pta_colours(kind: str) -> None:
    """Every colour is a PTA colour, a tint of one between it and white, or the black of
    mermaid's sequence arrowheads."""
    drawing = to_drawing(recorded(kind))
    used = {i.fill for i in drawing.items if isinstance(i, DrawingShape)}
    used |= {i.stroke for i in drawing.items if isinstance(i, DrawingShape)}
    used |= {i.color for i in drawing.items if isinstance(i, DrawingText)}
    used.discard(None)
    palette = {
        colors.PTA_BLUE,
        colors.DARK_BLUE,
        colors.LIGHT_BLUE,
        colors.GREY_DARK,
        colors.GREY_MID,
        colors.GREY_LIGHT,
        colors.WHITE,
        colors.TEXT_SLIDES,
        colors.SIGNAL_RED,
    }
    tints = {colors.tint(color, share / 100) for color in palette for share in range(101)}
    black = "0" * 6
    assert {c for c in used if c is not None} - palette - tints - {black} == set()


def test_text_of_the_flowchart_is_in_its_shapes() -> None:
    drawing = to_drawing(recorded("flowchart"))
    words = " ".join(i.text for i in drawing.items if isinstance(i, DrawingText))
    for label in ("Markdown-Dokument", "Front Matter?", "Ausgabe", "Fertig"):
        assert label.split()[0] in words
    kinds = {i.kind for i in drawing.items if isinstance(i, DrawingShape)}
    assert {ShapeKind.RECTANGLE, ShapeKind.ELLIPSE, ShapeKind.PATH} <= kinds


def test_states_are_rounded_rectangles() -> None:
    drawing = to_drawing(recorded("stateDiagram-v2"))
    kinds = {i.kind for i in drawing.items if isinstance(i, DrawingShape)}
    assert ShapeKind.ROUNDED_RECTANGLE in kinds
