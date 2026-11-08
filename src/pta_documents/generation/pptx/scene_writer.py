"""Scene slides (E09-S04): named shapes on the grid of ``Nur Titel``, which Morph moves.

Port of vt-tools-libs ``DeckWriter.WriteSceneSlide``/``SceneShape``. Every shape is named
``!!name`` — PowerPoint's Morph pairs shapes of the same ``!!`` name on two slides (``morph``
on the second, E09-S03) and moves, resizes, turns and recolours them. A box is a preset shape
(``rect``, ``roundRect`` with its corner as ``adj``, ``ellipse``), a line or arrow a ``line``
shape (``tailEnd`` triangle), an image a picture fitted into its box. Text is centred both ways
in Segoe UI Light (bold: Segoe UI); opacity is ``a:alpha`` on every colour, rotation ``rot``.
A shape with ``step=n`` appears on the n-th click of the slide (a fade, E09-S02).

The grid is ``scene.COLUMNS`` × ``scene.ROWS`` units of ``scene.UNIT_EMU`` from the top left of
the content area; the line widths, the corner and the text room are those of the still drawing
(``drawing.scene``) at ``scene.UNIT_EMU / PIXELS_PER_UNIT`` EMU a pixel.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any, Final

from lxml import etree
from pptx.slide import Slide as PptxSlide
from pptx.util import Emu

from pta_documents.design import colors
from pta_documents.design import slides as design
from pta_documents.drawing import scene as scene_drawing
from pta_documents.generation.common import scene_colors
from pta_documents.generation.common.scene import UNIT_EMU, SceneShape, ShapeKind
from pta_documents.generation.pptx import flow, visuals
from pta_documents.generation.pptx.model import Click, Image, SceneSlide

if TYPE_CHECKING:
    from pta_documents.generation.pptx.writer import DeckWriter

A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
MORPH_PREFIX: Final = "!!"
"""What a shape's name starts with so that Morph pairs it by name."""
EMU_PER_PIXEL: Final = UNIT_EMU / scene_drawing.PIXELS_PER_UNIT
BOX_LINE: Final = round(scene_drawing.BOX_LINE * EMU_PER_PIXEL)
LINE_WIDTH: Final = round(scene_drawing.LINE_WIDTH * EMU_PER_PIXEL)
CORNER: Final = round(scene_drawing.CORNER_RADIUS * EMU_PER_PIXEL)
TEXT_PADDING: Final = round(scene_drawing.TEXT_PADDING * EMU_PER_PIXEL)
FULL: Final = 100000
"""100 % in DrawingML (alpha, adjust values)."""
PILL_CORNER: Final = 50000
"""The ``adj`` of a ``roundRect`` whose corners are half its shorter side."""
DEGREE: Final = 60000
"""A degree in DrawingML angles."""
_PRESETS: Final = {
    ShapeKind.BOX: "rect",
    ShapeKind.TEXT: "rect",
    ShapeKind.ROUND: "roundRect",
    ShapeKind.PILL: "roundRect",
    ShapeKind.CIRCLE: "ellipse",
    ShapeKind.LINE: "line",
    ShapeKind.ARROW: "line",
}


def a(name: str) -> str:
    return f"{{{A}}}{name}"


def p(name: str) -> str:
    return f"{{{P}}}{name}"


def write_scene_slide(deck: DeckWriter, slide: SceneSlide) -> None:
    """The slide on ``Nur Titel`` with its title (and kicker), then the shapes in order."""
    target = flow.headed_slide(deck, slide, design.LAYOUTS.title_only, 0)
    images = dict(slide.images)
    for n, shape in enumerate(slide.scene.shapes):
        click = Click(shape.step) if shape.step > 0 else None
        with deck.at(target, click):
            image = images.get(n)
            if image is not None:
                _picture(target, shape, image)
            else:
                _shape(deck, target, shape, slide.dark)
    deck.finish(target, footer=True, color=colors.WHITE if slide.dark else None)


def box_of(shape: SceneShape) -> tuple[int, int, int, int]:
    """The shape's box on the slide in EMU (left, top, width, height), at least 1 wide and high."""
    x, y, w, h = shape.box
    area = design.CONTENT_AREA
    return (
        area.left + round(x * UNIT_EMU),
        area.top + round(y * UNIT_EMU),
        max(1, round(w * UNIT_EMU)),
        max(1, round(h * UNIT_EMU)),
    )


def _transform(parent: etree._Element, shape: SceneShape, box: tuple[int, int, int, int]) -> None:
    xfrm = etree.SubElement(parent, a("xfrm"))
    if shape.rotation:
        xfrm.set("rot", str(round(shape.rotation % 360 * DEGREE)))
    if shape.is_line and shape.width < 0:
        xfrm.set("flipH", "1")
    if shape.is_line and shape.height < 0:
        xfrm.set("flipV", "1")
    left, top, width, height = box
    etree.SubElement(xfrm, a("off"), x=str(left), y=str(top))
    etree.SubElement(xfrm, a("ext"), cx=str(width), cy=str(height))


def _alpha(shape: SceneShape) -> int:
    return round(shape.opacity * FULL)


def _solid(parent: etree._Element, color: str | None, alpha: int) -> None:
    """A solid fill of ``color`` (``a:noFill`` for None), with ``alpha`` below 100 %."""
    if color is None:
        etree.SubElement(parent, a("noFill"))
        return
    srgb = etree.SubElement(etree.SubElement(parent, a("solidFill")), a("srgbClr"), val=color)
    if alpha < FULL:
        etree.SubElement(srgb, a("alpha"), val=str(alpha))


def _shape(deck: DeckWriter, target: PptxSlide, shape: SceneShape, dark: bool) -> None:
    tree: Any = target.shapes._spTree
    box = box_of(shape)
    alpha = _alpha(shape)
    sp = etree.SubElement(tree, p("sp"))
    nv = etree.SubElement(sp, p("nvSpPr"))
    etree.SubElement(
        nv, p("cNvPr"), id=str(target.shapes._next_shape_id), name=MORPH_PREFIX + shape.name
    )
    etree.SubElement(nv, p("cNvSpPr"))
    etree.SubElement(nv, p("nvPr"))
    sp_pr = etree.SubElement(sp, p("spPr"))
    _transform(sp_pr, shape, box)
    geometry = etree.SubElement(sp_pr, a("prstGeom"), prst=_PRESETS[shape.kind])
    adjust = etree.SubElement(geometry, a("avLst"))
    if shape.kind in (ShapeKind.ROUND, ShapeKind.PILL):
        shorter = max(1, min(box[2], box[3]))
        corner = (
            PILL_CORNER
            if shape.kind is ShapeKind.PILL
            else min(PILL_CORNER, CORNER * FULL // shorter)
        )
        etree.SubElement(adjust, a("gd"), name="adj", fmla=f"val {corner}")
    soft = scene_colors.is_soft(shape)
    fill_hex = scene_colors.hex_of(scene_colors.fill(shape))
    if soft and fill_hex is not None:
        fill_hex = scene_colors.soft_fill(fill_hex)
    _solid(sp_pr, fill_hex, alpha)
    stroke = scene_colors.hex_of(scene_colors.stroke(shape))
    line = etree.SubElement(sp_pr, a("ln"))
    if stroke is not None:
        line.set("w", str(LINE_WIDTH if shape.is_line else BOX_LINE))
    _solid(line, stroke, alpha)
    if shape.kind is ShapeKind.ARROW:
        etree.SubElement(line, a("tailEnd"), type="triangle")
    if shape.is_line:
        return
    # Every shape but a line has a text body, so that PowerPoint builds it like its own.
    is_text = shape.kind is ShapeKind.TEXT
    padding = str(0 if is_text else TEXT_PADDING)
    body = etree.SubElement(sp, p("txBody"))
    body_pr = etree.SubElement(
        body, a("bodyPr"), wrap="square", lIns=padding, rIns=padding, tIns="0", bIns="0"
    )
    body_pr.set("anchor", "ctr")
    etree.SubElement(body_pr, a("noAutofit"))
    etree.SubElement(body, a("lstStyle"))
    paragraph = etree.SubElement(body, a("p"))
    p_pr = etree.SubElement(paragraph, a("pPr"), marL="0", indent="0")
    p_pr.set("algn", "l" if is_text else "ctr")
    etree.SubElement(p_pr, a("buNone"))
    size = str(round(shape.size * 100))
    if shape.text:
        run = etree.SubElement(paragraph, a("r"))
        r_pr = etree.SubElement(run, a("rPr"), lang=deck.lang, sz=size)
        if shape.bold:
            r_pr.set("b", "1")
        r_pr.set("dirty", "0")
        text_hex = scene_colors.hex_of(scene_colors.text(shape, soft, dark))
        if text_hex is not None:
            _solid(r_pr, text_hex, alpha)
        # PTA rule: emphasis in Segoe UI (the heading font), not in Segoe UI Light.
        font = "+mj-lt" if shape.bold else design.BODY_FONT
        etree.SubElement(r_pr, a("latin"), typeface=font)
        etree.SubElement(run, a("t")).text = shape.text
    etree.SubElement(paragraph, a("endParaRPr"), lang=deck.lang, sz=size)


def _picture(target: PptxSlide, shape: SceneShape, image: Image) -> None:
    """The picture fitted into the shape's box (decision 2026-11-07: never cropped), centred,
    named for Morph, with its alternative text, rotation and opacity."""
    left, top, width, height = box_of(shape)
    pixels_x, pixels_y = visuals.picture_size(image)
    fit = min(width / pixels_x, height / pixels_y)
    w, h = max(1, round(pixels_x * fit)), max(1, round(pixels_y * fit))
    picture: Any = target.shapes.add_picture(
        io.BytesIO(image.resource.content),
        Emu(left + (width - w) // 2),
        Emu(top + (height - h) // 2),
        Emu(w),
        Emu(h),
    )
    c_nv_pr = picture._element.nvPicPr.cNvPr
    c_nv_pr.set("name", MORPH_PREFIX + shape.name)
    c_nv_pr.set("descr", shape.text)
    visuals.attach_svg(picture, image)
    if shape.rotation:
        picture.rotation = shape.rotation % 360
    alpha = _alpha(shape)
    if alpha < FULL:
        blip = picture._element.find(f"{p('blipFill')}/{a('blip')}")
        if blip is not None:
            fix = etree.SubElement(blip, a("alphaModFix"), amt=str(alpha))
            blip.insert(0, fix)
