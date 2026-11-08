"""The logos converted from the EMF pictures of the templates (E01-S04)."""

from __future__ import annotations

import base64
import io
import struct
import zipfile
from pathlib import Path

import emf
import pytest
from lxml import etree
from PIL import Image

from pta_documents.design import colors, logos
from pta_documents.design.logos import Logo
from pta_documents.design.variants import WordVariant
from pta_documents.drawing import DrawingShape, to_svg
from pta_documents.drawing.svg_output import path_data
from tests.conftest import SOURCE_TEMPLATES

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
WP_FRAMES = (f"{{{WP}}}inline", f"{{{WP}}}anchor")
PR = "http://schemas.openxmlformats.org/package/2006/relationships"

SLIDES_SOURCE = "PTA-Powerpoint-Basisvorlage.potx"
LAYOUTS = {Logo.SLIDES: "Titelfolie mit Bild 01", Logo.SLIDES_PLAIN: "Abbschlussfolie"}
FILLS = {Logo.WORD: colors.PTA_BLUE, Logo.SLIDES: colors.WHITE, Logo.SLIDES_PLAIN: colors.WHITE}


def placed_emf(source: str, part: str) -> tuple[bytes, float]:
    """The EMF picture placed in ``part`` and the aspect ratio of its frame in the template."""
    with zipfile.ZipFile(SOURCE_TEMPLATES / source) as archive:
        directory, file = part.rsplit("/", 1)
        rels = etree.fromstring(archive.read(f"{directory}/_rels/{file}.rels"))
        targets = {
            str(rel.get("Id")): str(rel.get("Target")) for rel in rels.iterfind(f"{{{PR}}}*")
        }
        root = etree.fromstring(archive.read(part))
        for blip in root.iterfind(f".//{{{A}}}blip"):
            target = targets[str(blip.get(f"{{{R}}}embed"))]
            if not target.endswith(".emf"):
                continue
            data = archive.read(_join(directory, target))
            if part.startswith("word/"):
                drawing = next(a for a in blip.iterancestors() if a.tag in WP_FRAMES)
                extent = drawing.find(f"{{{WP}}}extent")
                assert extent is not None
            else:
                pic = next(a for a in blip.iterancestors() if a.tag == f"{{{P}}}pic")
                extent = pic.find(f".//{{{A}}}xfrm/{{{A}}}ext")
                assert extent is not None
            return data, int(str(extent.get("cx"))) / int(str(extent.get("cy")))
    raise AssertionError(f"no EMF in {source}:{part}")


def _join(directory: str, target: str) -> str:
    parts = directory.split("/")
    for piece in target.split("/"):
        if piece == "..":
            parts.pop()
        else:
            parts.append(piece)
    return "/".join(parts)


def layout_part(name: str) -> str:
    with zipfile.ZipFile(SOURCE_TEMPLATES / SLIDES_SOURCE) as archive:
        for part in sorted(archive.namelist()):
            if part.startswith("ppt/slideLayouts/") and part.endswith(".xml"):
                c_sld = etree.fromstring(archive.read(part)).find(f"{{{P}}}cSld")
                if c_sld is not None and c_sld.get("name") == name:
                    return part
    raise AssertionError(name)


def source(logo: Logo) -> tuple[bytes, float]:
    if logo is Logo.WORD:
        return placed_emf(WordVariant.PORTRAIT.source_file, "word/header1.xml")
    return placed_emf(SLIDES_SOURCE, layout_part(LAYOUTS[logo]))


def emf_frame_ratio(data: bytes) -> float:
    left, top, right, bottom = struct.unpack_from("<4i", data, 24)
    return (right - left) / (bottom - top)


@pytest.mark.parametrize("variant", list(WordVariant))
def test_all_word_templates_carry_the_same_logo(variant: WordVariant) -> None:
    with zipfile.ZipFile(SOURCE_TEMPLATES / variant.source_file) as archive:
        names = archive.namelist()
    headers = [
        n
        for n in names
        if n.startswith("word/header") and n.replace("word/", "word/_rels/") + ".rels" in names
    ]
    assert headers
    for header in headers:
        assert placed_emf(variant.source_file, header)[0] == source(Logo.WORD)[0]


@pytest.mark.parametrize("logo", list(Logo))
def test_svg_has_the_shape_of_the_template_logo(logo: Logo) -> None:
    data, template_ratio = source(logo)
    ratio = logos.aspect_ratio(logo)
    assert ratio == pytest.approx(emf_frame_ratio(data), rel=0.01)
    assert ratio == pytest.approx(template_ratio, rel=0.01)
    assert logos.size(logo) == (emf.read(data).width, emf.read(data).height)


@pytest.mark.parametrize("logo", list(Logo))
def test_fills_come_from_the_colour_module(logo: Logo) -> None:
    shapes = logos.shapes(logo)
    assert shapes
    assert {shape.fill for shape in shapes} == {FILLS[logo]}
    assert not any(shape.even_odd for shape in shapes)  # the EMFs fill WINDING


def test_slogan_only_on_the_title_slide_logo() -> None:
    assert len(logos.shapes(Logo.SLIDES)) > len(logos.shapes(Logo.SLIDES_PLAIN))
    assert len(logos.shapes(Logo.SLIDES_PLAIN)) == len(logos.shapes(Logo.WORD))


@pytest.mark.parametrize("logo", list(Logo))
def test_shapes_read_back_the_svg_paths(logo: Logo) -> None:
    root = etree.fromstring(logos.svg(logo))
    written = [str(path.get("d")) for path in root]
    read = [
        "".join(
            command + " ".join(emf.number(v) for v in values) for command, values in shape.segments
        )
        for shape in logos.shapes(logo)
    ]
    assert read == written
    first = logos.shapes(logo)[0].segments
    assert first[0][0] == "M" and first[-1] == ("Z", ())


@pytest.mark.parametrize("logo", list(Logo))
def test_drawing_has_the_vector_paths_of_the_svg(logo: Logo) -> None:
    """E01-S04 acceptance criterion 3, closed with E02-S03."""
    drawing = logos.drawing(logo)
    assert (drawing.width, drawing.height) == logos.size(logo)
    shapes = logos.shapes(logo)
    assert len(drawing.items) == len(shapes)
    for item, shape in zip(drawing.items, shapes, strict=True):
        assert isinstance(item, DrawingShape)
        assert (item.fill, item.stroke, item.even_odd) == (shape.fill, None, shape.even_odd)
        assert [type(s).__name__ for s in item.path.segments] == [
            SEGMENT_TYPES[command] for command, _ in shape.segments
        ]
        assert [c for s in item.path.segments for p in s.points for c in p] == [
            v for _, values in shape.segments for v in values
        ]
    root = etree.fromstring(to_svg(drawing).encode())
    written = [path.get("d") for path in root]
    assert written == [
        path_data(item.path) for item in drawing.items if isinstance(item, DrawingShape)
    ]


def test_drawing_scales_to_a_width() -> None:
    plain, scaled = logos.drawing(Logo.WORD), logos.drawing(Logo.WORD, width=100)
    assert scaled.width == pytest.approx(100)
    assert scaled.height == pytest.approx(100 / logos.aspect_ratio(Logo.WORD))
    first, second = plain.items[0], scaled.items[0]
    assert isinstance(first, DrawingShape) and isinstance(second, DrawingShape)
    factor = 100 / plain.width
    assert second.path.bounds == pytest.approx(tuple(v * factor for v in first.path.bounds))


SEGMENT_TYPES = {"M": "MoveTo", "L": "LineTo", "C": "CubicTo", "Z": "ClosePath"}


@pytest.mark.parametrize("logo", list(Logo))
def test_png_is_wide_and_transparent(logo: Logo) -> None:
    with Image.open(io.BytesIO(logos.png(logo))) as image:
        assert image.format == "PNG" and image.mode == "RGBA"
        width, height = image.size
        assert width == logos.PNG_WIDTH
        assert width / height == pytest.approx(logos.aspect_ratio(logo), rel=0.005)
        corner = image.getpixel((0, 0))
        assert isinstance(corner, tuple) and corner[3] == 0
        alpha = image.getchannel("A")
        assert alpha.getextrema() == (0, 255)


def test_unknown_records_stop_the_conversion() -> None:
    header = struct.pack("<II4i4i", 1, 88 - 0, 0, 0, 10, 10, 0, 0, 100, 100) + bytes(88 - 40)
    unknown = struct.pack("<II", 76, 8)  # EMR_BITBLT
    eof = struct.pack("<II", 14, 20) + bytes(12)
    with pytest.raises(emf.EmfError, match="record type 76"):
        emf.read(header + unknown + eof)
    assert emf.read(header + eof).shapes == ()


def test_parse_path_rejects_other_commands() -> None:
    with pytest.raises(ValueError, match="unexpected character"):
        logos.parse_path("M0 0Q1 1 2 2Z")
    with pytest.raises(ValueError, match="needs 6 numbers"):
        logos.parse_path("M0 0C1 1Z")
    assert logos.parse_path("M0 0L1.5 -2Z") == (("M", (0, 0)), ("L", (1.5, -2)), ("Z", ()))


def test_review_page(review_dir: Path) -> None:
    rows: list[str] = []
    for logo in Logo:
        svg = base64.b64encode(logos.svg(logo)).decode()
        png = base64.b64encode(logos.png(logo)).decode()
        cells = "".join(
            f'<td style="background:#{background};padding:16px">'
            f'<img src="data:image/{kind};base64,{data}" width="300"></td>'
            for background in (colors.WHITE, colors.DARK_BLUE)
            for kind, data in (("svg+xml", svg), ("png", png))
        )
        rows.append(f"<tr><th>{logo.stem}</th>{cells}</tr>")
    page = (
        "<!doctype html><meta charset=utf-8><title>PTA-Logos</title><table>"
        "<tr><th></th><th>SVG weiß</th><th>PNG weiß</th><th>SVG dunkelblau</th>"
        f"<th>PNG dunkelblau</th></tr>{''.join(rows)}</table>"
    )
    (review_dir / "logos.html").write_text(page, encoding="utf-8")
