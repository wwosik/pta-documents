"""E06-S03: CSS values and the cascade of an SVG (port of DocLibs ``SvgStyleTests.cs``, with
the colour functions, names and rules mermaid-cli writes)."""

from __future__ import annotations

import pytest
from lxml import etree

from pta_documents.drawing.svg_geometry import SvgDrawingError
from pta_documents.drawing.svg_style import Cascade, SvgStyle, on_white

STYLE = SvgStyle.read(
    "--bg:#FFFFFF;--fg:#1F2937;--accent:#0E7C86;background:var(--bg)",
    """
    text { font-family: 'X', sans-serif; }
    svg {
      --_text: var(--fg);
      --_line: var(--line, color-mix(in srgb, var(--fg) 50%, var(--bg)));
      --_arrow: var(--accent, var(--fg));
      --fs-s: 0.875rem;
    }
    """,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("#0e7c86", "0E7C86"),
        ("#abc", "AABBCC"),
        ("var(--_text)", "1F2937"),
        ("var(--_arrow)", "0E7C86"),
        ("var(--missing, #123456)", "123456"),
        ("var(--_line)", "8F949B"),
        ("color-mix(in srgb, #000000 25%, #FFFFFF)", "BFBFBF"),
        ("color-mix(in srgb, #000000, #FFFFFF 75%)", "BFBFBF"),
        (
            "color-mix(in srgb, color-mix(in srgb, var(--accent, var(--fg)) 50%, var(--bg)) 50%,"
            " #000000)",
            "445F62",
        ),
        ("white", "FFFFFF"),
        ("lightgrey", "D3D3D3"),
        ("rgb(1, 2, 3)", "010203"),
        ("rgb(0 111 185)", "006FB9"),
        ("rgb(12.2499999999, 12.2499999999, 12.2499999999)", "0C0C0C"),
        ("rgba(0, 0, 0, 0.5)", "808080"),
        ("rgb(0 0 0 / 0.5)", "808080"),
        ("hsl(0, 0%, 100%)", "FFFFFF"),
        ("hsl(-120, 0%, 90.1960784314%)", "E6E6E6"),
        ("hsl(120, 100%, 25%)", "008000"),
        ("hsla(0, 0%, 0%, 25%)", "BFBFBF"),
    ],
)
def test_colours_resolve(value: str, expected: str) -> None:
    assert STYLE.color(value) == expected


@pytest.mark.parametrize("value", ["none", "transparent", "rgba(1, 2, 3, 0)"])
def test_none_is_no_colour(value: str) -> None:
    assert STYLE.color(value) is None


def test_current_color_is_the_colour_given() -> None:
    assert STYLE.paint("currentColor", ("123456", 1)) == ("123456", 1)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("var(--fs-s)", 14), ("12", 12), ("12.5px", 12.5), ("1.5em", 24), ("1pt", 4 / 3)],
)
def test_lengths_resolve(value: str, expected: float) -> None:
    assert STYLE.length(value) == pytest.approx(expected)


def test_em_refers_to_the_font_size() -> None:
    assert STYLE.length("1.1em", 10) == pytest.approx(11)


@pytest.mark.parametrize(
    "value",
    [
        "var(--undefined)",
        "color-mix(in oklch, #000000, #FFFFFF)",
        "url(#nowhere)",
        "currentColor",
        "rgb(1, 2)",
        "hsl(10, 20, 30)",
        "notacolour",
    ],
)
def test_unknown_css_raises(value: str) -> None:
    with pytest.raises(SvgDrawingError, match="cannot be drawn"):
        STYLE.color(value)


def test_gradients_stand_for_their_first_stop() -> None:
    style = SvgStyle.read(None, None)
    style.gradients["g"] = "#336699"
    assert style.color("url(#g)") == "336699"


def test_a_translucent_colour_is_mixed_with_white() -> None:
    assert on_white("0000FF", 0.5) == "8080FF"


def tree(markup: str) -> etree._Element:
    return etree.fromstring(markup)


def test_rules_apply_by_importance_specificity_and_order() -> None:
    root = tree(
        '<svg id="s"><g class="node"><rect id="r" class="box" fill="#000"'
        ' style="stroke: #111111"/></g></svg>'
    )
    cascade = Cascade(
        root,
        "#s .node rect{fill:#AAAAAA;stroke:#222222}"
        " rect{fill:#BBBBBB!important}"
        " .box{fill:#CCCCCC}"
        " #s .node .box{stroke-width:2px}"
        " .box{stroke-width:3px}"
        " @keyframes dash{to{stroke-dashoffset:0;}}",
    )
    rect = root.find(".//rect")
    assert rect is not None
    assert cascade.value(rect, "fill") == "#BBBBBB"  # important beats specificity
    assert cascade.value(rect, "stroke") == "#111111"  # the style attribute beats rules
    assert cascade.value(rect, "stroke-width") == "2px"  # specificity beats order
    assert cascade.value(rect, "opacity") is None


def test_a_presentation_attribute_is_the_last_resort_and_empty_is_none() -> None:
    root = tree('<svg><text font-weight="" fill="#123456">x</text></svg>')
    cascade = Cascade(root, "")
    text = root.find("text")
    assert text is not None
    assert cascade.value(text, "fill") == "#123456"
    assert cascade.value(text, "font-weight") is None


def test_a_negative_stroke_width_is_dropped_as_css_drops_it() -> None:
    root = tree('<svg><path class="e"/></svg>')
    cascade = Cascade(root, ".e{stroke-width:2} .e{stroke-width:-4}")
    path = root.find("path")
    assert path is not None
    assert cascade.value(path, "stroke-width") == "2"


def test_pseudo_elements_and_hover_match_nothing() -> None:
    root = tree('<svg><rect class="a"/></svg>')
    cascade = Cascade(root, ".a::before{fill:#111111} .a:hover{fill:#222222}")
    rect = root.find("rect")
    assert rect is not None
    assert cascade.value(rect, "fill") is None


@pytest.mark.parametrize("css", ["@media print { rect { fill: red } }", "rect { fill: red"])
def test_unknown_at_rules_and_broken_css_raise(css: str) -> None:
    with pytest.raises(SvgDrawingError):
        Cascade(tree("<svg><rect/></svg>"), css)
