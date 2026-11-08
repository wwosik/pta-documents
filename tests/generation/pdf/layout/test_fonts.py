from __future__ import annotations

from reportlab.lib.fonts import tt2ps
from reportlab.pdfbase import pdfmetrics

from pta_documents.design import fonts
from pta_documents.design.fonts import FontFace
from pta_documents.generation.pdf.layout.fonts import PREFIX, register


def test_faces_are_registered_under_names_from_their_content() -> None:
    first = register(fonts.bundled())
    second = register(fonts.bundled())
    assert first.names == second.names
    assert all(name.startswith(PREFIX) for name in first.names.values())
    assert set(first.names.values()) <= set(pdmetrics_names())
    # Selawik italic is the slanted regular: a face of its own.
    assert first.name(FontFace.ITALIC) != first.name(FontFace.REGULAR)
    assert first.name(FontFace.BOLD_ITALIC) != first.name(FontFace.BOLD)


def pdmetrics_names() -> list[str]:
    return list(pdfmetrics.getRegisteredFontNames())


def test_the_families_resolve_bold_and_italic() -> None:
    registered = register(fonts.bundled())
    text = registered.text
    assert tt2ps(text, 1, 0) == registered.name(FontFace.BOLD)
    assert tt2ps(text, 0, 1) == registered.name(FontFace.ITALIC)
    assert tt2ps(text, 1, 1) == registered.name(FontFace.BOLD_ITALIC)
    assert tt2ps(registered.mono, 1, 0) == registered.name(FontFace.MONO_BOLD)


def test_measuring() -> None:
    registered = register(fonts.bundled())
    assert registered.width("PTA", FontFace.BOLD, 10) > registered.width(
        "PTA", FontFace.REGULAR, 10
    )
    assert 1.1 < registered.line_height() < 1.5
    assert registered.width("\u00a0", FontFace.REGULAR, 10) == registered.width(
        " ", FontFace.REGULAR, 10
    )
