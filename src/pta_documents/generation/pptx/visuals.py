"""Tables, code boxes, picture rows and free text boxes in the PTA style."""

from __future__ import annotations

import copy
import io
import re
from collections.abc import Callable
from dataclasses import replace
from typing import Any, Final

from lxml import etree
from PIL import Image as PillowImage
from pptx.enum.shapes import MSO_SHAPE
from pptx.opc.package import Part
from pptx.opc.packuri import PackURI
from pptx.slide import Slide as PptxSlide
from pptx.util import Emu

from pta_documents.design import colors
from pta_documents.design import slides as design
from pta_documents.drawing import harvey
from pta_documents.generation.common import svg_blip
from pta_documents.generation.common.code_highlight import CodeLine, CodeSpan
from pta_documents.generation.pptx import drawing, fitting
from pta_documents.generation.pptx.model import Align, Code, Image, Run, Table

A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
NUMBER: Final = re.compile(r"^[+\-−–]?[\d.,'\s]+\s?(%|€|\$|£|k|m|mio\.?|mrd\.?|T€)?$", re.I)

RunWriter = Callable[[PptxSlide, Run, int | None, str | None], etree._Element]


def a(name: str) -> str:
    return f"{{{A}}}{name}"


def _solid(parent: etree._Element, color: str) -> etree._Element:
    fill = etree.SubElement(parent, a("solidFill"))
    etree.SubElement(fill, a("srgbClr")).set("val", color)
    return fill


def _line(parent: etree._Element, tag: str, color: str | None, width_pt: float) -> None:
    line = etree.SubElement(parent, a(tag))
    if color is None:
        line.set("w", "0")
        etree.SubElement(line, a("noFill"))
        return
    line.set("w", str(round(width_pt * fitting.EMU_PER_POINT)))
    line.set("cmpd", "sng")
    _solid(line, color)


def column_alignments(table: Table) -> list[Align]:
    """Markdown alignment, else numbers right and everything else left (PTA sample table)."""
    columns = len(table.alignments) or max(len(r) for r in table.rows)
    first = 1 if table.has_header else 0
    result: list[Align] = []
    for c in range(columns):
        given = table.alignments[c] if c < len(table.alignments) else Align.DEFAULT
        if given is not Align.DEFAULT:
            result.append(given)
            continue
        values = [
            "".join(r.text for r in row[c]).strip()
            for row in table.rows[first:]
            if c < len(row) and "".join(r.text for r in row[c]).strip()
        ]
        numeric = bool(values) and all(NUMBER.match(v) for v in values)
        result.append(Align.RIGHT if numeric and c > 0 else Align.LEFT)
    return result


def draw_table(
    slide: PptxSlide,
    table: Table,
    layout: fitting.TableLayout,
    left: int,
    top: int,
    run_writer: RunWriter,
    lang: str,
    dark: bool = False,
) -> int:
    """Draw the table; returns its height. A highlighted row is on the PTA yellow; on a dark
    slide the body rows are white."""
    t = design.TABLE
    row_color = colors.WHITE if dark else t.row_color
    closing_rule = colors.WHITE if dark else t.closing_rule_color
    columns = len(layout.widths)
    title_rows = 1 if table.title else 0
    frame = slide.shapes.add_table(
        len(table.rows) + title_rows,
        columns,
        Emu(left),
        Emu(top),
        Emu(sum(layout.widths)),
        Emu(layout.height),
    )
    shape: Any = frame
    graphic_table = shape.table
    tbl = graphic_table._tbl
    tbl_pr = tbl.tblPr
    tbl_pr.set("firstRow", "1" if table.has_header else "0")
    tbl_pr.set("bandRow", "0")
    for c, width in enumerate(layout.widths):
        graphic_table.columns[c].width = Emu(width)
    for r, height in enumerate(layout.heights):
        graphic_table.rows[r].height = Emu(height)
    alignments = column_alignments(table)

    if table.title:
        first = graphic_table.cell(0, 0)
        if columns > 1:
            first.merge(graphic_table.cell(0, columns - 1))
        _cell(
            first,
            [replace(r, bold=True) for r in table.title],
            t.title_size_pt,
            t.title_color,
            "+mj-lt",
            Align.LEFT,
            None,
            None,
            slide,
            run_writer,
            lang,
            first_column=True,
        )

    data_rows = len(table.rows) - (1 if table.has_header else 0)
    for r, row in enumerate(table.rows):
        header = table.has_header and r == 0
        body_index = r - (1 if table.has_header else 0)
        last = not header and body_index == data_rows - 1
        highlighted = not header and table.is_highlighted(r)
        for c in range(columns):
            cell = graphic_table.cell(r + title_rows, c)
            runs = list(row[c]) if c < len(row) else []
            align = Align.CENTER if any(run.harvey is not None for run in runs) else alignments[c]
            if header:
                _cell(
                    cell,
                    runs,
                    layout.header_pt,
                    t.header_color,
                    "+mj-lt",
                    alignments[c],
                    t.header_fill,
                    None,
                    slide,
                    run_writer,
                    lang,
                    first_column=c == 0,
                )
            else:
                rule = closing_rule if last else t.rule_color
                _cell(
                    cell,
                    runs,
                    layout.row_pt,
                    t.row_color if highlighted else row_color,
                    None,
                    align,
                    design.FLOW.highlight if highlighted else None,
                    rule,
                    slide,
                    run_writer,
                    lang,
                    first_column=c == 0,
                )
            if len(runs) == 1 and runs[0].harvey is not None:
                x = left + sum(layout.widths[:c]) + layout.widths[c] // 2
                y = (
                    top
                    + sum(layout.heights[: r + title_rows])
                    + layout.heights[r + title_rows] // 2
                )
                harvey_ball(slide, runs[0].harvey, x, y, lang)
    return layout.height


HARVEY_NAME: Final = "harvey"
"""The start of the name of a Harvey ball's group (``harvey-3``); the PPTX converter reads it
back as ``[3/4]``."""


def harvey_ball(slide: PptxSlide, quarters: int, x: int, y: int, lang: str) -> None:
    """A Harvey ball (E15-S02) as a group of shapes centred on (``x``, ``y``) EMU, over a table
    cell (cells hold no shapes)."""
    ball = harvey.ball(quarters)
    size = round(ball.width * drawing.EMU_PER_PIXEL)
    alt = f"{quarters}/{harvey.QUARTERS}"
    name = f"{HARVEY_NAME}-{quarters}"
    drawing.place(slide, ball, x - size // 2, y - size // 2, size, size, alt, lang, name)


def _cell(
    cell: Any,
    runs: list[Run],
    size_pt: float,
    color: str,
    font: str | None,
    align: Align,
    fill: str | None,
    bottom_rule: str | None,
    slide: PptxSlide,
    run_writer: RunWriter,
    lang: str,
    first_column: bool,
) -> None:
    tc = cell._tc
    body = tc.txBody
    for old in body.findall(a("p")):
        body.remove(old)
    paragraph = etree.SubElement(body, a("p"))
    p_pr = etree.SubElement(paragraph, a("pPr"))
    p_pr.set("algn", "r" if align is Align.RIGHT else "ctr" if align is Align.CENTER else "l")
    size = round(size_pt * 100)
    for run in runs:
        if run.harvey is not None:
            continue  # drawn over the cell (harvey_ball)
        if run.is_break:
            etree.SubElement(etree.SubElement(paragraph, a("br")), a("rPr")).set("lang", lang)
            continue
        element = run_writer(slide, run, size, color)
        r_pr = element.find(a("rPr"))
        assert r_pr is not None
        if font and r_pr.find(a("latin")) is None:
            # The font unless the run set one, before a hyperlink (schema order).
            link = r_pr.find(a("hlinkClick"))
            latin = etree.Element(a("latin"), typeface=font)
            if link is None:
                r_pr.append(latin)
            else:
                link.addprevious(latin)
        paragraph.append(element)
    end = etree.SubElement(paragraph, a("endParaRPr"))
    end.set("lang", lang)
    end.set("sz", str(size))

    tc_pr = tc.get_or_add_tcPr()
    for child in list(tc_pr):
        tc_pr.remove(child)
    tc_pr.set("anchor", "ctr")
    if first_column:
        tc_pr.set("marL", "0")
    width = design.TABLE.rule_width_pt
    _line(tc_pr, "lnL", None, width)
    _line(tc_pr, "lnR", None, width)
    _line(tc_pr, "lnT", None, width)
    _line(tc_pr, "lnB", bottom_rule, width)
    if fill is None:
        etree.SubElement(tc_pr, a("noFill"))
    else:
        _solid(tc_pr, fill)


def code_runs(
    paragraph: etree._Element, line: str, spans: CodeLine | None, size_pt: float, lang: str
) -> None:
    """The runs of a line of code in Consolas: one in the text colour, or one per highlighted
    span in the PTA colours (E17-S02)."""
    parts = [CodeSpan(line)] if spans is None else list(spans)
    for span in parts:
        if not span.text:
            continue
        look = span.look
        run = etree.SubElement(paragraph, a("r"))
        r_pr = etree.SubElement(run, a("rPr"))
        r_pr.set("lang", lang)
        r_pr.set("sz", str(round(size_pt * 100)))
        if look.bold:
            r_pr.set("b", "1")
        if look.italic:
            r_pr.set("i", "1")
        r_pr.set("dirty", "0")
        _solid(r_pr, look.color or colors.TEXT_SLIDES)
        etree.SubElement(r_pr, a("latin")).set("typeface", design.CODE_FONT)
        etree.SubElement(r_pr, a("cs")).set("typeface", design.CODE_FONT)
        etree.SubElement(run, a("t")).text = span.text


def draw_code(
    slide: PptxSlide, code: Code, size_pt: float, left: int, top: int, width: int, lang: str
) -> int:
    height = fitting.code_height(len(code.lines), size_pt)
    shape: Any = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Emu(left), Emu(top), Emu(width), Emu(height)
    )
    element = shape._element
    style = element.find(f"{{{P}}}style")
    if style is not None:
        element.remove(style)
    sp_pr = element.spPr
    _solid(sp_pr, design.CODE_BACKGROUND)
    etree.SubElement(etree.SubElement(sp_pr, a("ln")), a("noFill"))
    body = element.txBody
    body_pr = body.find(a("bodyPr"))
    assert body_pr is not None
    for side in ("lIns", "rIns", "tIns", "bIns"):
        body_pr.set(side, str(fitting.CODE_PAD))
    body_pr.set("anchor", "t")
    body_pr.set("wrap", "none")
    for old in body.findall(a("p")):
        body.remove(old)
    for n, line in enumerate(code.lines):
        paragraph = etree.SubElement(body, a("p"))
        etree.SubElement(paragraph, a("pPr")).set("algn", "l")
        code_runs(paragraph, line, code.spans[n] if code.spans else None, size_pt, lang)
        end = etree.SubElement(paragraph, a("endParaRPr"))
        end.set("lang", lang)
        end.set("sz", str(round(size_pt * 100)))
    return height


def picture_size(image: Image) -> tuple[float, float]:
    """The natural size of ``image`` in pixels: of the original for a converted image."""
    if image.natural is not None:
        return image.natural
    with PillowImage.open(io.BytesIO(image.resource.content)) as picture:
        return picture.size


def attach_svg(picture: Any, image: Image) -> None:
    """The SVG of a converted SVG image beside its PNG (``asvg:svgBlip``); else nothing."""
    if image.svg is not None:
        part = picture.part
        svg_blip.attach(picture._element, part, image.svg, _svg_part(part))


def _svg_part(owner: Any) -> svg_blip.PartFactory:
    """Makes SVG parts in the package of ``owner`` (python-pptx: package before blob)."""

    def new_part(partname: str, blob: bytes) -> Part:
        return Part(PackURI(partname), svg_blip.CONTENT_TYPE, owner.package, blob)

    return new_part


EMU_PER_PIXEL: Final = 9525
"""A pixel at 96 dpi: the natural size of an image on a slide."""


def fit_picture(picture: Any, image: Image) -> None:
    """A picture a placeholder cropped to fill it, uncropped and fitted into the placeholder
    instead (``image.scale`` times as large at most), centred in it."""
    picture.crop_left = picture.crop_right = picture.crop_top = picture.crop_bottom = 0.0
    left, top = int(picture.left), int(picture.top)
    room_x, room_y = int(picture.width), int(picture.height)
    pixels_x, pixels_y = picture_size(image)
    factor = min(room_x / pixels_x, room_y / pixels_y) * min(image.scale, 1.0)
    width, height = int(pixels_x * factor), int(pixels_y * factor)
    picture.left = Emu(left + (room_x - width) // 2)
    picture.top = Emu(top + (room_y - height) // 2)
    picture.width = Emu(width)
    picture.height = Emu(height)


def draw_pictures(
    slide: PptxSlide | None, images: list[Image], left: int, top: int, width: int, height: int
) -> tuple[int, list[float]]:
    """Pictures side by side, each in an equal share of the width, aligned to the top left;
    without a slide only measured.

    Returns the height used and, per image, how many times its natural size it is shown at.
    """
    count = len(images)
    share = (width - design.PICTURE_GAP * (count - 1)) // count
    used = 0
    x = left
    factors: list[float] = []
    for image in images:
        pixels_x, pixels_y = picture_size(image)
        scale = min(share / pixels_x, height / pixels_y) * min(image.scale, 1.0)
        factors.append(scale / EMU_PER_PIXEL)
        w, h = int(pixels_x * scale), int(pixels_y * scale)
        if slide is not None:
            picture: Any = slide.shapes.add_picture(
                io.BytesIO(image.resource.content), Emu(x), Emu(top), Emu(w), Emu(h)
            )
            picture._element.nvPicPr.cNvPr.set("descr", image.alt)
            attach_svg(picture, image)
        x += share + design.PICTURE_GAP
        used = max(used, h)
    return used, factors


def text_box(slide: PptxSlide, left: int, top: int, width: int, height: int) -> etree._Element:
    """A text box with the master's body levels, so paragraphs look as in the placeholders."""
    shape: Any = slide.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(height))
    body = shape._element.txBody
    body_pr = body.find(a("bodyPr"))
    assert body_pr is not None
    for side in ("lIns", "rIns", "tIns", "bIns"):
        body_pr.set(side, "0")
    body_pr.set("wrap", "square")
    for child in list(body_pr):
        body_pr.remove(child)
    master: etree._Element = slide.slide_layout.slide_master._element
    levels = master.find(f"{{{P}}}txStyles/{{{P}}}bodyStyle")
    list_style = body.find(a("lstStyle"))
    if levels is not None and list_style is not None:
        for level in levels:
            if etree.QName(level).localname.startswith("lvl"):
                list_style.append(copy.deepcopy(level))
    return body
