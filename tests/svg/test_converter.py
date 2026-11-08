"""E06-S04: SVG to PNG with resvg (port of DocLibs ``SvgConverterTests.cs``)."""

from __future__ import annotations

import base64
import io
from pathlib import Path

import pytest
from PIL import Image

from pta_documents import DocumentConversionError, DocumentFormat
from pta_documents.design import colors
from pta_documents.drawing import (
    Drawing,
    DrawingHotspot,
    DrawingHover,
    DrawingPath,
    DrawingShape,
    ShapeKind,
    to_svg,
)
from pta_documents.svg import MAX_PIXELS, PngOptions, natural_size, to_png

resvg_py = pytest.importorskip("resvg_py")

RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)
SQUARES = """<svg xmlns="http://www.w3.org/2000/svg" width="40" height="20">
  <rect x="0" y="0" width="20" height="20" fill="#FF0000"/>
  <rect x="20" y="0" width="20" height="20" fill="#0000FF"/>
</svg>"""
VIEW_BOX_ONLY = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 150">'
    '<rect width="300" height="150" fill="#00FF00"/></svg>'
)


def image(png: bytes) -> Image.Image:
    return Image.open(io.BytesIO(png)).convert("RGBA")


def pixel(picture: Image.Image, x: int, y: int) -> tuple[int, ...]:
    value = picture.getpixel((x, y))
    assert isinstance(value, tuple)
    return value


def ink_width(png: bytes) -> int:
    box = image(png).getchannel("A").getbbox()
    return 0 if box is None else box[2] - box[0]


def test_the_svg_is_drawn_at_twice_its_size_on_transparency() -> None:
    picture = image(to_png(SQUARES))
    assert picture.size == (80, 40)
    assert pixel(picture, 10, 20) == RED
    assert pixel(picture, 70, 20) == BLUE


def test_the_size_comes_from_width_and_height_else_the_view_box() -> None:
    assert natural_size(SQUARES) == (40.0, 20.0)
    assert natural_size(VIEW_BOX_ONLY) == (300.0, 150.0)
    assert image(to_png(VIEW_BOX_ONLY, PngOptions(width=600))).size == (600, 300)
    assert image(to_png(VIEW_BOX_ONLY, PngOptions(scale=1))).size == (300, 150)


@pytest.mark.parametrize(
    ("attributes", "size"),
    [
        ('width="72pt" height="1in"', (96.0, 96.0)),
        ('width="25.4mm" height="2.54cm"', (96.0, 96.0)),
        ('width="6pc" height="10"', (96.0, 10.0)),
        ('width="200" viewBox="0 0 100 50"', (200.0, 100.0)),
        ('height="100%" viewBox="0 0 100 50"', (100.0, 50.0)),
        ('width="50%" height="25" viewBox="0 0 100 50"', (50.0, 25.0)),
    ],
)
def test_units_and_proportions_of_the_size(attributes: str, size: tuple[float, float]) -> None:
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" {attributes}/>'
    assert natural_size(svg) == pytest.approx(size)


@pytest.mark.parametrize(
    "attributes", ["", 'width="10"', 'width="10%" height="5em"', 'viewBox="0 0 0 10"']
)
def test_an_svg_without_a_size_is_an_svg_error(attributes: str) -> None:
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" {attributes}/>'
    with pytest.raises(DocumentConversionError) as error:
        to_png(svg)
    assert error.value.format is DocumentFormat.SVG
    assert "it has no size" in error.value.reason


def test_a_background_fills_what_the_svg_leaves_open() -> None:
    dot = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        '<circle cx="5" cy="5" r="1" fill="#000000"/></svg>'
    )
    assert pixel(image(to_png(dot)), 0, 0)[3] == 0
    white = image(to_png(dot, PngOptions(background=colors.WHITE)))
    assert pixel(white, 0, 0) == (255, 255, 255, 255)
    with pytest.raises(ValueError, match="not a colour"):
        to_png(dot, PngOptions(background="#FFFFFF"))


def test_a_png_larger_than_the_limit_is_refused() -> None:
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{MAX_PIXELS // 2 + 1}" height="10"/>'
    with pytest.raises(DocumentConversionError) as error:
        to_png(svg)
    assert f"larger than {MAX_PIXELS} pixels a side" in error.value.reason
    with pytest.raises(ValueError, match="positive"):
        to_png(SQUARES, PngOptions(scale=0))


def text(family: str) -> bytes:
    return to_png(
        '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="40">'
        f'<text x="0" y="30" font-family="{family}" font-size="24">Wide wide wide wide</text></svg>'
    )


def test_text_is_set_in_the_bundled_fonts_whatever_the_system_has() -> None:
    selawik = text("Selawik")
    assert ink_width(selawik) > 100
    # No system font is loaded: unknown and generic families fall back to Selawik.
    assert text("Arial") == selawik
    assert text("sans-serif") == selawik
    assert text("Segoe UI, Selawik, sans-serif") == selawik
    assert text("monospace") == text("Inconsolata")
    assert text("monospace") != selawik
    assert text("serif") == selawik
    assert text("Gelasio") != selawik


def test_the_same_svg_gives_the_same_png() -> None:
    assert to_png(SQUARES) == to_png(SQUARES.encode("utf-8"))


@pytest.mark.parametrize("svg", ["not an svg at all", "<html><body/></html>"])
def test_an_svg_that_cannot_be_drawn_is_an_svg_error(svg: str) -> None:
    with pytest.raises(DocumentConversionError) as error:
        to_png(svg)
    assert error.value.format is DocumentFormat.SVG
    assert error.value.reason.startswith("The SVG cannot be converted: ")


def red_png(path: Path) -> Path:
    Image.new("RGB", (10, 10), (255, 0, 0)).save(path, "PNG")
    return path


def test_nothing_outside_the_svg_is_loaded(tmp_path: Path) -> None:
    red = red_png(tmp_path / "red.png")
    css = tmp_path / "a.css"
    css.write_text("rect { fill: #FF0000; }", encoding="utf-8")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
        width="30" height="10">
      <style>@import url({css.as_uri()});</style>
      <script>document.documentElement.setAttribute('width', '500');</script>
      <image x="0" y="0" width="10" height="10" href="{red}"/>
      <image x="10" y="0" width="10" height="10" xlink:href="{red.as_uri()}"/>
      <rect x="20" width="10" height="10" style="fill: url({red.as_uri()})"/>
    </svg>"""
    # resvg itself would load the file: the test shows the cleaning keeps it out.
    unclean = image(resvg_py.svg_to_bytes(svg_string=svg, skip_system_fonts=True))
    assert pixel(unclean, 5, 5) == RED
    picture = image(to_png(svg, PngOptions(scale=1)))
    assert picture.size == (30, 10)
    assert pixel(picture, 5, 5)[3] == 0
    assert pixel(picture, 15, 5)[3] == 0
    assert pixel(picture, 25, 5)[3] == 0


def test_links_inside_the_svg_and_data_uris_still_work() -> None:
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), (0, 255, 0)).save(buffer, "PNG")
    data = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
        width="20" height="10">
      <defs><linearGradient id="g"><stop offset="0" stop-color="#0000FF"/>
        <stop offset="1" stop-color="#0000FF"/></linearGradient></defs>
      <rect width="10" height="10" style="fill: url(#g)"/>
      <image x="10" y="0" width="10" height="10" xlink:href="{data}"/>
    </svg>"""
    picture = image(to_png(svg, PngOptions(scale=1)))
    assert pixel(picture, 5, 5) == BLUE
    assert pixel(picture, 15, 5) == (0, 255, 0, 255)


def test_the_tooltips_of_a_drawing_are_not_in_its_png() -> None:
    """The tooltips of ``to_svg`` show only on ``:hover``, which a PNG never has."""
    bar = DrawingShape(
        DrawingPath.rectangle(40, 60, 20, 40),
        colors.PTA_BLUE,
        None,
        0,
        kind=ShapeKind.RECTANGLE,
        hover=DrawingHover("Ein langer Tooltip", 50, 60),
    )
    point = DrawingHotspot(20, 50, 10, dot=colors.SIGNAL_RED, hover=DrawingHover("x", 20, 50))
    with_tips = image(to_png(to_svg(Drawing(100, 100, (bar, point)))))
    without = image(to_png(to_svg(Drawing(100, 100, (bar,)))))
    assert with_tips.size == (200, 200)
    assert with_tips.getchannel("A").getbbox() == (80, 120, 120, 200)  # only the bar
    assert with_tips.tobytes() == without.tobytes()


def test_a_drawing_becomes_a_png_at_twice_its_size() -> None:
    """In place of DocLibs ``ChartPngTests``: the finance charts (E06-S02) are not there yet."""
    drawing = Drawing(
        120,
        60,
        tuple(
            DrawingShape(DrawingPath.rectangle(10 + 30 * i, 50 - 10 * i, 20, 10 * i), c, None, 0)
            for i, c in enumerate(colors.ACCENTS[:3], start=1)
        ),
    )
    picture = image(to_png(to_svg(drawing)))
    assert picture.size == (240, 120)
    assert ink_width(to_png(to_svg(drawing))) > picture.size[0] / 2
