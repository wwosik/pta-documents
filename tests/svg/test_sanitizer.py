"""E06-S04: nothing outside an SVG survives cleaning (port of DocLibs ``SvgSanitizer.cs``)."""

from __future__ import annotations

import pytest

from pta_documents import DocumentConversionError, DocumentFormat
from pta_documents.svg import clean

NS = 'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"'


def test_scripts_and_foreign_objects_go_with_their_content_but_the_text_after_stays() -> None:
    svg = f"<svg {NS}><script>alert(1)</script>a<foreignObject><p>x</p></foreignObject>b</svg>"
    assert clean(svg).endswith(">ab</svg>")


def test_external_links_go_internal_ones_and_data_uris_stay() -> None:
    svg = (
        f'<svg {NS}><image href="file:///etc/passwd"/>'
        '<image xlink:href="https://example.org/a.png"/><image href="images/a.png"/>'
        '<use href="#a"/><image xlink:href=" data:image/png;base64,AA"/></svg>'
    )
    cleaned = clean(svg)
    assert "passwd" not in cleaned
    assert "example.org" not in cleaned
    assert "images/a.png" not in cleaned
    assert 'href="#a"' in cleaned
    assert "data:image/png;base64,AA" in cleaned


def test_css_loses_external_urls_and_imports_in_style_elements_and_attributes() -> None:
    svg = (
        f"<svg {NS}><style>@import url(https://example.org/a.css); @import 'b.css';"
        ' .a{fill:url(#g)} .b{fill:url("file:///x.png")}</style>'
        '<rect style="fill:url( http://example.org/p )"/><rect fill="url(#g)"/></svg>'
    )
    cleaned = clean(svg)
    assert "@import" not in cleaned
    assert "example.org" not in cleaned
    assert "file:" not in cleaned
    assert ".a{fill:url(#g)}" in cleaned
    assert ".b{fill:none}" in cleaned
    assert 'style="fill:none"' in cleaned
    assert 'fill="url(#g)"' in cleaned


def test_the_dtd_goes_and_entities_are_never_expanded() -> None:
    svg = (
        '<?xml version="1.0"?><!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">'
        '<!ENTITY a "aaaa"><!ENTITY b "&a;&a;&a;&a;">]>'
        f"<svg {NS}><text>&x;</text><text>&b;!</text><?xml-stylesheet href='a.css'?></svg>"
    )
    cleaned = clean(svg)
    assert "DOCTYPE" not in cleaned
    assert "ENTITY" not in cleaned
    assert "aaaa" not in cleaned
    assert "stylesheet" not in cleaned
    assert "<text>!</text>" in cleaned


@pytest.mark.parametrize("svg", ["not an svg at all", "<html><body/></html>", "<svg", b"\xff\xfe"])
def test_what_is_not_an_svg_is_an_svg_error(svg: str | bytes) -> None:
    with pytest.raises(DocumentConversionError) as error:
        clean(svg)
    assert error.value.format is DocumentFormat.SVG
    assert error.value.reason.startswith("The SVG cannot be converted: ")
