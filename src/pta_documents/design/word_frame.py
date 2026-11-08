"""The page frame of the PTA Word templates: header, footer and the first page, read from the
template (``word/header*.xml``, ``word/footer*.xml``, the ``w:sectPr`` of the body).

The PDF generator (E05-S03) draws what Word shows around the text of every page, at the place
and in the format of the template: the logo and the gradient rules (anchored drawings,
``wp:anchor``), the header table with title and subtitle, the footer table with company, date
and page number. Nothing of it is a second table of values in code; a template that changes
moves the PDF with it. Positions are in points from the top left of the page.

What the templates show (Designanalyse, *Kopf- und Fußzeile*): logo portrait 2.22 × 1.28 cm,
1.09 cm from the top, right on the type area; landscape 3.01 × 1.73 cm at 24.49/1.05 cm; rule
portrait 16.6 cm at 2.20/2.80 cm and over the footer at 28.20 cm; landscape 25.3 cm at 3.40 cm and
19.20 cm; the first page of ``quer`` has its rule at 6.00 cm. Rules run from ``accent1`` over
``accent3`` (53 %) to ``accent3`` without opacity, as wide as the theme's line style.
"""

from __future__ import annotations

import io
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Final

from lxml import etree

from pta_documents.design import templates, word, word_styles
from pta_documents.design.variants import WordVariant
from pta_documents.design.word_styles import LineRule, PageSetup, ParagraphFormat, WordDesign

W: Final = word_styles.W
A: Final = word_styles.A
R: Final = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP: Final = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
PIC: Final = "http://schemas.openxmlformats.org/drawingml/2006/picture"
MC: Final = "http://schemas.openxmlformats.org/markup-compatibility/2006"
PACKAGE_RELS: Final = "http://schemas.openxmlformats.org/package/2006/relationships"
EMU_PER_POINT: Final = 12700
GRADIENT_POSITION_SCALE: Final = 100000
"""``a:gs pos`` and ``a:alpha val`` are in thousandths of a percent."""


def _w(name: str) -> str:
    return f"{{{W}}}{name}"


def _a(name: str) -> str:
    return f"{{{A}}}{name}"


def _wp(name: str) -> str:
    return f"{{{WP}}}{name}"


class Alignment(StrEnum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class VerticalAlignment(StrEnum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


class FrameField(StrEnum):
    """What a paragraph of a header or footer shows; the placeholder text of the template says
    which (``word.TITLE_PLACEHOLDER`` …)."""

    TITLE = "title"
    SUBTITLE = "subtitle"
    COMPANY = "company"
    AS_OF = "as-of"
    """„Stand: TT.MM.JJJJ"."""
    PAGE = "page"
    """„Seite n | m" (the fields ``PAGE`` and ``NUMPAGES``)."""
    NONE = "none"
    """An empty paragraph: it only takes room."""


@dataclass(frozen=True)
class Box:
    """A rectangle on the page, in points from the top left."""

    x_pt: float
    y_pt: float
    width_pt: float
    height_pt: float


@dataclass(frozen=True)
class GradientStop:
    position: float
    """0 … 1 along the rule."""
    color: str
    """RGB hex."""
    alpha: float = 1.0


@dataclass(frozen=True)
class FrameRule:
    """A horizontal rule with a gradient (``prstGeom line``)."""

    x_pt: float
    y_pt: float
    width_pt: float
    stroke_pt: float
    stops: tuple[GradientStop, ...]


@dataclass(frozen=True)
class FrameParagraph:
    """A paragraph of a header or footer: its style with the direct formatting of the paragraph
    and of its first run with text (bold, colour, size)."""

    format: ParagraphFormat
    field: FrameField
    align: Alignment = Alignment.LEFT

    def height(self, natural: float) -> float:
        """The room the paragraph takes for a font whose single line is ``natural`` × size."""
        fmt = self.format
        return fmt.space_before_pt + fmt.leading(natural) + fmt.space_after_pt


@dataclass(frozen=True)
class FrameCell:
    width_pt: float
    paragraphs: tuple[FrameParagraph, ...]
    v_align: VerticalAlignment = VerticalAlignment.TOP


@dataclass(frozen=True)
class FrameRow:
    cells: tuple[FrameCell, ...]
    height_pt: float | None = None
    """``w:trHeight``; None: as high as the content."""
    height_rule: LineRule = LineRule.AT_LEAST


@dataclass(frozen=True)
class FrameTable:
    """A table without rules in a header or footer (title and subtitle; company, date, page)."""

    x_pt: float
    rows: tuple[FrameRow, ...]

    @property
    def width_pt(self) -> float:
        return max((sum(c.width_pt for c in row.cells) for row in self.rows), default=0.0)


type FrameBlock = FrameTable | FrameParagraph


@dataclass(frozen=True)
class Band:
    """One header or footer part: the text blocks in their order, the pictures (the logo) and
    the rules anchored to the page."""

    blocks: tuple[FrameBlock, ...] = ()
    pictures: tuple[Box, ...] = ()
    rules: tuple[FrameRule, ...] = ()


@dataclass(frozen=True)
class PageKind:
    """Header and footer of a kind of page (the first, every other)."""

    header: Band
    footer: Band


@dataclass(frozen=True)
class PageFrame:
    """The frame of a template variant."""

    page: PageSetup
    other: PageKind
    """Every page but the first of a template with a different first page."""
    first: PageKind | None = None
    """The first page (``w:titlePg``): the cover of ``hoch`` and ``quer``."""

    def kind(self, page_number: int) -> PageKind:
        """The header and footer of page ``page_number`` (1-based)."""
        if page_number == 1 and self.first is not None:
            return self.first
        return self.other


def read(variant: WordVariant, design: WordDesign | None = None) -> PageFrame:
    """The frame of the embedded template of ``variant``; ``design`` is its
    ``word_styles.read(variant)`` if the caller has it already."""
    design = design or word_styles.read(variant)
    with zipfile.ZipFile(io.BytesIO(templates.word_template(variant))) as archive:
        document = etree.fromstring(archive.read("word/document.xml"))
        relationships = etree.fromstring(archive.read("word/_rels/document.xml.rels"))
        targets = {
            str(r.get("Id")): "word/" + str(r.get("Target"))
            for r in relationships.iter(f"{{{PACKAGE_RELS}}}Relationship")
        }
        sections = list(document.iter(_w("sectPr")))
        if not sections:
            raise ValueError("the template has no section properties")
        section = sections[-1]
        reader = _BandReader(design, _line_widths(archive))

        def band(kind: str, reference: str) -> Band:
            for ref in section.iter(_w(reference)):
                if ref.get(_w("type"), "default") == kind:
                    part = targets[str(ref.get(f"{{{R}}}id"))]
                    return reader.band(etree.fromstring(archive.read(part)))
            return Band()

        other = PageKind(band("default", "headerReference"), band("default", "footerReference"))
        first = None
        if section.find(_w("titlePg")) is not None:
            first = PageKind(band("first", "headerReference"), band("first", "footerReference"))
    return PageFrame(design.page, other, first)


def header_top(frame: PageFrame) -> float:
    """Where the header starts: the header distance of the section."""
    return frame.page.header_pt


def footer_bottom(frame: PageFrame) -> float:
    """Where the footer ends, from the top of the page: the footer distance above the bottom."""
    return frame.page.height_pt - frame.page.footer_pt


def block_height(block: FrameBlock, natural: float) -> float:
    """The room a block of a header or footer takes, as Word lays it out."""
    if isinstance(block, FrameParagraph):
        return block.height(natural)
    return sum(row_height(row, natural) for row in block.rows)


def row_height(row: FrameRow, natural: float) -> float:
    content = max(
        (sum(p.height(natural) for p in cell.paragraphs) for cell in row.cells), default=0.0
    )
    if row.height_pt is None:
        return content
    if row.height_rule is LineRule.EXACT:
        return row.height_pt
    return max(row.height_pt, content)


def band_height(band: Band, natural: float) -> float:
    return sum(block_height(b, natural) for b in band.blocks)


def body_top(frame: PageFrame, page_number: int, natural: float) -> float:
    """Where the text of page ``page_number`` starts: the top margin, or lower when the header
    reaches below it (Word moves the text down then — the cover of ``hoch`` and ``quer`` uses an
    empty header paragraph with a large space after to place the title)."""
    header = frame.kind(page_number).header
    return max(frame.page.top_pt, header_top(frame) + band_height(header, natural))


class _BandReader:
    def __init__(self, design: WordDesign, line_widths: tuple[float, ...]) -> None:
        self.design = design
        self.line_widths = line_widths

    def band(self, root: etree._Element) -> Band:
        blocks: list[FrameBlock] = []
        for child in root:
            if child.tag == _w("tbl"):
                blocks.append(self.table(child))
            elif child.tag == _w("p"):
                blocks.append(self.paragraph(child))
        pictures: list[Box] = []
        rules: list[FrameRule] = []
        for anchor in root.iter(_wp("anchor")):
            if any(a.tag == f"{{{MC}}}Fallback" for a in anchor.iterancestors()):
                continue
            box = self.box(anchor)
            if anchor.find(f".//{{{PIC}}}pic") is not None:
                pictures.append(box)
                continue
            geometry = anchor.find(f".//{_a('prstGeom')}")
            if geometry is not None and geometry.get("prst") == "line":
                rules.append(self.rule(anchor, box))
        return Band(tuple(blocks), tuple(pictures), tuple(rules))

    def table(self, table: etree._Element) -> FrameTable:
        page = self.design.page
        indent = table.find(f"{_w('tblPr')}/{_w('tblInd')}")
        x = page.left_pt + (_twips(indent, "w") or 0.0)
        rows: list[FrameRow] = []
        for tr in table.iterfind(_w("tr")):
            cells: list[FrameCell] = []
            for tc in tr.iterfind(_w("tc")):
                width = tc.find(f"{_w('tcPr')}/{_w('tcW')}")
                v_align = tc.find(f"{_w('tcPr')}/{_w('vAlign')}")
                cells.append(
                    FrameCell(
                        width_pt=_twips(width, "w") or 0.0,
                        paragraphs=tuple(self.paragraph(p) for p in tc.iterfind(_w("p"))),
                        v_align=VerticalAlignment(
                            str(v_align.get(_w("val"))) if v_align is not None else "top"
                        ),
                    )
                )
            height = tr.find(f"{_w('trPr')}/{_w('trHeight')}")
            rows.append(
                FrameRow(
                    tuple(cells),
                    _twips(height, "val"),
                    LineRule(str(height.get(_w("hRule"), "atLeast")))
                    if height is not None
                    else LineRule.AT_LEAST,
                )
            )
        return FrameTable(x, tuple(rows))

    def paragraph(self, paragraph: etree._Element) -> FrameParagraph:
        p_pr = paragraph.find(_w("pPr"))
        style_id = None
        if p_pr is not None and (style := p_pr.find(_w("pStyle"))) is not None:
            style_id = str(style.get(_w("val")))
        name = self.design.paragraph_ids.get(style_id or "", word.STYLES.normal)
        fmt = self.design.paragraph(name)
        if p_pr is not None and (spacing := p_pr.find(_w("spacing"))) is not None:
            before = _twips(spacing, "before")
            after = _twips(spacing, "after")
            line = _twips(spacing, "line")
            fmt = replace(
                fmt,
                space_before_pt=fmt.space_before_pt if before is None else before,
                space_after_pt=fmt.space_after_pt if after is None else after,
                line_pt=fmt.line_pt if line is None else line,
                line_rule=fmt.line_rule
                if line is None
                else LineRule(str(spacing.get(_w("lineRule"), "auto"))),
            )
        text = _text(paragraph)
        run = next((r for r in paragraph.iter(_w("r")) if r.find(_w("t")) is not None), None)
        r_pr = run.find(_w("rPr")) if run is not None else None
        if r_pr is not None:
            size = r_pr.find(_w("sz"))
            bold = word_styles.is_on(r_pr.find(_w("b")))
            fmt = replace(
                fmt,
                size_pt=fmt.size_pt if size is None else int(str(size.get(_w("val")))) / 2,
                bold=fmt.bold if bold is None else bold,
                color=word_styles.color_of(r_pr.find(_w("color")), self.design.theme)
                if r_pr.find(_w("color")) is not None
                else fmt.color,
            )
        jc = p_pr.find(_w("jc")) if p_pr is not None else None
        return FrameParagraph(fmt, _field(paragraph, text), _alignment(jc))

    def box(self, anchor: etree._Element) -> Box:
        page = self.design.page
        extent = anchor.find(_wp("extent"))
        if extent is None:
            raise ValueError("an anchored drawing of the template has no extent")
        width = int(str(extent.get("cx"))) / EMU_PER_POINT
        height = int(str(extent.get("cy"))) / EMU_PER_POINT
        horizontal = anchor.find(_wp("positionH"))
        vertical = anchor.find(_wp("positionV"))
        if horizontal is None or vertical is None:
            raise ValueError("an anchored drawing of the template has no position")
        x = _position(horizontal, width, page.width_pt, page.left_pt, page.width_pt - page.right_pt)
        y = _position(
            vertical, height, page.height_pt, page.top_pt, page.height_pt - page.bottom_pt
        )
        return Box(x, y, width, height)

    def rule(self, anchor: etree._Element, box: Box) -> FrameRule:
        line = anchor.find(f".//{_a('ln')}")
        stroke: float | None = None
        if line is not None and line.get("w") is not None:
            stroke = int(str(line.get("w"))) / EMU_PER_POINT
        if stroke is None:
            reference = anchor.find(f".//{_a('lnRef')}")
            index = int(str(reference.get("idx"))) if reference is not None else 0
            if not 1 <= index <= len(self.line_widths):
                raise ValueError(f"the template's rule refers to line style {index}")
            stroke = self.line_widths[index - 1]
        stops: list[GradientStop] = []
        gradient = line.find(_a("gradFill")) if line is not None else None
        if gradient is None:
            raise ValueError("a rule of the template has no gradient")
        for stop in gradient.iter(_a("gs")):
            scheme = stop.find(_a("schemeClr"))
            rgb = stop.find(_a("srgbClr"))
            color_element = scheme if scheme is not None else rgb
            if color_element is None:
                raise ValueError("a gradient stop of the template has no colour")
            value = str(color_element.get("val"))
            alpha = color_element.find(_a("alpha"))
            stops.append(
                GradientStop(
                    position=int(str(stop.get("pos"))) / GRADIENT_POSITION_SCALE,
                    color=self.design.theme[value] if scheme is not None else value.upper(),
                    alpha=int(str(alpha.get("val"))) / GRADIENT_POSITION_SCALE
                    if alpha is not None
                    else 1.0,
                )
            )
        return FrameRule(box.x_pt, box.y_pt, box.width_pt, stroke, tuple(stops))


def _line_widths(archive: zipfile.ZipFile) -> tuple[float, ...]:
    """The widths of the theme's line styles (``a:lnStyleLst``), for ``a:lnRef idx``."""
    theme = etree.fromstring(archive.read("word/theme/theme1.xml"))
    styles = theme.find(f".//{_a('lnStyleLst')}")
    if styles is None:
        return ()
    return tuple(int(str(ln.get("w", "0"))) / EMU_PER_POINT for ln in styles.iterfind(_a("ln")))


def _position(
    position: etree._Element, size: float, page: float, margin_start: float, margin_end: float
) -> float:
    relative = str(position.get("relativeFrom"))
    match relative:
        case "page":
            start, end = 0.0, page
        case "margin":
            start, end = margin_start, margin_end
        case _:
            raise ValueError(f"anchored drawings relative to {relative!r} are not supported")
    offset = position.find(_wp("posOffset"))
    if offset is not None:
        return start + int(str(offset.text)) / EMU_PER_POINT
    align = position.find(_wp("align"))
    match align.text if align is not None else None:
        case "left" | "top" | "inside":
            return start
        case "right" | "bottom" | "outside":
            return end - size
        case "center":
            return start + (end - start - size) / 2
        case other:
            raise ValueError(f"unsupported alignment {other!r} of an anchored drawing")


def _text(paragraph: etree._Element) -> str:
    return "".join(t.text or "" for t in paragraph.iter(_w("t")))


_ALIGNMENTS: Final[Mapping[str, Alignment]] = {
    "center": Alignment.CENTER,
    "right": Alignment.RIGHT,
    "end": Alignment.RIGHT,
}


def _alignment(jc: etree._Element | None) -> Alignment:
    if jc is None:
        return Alignment.LEFT
    return _ALIGNMENTS.get(str(jc.get(_w("val"))), Alignment.LEFT)


def _field(paragraph: etree._Element, text: str) -> FrameField:
    instructions = " ".join(i.text or "" for i in paragraph.iter(_w("instrText"))).split()
    if word.SUBTITLE_PLACEHOLDER in text or "Untertitel" in instructions:
        return FrameField.SUBTITLE
    if word.TITLE_PLACEHOLDER in text or "Titel" in instructions:
        return FrameField.TITLE
    if word.COMPANY_PLACEHOLDER in " ".join(text.split()):
        return FrameField.COMPANY
    if text.strip().startswith(word.AS_OF_LABEL):
        return FrameField.AS_OF
    if "PAGE" in instructions:
        return FrameField.PAGE
    return FrameField.NONE


def _twips(element: etree._Element | None, attribute: str) -> float | None:
    if element is None:
        return None
    value = element.get(_w(attribute))
    return None if value is None else int(value) / word_styles.TWIPS_PER_POINT
