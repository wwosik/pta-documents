"""Writes slides onto the PTA layouts of the template."""

from __future__ import annotations

import copy
import io
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Final

from lxml import etree
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.presentation import Presentation
from pptx.slide import Slide as PptxSlide
from pptx.slide import SlideLayout
from pptx.util import Emu

from pta_documents.design import colors, templates
from pta_documents.design import slides as design
from pta_documents.design.variants import GeneratedTexts, Language, SlidesVariant
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.result import NoteCodes, Notes
from pta_documents.generation.pptx import fitting, flow, visuals
from pta_documents.generation.pptx.model import (
    ChapterSlide,
    ClosingSlide,
    Code,
    ContentSlide,
    FlowSlide,
    Image,
    Images,
    Kind,
    LayoutSlide,
    Paragraph,
    Run,
    Slide,
    Table,
    TitleSlide,
    Visual,
    VisualSlide,
    plain_text,
)
from pta_documents.generation.pptx.options import PptxOptions

FORMAT: Final = DocumentFormat.PPTX
A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
R: Final = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
FOOTER_TYPES: Final = ("ftr", "sldNum")
MAX_ENLARGEMENT: Final = 2.0
"""Shown at more than this many times its natural size, an image gets an ``image-enlarged`` note."""
MAX_CROPPED: Final = 0.25
"""Losing more than this share of its area to a placeholder, an image gets ``image-cropped``."""


def a(name: str) -> str:
    return f"{{{A}}}{name}"


def p(name: str) -> str:
    return f"{{{P}}}{name}"


@dataclass(frozen=True)
class DeckInfo:
    title: str | None
    subtitle: str | None
    byline: str | None
    footer: str


class DeckWriter:
    def __init__(
        self,
        presentation: Presentation,
        options: PptxOptions,
        texts: GeneratedTexts,
        info: DeckInfo,
        notes: Notes | None = None,
    ) -> None:
        self.presentation = presentation
        self.notes = notes if notes is not None else Notes()
        self.options = options
        self.texts = texts
        self.info = info
        self.lang = "en-US" if options.language is Language.EN else "de-DE"
        self.layouts = {layout.name: layout for layout in presentation.slide_layouts}
        self.number = 0
        self.body_style = fitting.BodyStyle.read(presentation)

    # ------------------------------------------------------------------ entry

    def write(self, slides: Sequence[Slide]) -> None:
        for slide in slides:
            self.slide(slide)

    def slide(self, slide: Slide) -> None:
        match slide:
            case TitleSlide():
                self.title_slide(slide)
            case ChapterSlide():
                target = self.new_slide(slide.layout or design.LAYOUTS.chapter, slide)
                self.set_text(target, design.PLACEHOLDERS.chapter_number, f"{slide.number:02d}")
                self.set_title(target, slide.title)
                self.finish(target)
            case ClosingSlide():
                target = self.new_slide(slide.layout or design.LAYOUTS.closing, slide)
                self.set_title(target, slide.title)
                self.finish(target)
            case ContentSlide():
                self.content_slide(slide)
            case VisualSlide():
                self.visual_slide(slide)
            case LayoutSlide():
                self.layout_slide(slide)
            case FlowSlide():
                flow.write_flow_slide(self, slide)
            case _:
                raise TypeError(slide)

    # ------------------------------------------------------------------ slide kinds

    def title_slide(self, slide: TitleSlide) -> None:
        layout = slide.layout or design.TITLE_SLIDES[self.options.title_slide]
        target = self.new_slide(layout, slide)
        self.set_title(target, slide.title)
        ph = design.PLACEHOLDERS
        if self.info.subtitle:
            self.set_text(target, ph.subtitle, self.info.subtitle)
        elif slide.subtitle:
            self.set_paragraphs(target, ph.subtitle, [_flat(p) for p in slide.subtitle])
        if self.info.byline:
            self.set_text(target, ph.byline, self.info.byline)
        if (
            self.options.language is Language.EN
            and self.options.variant is SlidesVariant.BASIC
            and layout in design.TITLE_SLIDES.values()
        ):
            area = design.ENGLISH_LOGO_AREA
            target.shapes.add_picture(
                io.BytesIO(templates.read(templates.ENGLISH_LOGO)),
                Emu(area.left),
                Emu(area.top),
                Emu(area.width),
                Emu(area.height),
            )
        self.finish(target)

    def content_slide(self, slide: ContentSlide) -> None:
        area = design.CONTENT_AREA
        body = list(slide.body)
        scale = fitting.text_scale(self.body_style, body, area.width, area.height)
        if scale is not None or not body:
            self.text_slide(slide.title, body, scale or 1.0, slide)
            return
        smallest = self.body_style.scales()[-1]

        def fits(part: list[Paragraph]) -> bool:
            height = fitting.text_height(self.body_style, part, smallest, area.width)
            return height <= area.height

        parts = fitting.pack(fitting.groups(body), fits)
        self.note_split(slide, len(parts))
        for n, part in enumerate(parts):
            part_scale = fitting.text_scale(self.body_style, part, area.width, area.height)
            if part_scale is None:
                self.note_overfull(slide)
            self.text_slide(self.continued(slide.title, n), part, part_scale or smallest, slide)

    def text_slide(
        self, title: tuple[Run, ...], body: list[Paragraph], scale: float, slide: Slide
    ) -> None:
        target = self.new_slide(design.LAYOUTS.title_and_text, slide)
        self.set_title(target, title)
        if body:
            self.set_paragraphs(target, design.PLACEHOLDERS.body, body, scale)
        self.finish(target, footer=True)

    def visual_slide(self, slide: VisualSlide) -> None:
        visual = slide.visual
        text = [*slide.above, *slide.below]
        if isinstance(visual, Images) and len(visual.images) == 1:
            image = visual.images[0]
            layout = design.LAYOUTS.title_text_image if text else design.LAYOUTS.title_image
            target = self.new_slide(layout, slide)
            self.set_title(target, slide.title)
            if text:
                shape = self.placeholder(target, design.PLACEHOLDERS.body)
                width, height = int(shape.width), int(shape.height)
                scale = fitting.text_scale(self.body_style, text, width, height)
                if scale is None:
                    self.note_overfull(slide)
                self.set_paragraphs(
                    target,
                    design.PLACEHOLDERS.body,
                    text,
                    scale or self.body_style.scales()[-1],
                )
            self.fill_picture(target, design.PLACEHOLDERS.picture, image, slide)
            self.finish(target, footer=True)
            return
        self.visual_on_content_area(slide)

    def visual_on_content_area(self, slide: VisualSlide) -> None:
        """Table, code or a row of pictures in the content area, text above and below.

        What does not fit at the smallest size is split: table rows (header repeated), code
        lines, pictures beyond four; the text above goes on the first part, below on the last.
        """
        area = design.CONTENT_AREA
        above, below = list(slide.above), list(slide.below)
        above_height = self.text_block_height(above)
        below_height = self.text_block_height(below)
        room = area.height - (above_height + fitting.GAP if above else 0)
        room -= below_height + fitting.GAP if below else 0
        room_rest = area.height - (below_height + fitting.GAP if below else 0)
        visual = slide.visual
        parts: list[Visual] = []
        if isinstance(visual, Table):
            if fitting.fit_table(visual, area.width, room) is not None:
                parts = [visual]
            else:
                parts = list(fitting.split_table(visual, area.width, room, room_rest))
        elif isinstance(visual, Code):
            if fitting.fit_code(len(visual.lines), room) is not None:
                parts = [visual]
            else:
                first = fitting.code_lines_per_slide(room)
                rest = fitting.code_lines_per_slide(room_rest)
                lines = list(visual.lines)
                parts = [Code(tuple(lines[:first]))]
                for start in range(first, len(lines), rest):
                    parts.append(Code(tuple(lines[start : start + rest])))
        elif isinstance(visual, Images):
            per_row = design.MAX_PICTURES_PER_ROW
            parts = [
                Images(visual.images[i : i + per_row])
                for i in range(0, len(visual.images), per_row)
            ]
        self.note_split(slide, len(parts))
        for n, part in enumerate(parts):
            self.visual_part(
                slide,
                self.continued(slide.title, n),
                above if n == 0 else [],
                part,
                below if n == len(parts) - 1 else [],
            )

    def text_block_height(self, paragraphs: list[Paragraph]) -> int:
        if not paragraphs:
            return 0
        area = design.CONTENT_AREA
        scale = fitting.text_scale(self.body_style, paragraphs, area.width, area.height / 2)
        scale = scale or self.body_style.scales()[-1]
        return int(fitting.text_height(self.body_style, paragraphs, scale, area.width))

    def visual_part(
        self,
        slide: VisualSlide,
        title: tuple[Run, ...],
        above: list[Paragraph],
        visual: Visual,
        below: list[Paragraph],
    ) -> None:
        area = design.CONTENT_AREA
        layout = design.LAYOUTS.title_and_text if above else design.LAYOUTS.title_only
        target = self.new_slide(layout, slide)
        self.set_title(target, title)
        y = area.top
        if above:
            height = self.text_block_height(above)
            shape = self.placeholder(target, design.PLACEHOLDERS.body)
            shape.left, shape.top = Emu(area.left), Emu(y)
            shape.width, shape.height = Emu(area.width), Emu(height)
            scale = fitting.text_scale(self.body_style, above, area.width, height + 1)
            self.set_paragraphs(target, design.PLACEHOLDERS.body, above, scale or 1.0)
            y += height + fitting.GAP
        below_height = self.text_block_height(below)
        room = area.bottom - y - (below_height + fitting.GAP if below else 0)
        if isinstance(visual, Table):
            table_layout = fitting.fit_table(visual, area.width, room)
            if table_layout is None:
                self.note_overfull(slide)
                table_layout = fitting.table_layout(visual, area.width, *fitting.table_steps()[-1])
            used = visuals.draw_table(
                target, visual, table_layout, area.left, y, self.run_element, self.lang
            )
        elif isinstance(visual, Code):
            size = fitting.fit_code(len(visual.lines), room)
            if size is None:
                self.note_overfull(slide)
                size = fitting.CODE_SIZES[-1]
            used = visuals.draw_code(target, visual, size, area.left, y, area.width, self.lang)
        else:
            used, factors = visuals.draw_pictures(
                target, list(visual.images), area.left, y, area.width, room
            )
            for image, factor in zip(visual.images, factors, strict=True):
                self.note_enlarged(image, factor)
        y += used + fitting.GAP
        if below:
            body = visuals.text_box(target, area.left, y, area.width, below_height)
            self.write_paragraphs(target, body, below)
        self.finish(target, footer=True)

    def continued(self, title: tuple[Run, ...], index: int) -> tuple[Run, ...]:
        if index == 0:
            return title
        return (*title, Run(" " + self.texts.continued))

    def layout_slide(self, slide: LayoutSlide) -> None:
        target = self.new_slide(slide.layout, slide)
        self.set_title(target, slide.title)
        layout = self.layouts[slide.layout]
        decorative = _decorative(layout)
        bodies = [
            ph
            for ph in _placeholders(layout)
            if ph[1] in ("body", "obj")
            and ph[0] not in decorative
            and ph[0] not in (design.PLACEHOLDERS.title,)
        ]
        pictures = [ph for ph in _placeholders(layout) if ph[1] == "pic"]
        body_index = picture_index = 0
        for segment in slide.segments:
            paragraphs = [item for item in segment if isinstance(item, Paragraph)]
            visuals = [item for item in segment if not isinstance(item, Paragraph)]
            if paragraphs:
                if body_index >= len(bodies):
                    raise self.error(
                        f"The layout '{slide.layout}' has {len(bodies)} text placeholders; the "
                        "slide has more text parts (split at '---')",
                        slide,
                    )
                self.set_paragraphs(target, bodies[body_index][0], paragraphs)
                body_index += 1
            for visual in visuals:
                if isinstance(visual, Images) and picture_index + len(visual.images) <= len(
                    pictures
                ):
                    for image in visual.images:
                        self.fill_picture(target, pictures[picture_index][0], image, slide)
                        picture_index += 1
                else:
                    raise self.error(
                        f"The layout '{slide.layout}' has no place for this "
                        f"{type(visual).__name__.lower()}",
                        slide,
                    )
        self.finish(target, footer=True)

    # ------------------------------------------------------------------ slides and placeholders

    def error(self, reason: str, slide: Slide) -> DocumentConversionError:
        where = f" (line {slide.line})" if slide.line else ""
        return DocumentConversionError(FORMAT, f"{reason}{where}.")

    def new_slide(self, layout_name: str, slide: Slide) -> PptxSlide:
        layout = self.layouts.get(layout_name)
        if layout is None:
            valid = ", ".join(f"'{name}'" for name in self.layouts)
            raise self.error(
                f"The PTA template has no layout '{layout_name}'. Valid layouts: {valid}", slide
            )
        self.number += 1
        return self.presentation.slides.add_slide(layout)

    def placeholder(self, slide: PptxSlide, idx: int) -> Any:
        for shape in slide.placeholders:
            if shape.placeholder_format.idx == idx:
                return shape
        raise DocumentConversionError(
            FORMAT, f"The layout '{slide.slide_layout.name}' has no placeholder {idx}."
        )

    def set_title(self, slide: PptxSlide, runs: tuple[Run, ...], color: str | None = None) -> None:
        title: Any = slide.shapes.title
        if title is None:
            return
        paragraphs = [Paragraph(runs, Kind.SUBHEADLINE)]
        self.write_paragraphs(slide, title._element.txBody, paragraphs, color=color)

    def set_text(self, slide: PptxSlide, idx: int, text: str) -> None:
        self.set_paragraphs(slide, idx, [Paragraph((Run(text),), Kind.SUBHEADLINE)])

    def set_paragraphs(
        self, slide: PptxSlide, idx: int, paragraphs: list[Paragraph], scale: float = 1.0
    ) -> None:
        shape = self.placeholder(slide, idx)
        self.write_paragraphs(slide, shape._element.txBody, paragraphs, scale)

    def fill_picture(self, slide: PptxSlide, idx: int, image: Image, where: Slide) -> None:
        """The image in a picture placeholder, which crops it to fill the placeholder."""
        resource = image.resource
        placeholder = self.placeholder(slide, idx)
        picture = placeholder.insert_picture(io.BytesIO(resource.content))
        picture._element.nvPicPr.cNvPr.set("descr", image.alt)
        visible_x = 1.0 - float(picture.crop_left) - float(picture.crop_right)
        visible_y = 1.0 - float(picture.crop_top) - float(picture.crop_bottom)
        lost = 1.0 - visible_x * visible_y
        if lost > MAX_CROPPED:
            ratio = int(picture.width) / int(picture.height)
            other = (
                ""
                if slide.slide_layout.name == design.LAYOUTS.title_image
                else f", or put it alone on a slide, which gets the layout "
                f"'{design.LAYOUTS.title_image}'"
            )
            self.notes.add(
                NoteCodes.IMAGE_CROPPED,
                image.line,
                f"The image '{resource.path}' is cropped to its placeholder and loses "
                f"{round(lost * 100)} % of its area. Crop it yourself to the placeholder's "
                f"proportions (width : height = {ratio:.2f} : 1){other}.",
            )
        pixels_x, _ = visuals.picture_size(image)
        if visible_x > 0:
            self.note_enlarged(
                image, int(picture.width) / (pixels_x * visible_x * visuals.EMU_PER_PIXEL)
            )

    # ------------------------------------------------------------------ notes

    def note_split(self, slide: Slide, parts: int) -> None:
        if parts > 1:
            self.notes.add(
                NoteCodes.SLIDE_SPLIT,
                slide.line,
                f'The slide "{plain_text(slide.title)}" has too much for one slide and continues '
                f"on {parts - 1} more. Split it in the Markdown or shorten it.",
            )

    def note_overfull(self, slide: Slide) -> None:
        self.notes.add(
            NoteCodes.SLIDE_OVERFULL,
            slide.line,
            f'The slide "{plain_text(slide.title)}" does not fit even at the smallest text size '
            f"({design.MIN_FONT_PT:g} pt) and runs past its bottom. Shorten it, or split it into "
            "slides.",
        )

    def note_enlarged(self, image: Image, factor: float) -> None:
        if factor > MAX_ENLARGEMENT:
            self.notes.add(
                NoteCodes.IMAGE_ENLARGED,
                image.line,
                f"The image '{image.resource.path}' is shown at {factor:.1f} times its size and "
                "may look blurred. Use a larger image.",
            )

    def finish(self, slide: PptxSlide, footer: bool = False, color: str | None = None) -> None:
        """Remove placeholders left empty (decorative ones stay) and add footer and number."""
        decorative = _decorative(slide.slide_layout)
        for shape in list(slide.placeholders):
            fmt = shape.placeholder_format
            if fmt.idx in decorative:
                continue
            element = shape._element
            parent = element.getparent()
            if element.tag == p("sp") and not _text(element).strip() and parent is not None:
                parent.remove(element)
        if footer:
            self.add_footer(slide, color)

    def add_footer(self, slide: PptxSlide, color: str | None = None) -> None:
        tree = slide.shapes._spTree
        for layout_shape in slide.slide_layout.placeholders:
            ph = layout_shape._element.find(f"{p('nvSpPr')}/{p('nvPr')}/{p('ph')}")
            ph_type = ph.get("type") if ph is not None else None
            if ph_type not in FOOTER_TYPES:
                continue
            if ph_type == "sldNum" and not self.options.show_slide_numbers:
                continue
            shape = copy.deepcopy(layout_shape._element)
            c_nv_pr = shape.find(f"{p('nvSpPr')}/{p('cNvPr')}")
            assert c_nv_pr is not None
            c_nv_pr.set("id", str(slide.shapes._next_shape_id))
            for ext in c_nv_pr.findall(a("extLst")):
                c_nv_pr.remove(ext)
            sp_pr = shape.find(p("spPr"))
            if sp_pr is not None:
                for child in list(sp_pr):
                    sp_pr.remove(child)
            texts = list(shape.iter(a("t")))
            if ph_type == "ftr" and texts:
                texts[0].text = self.info.footer
                for extra in texts[1:]:
                    extra.text = ""
            elif ph_type == "sldNum" and texts:
                texts[0].text = str(self.number)
            for r_pr in shape.iter(a("rPr"), a("endParaRPr")):
                r_pr.set("lang", self.lang)
                if color is not None:
                    for old in r_pr.findall(a("solidFill")):
                        r_pr.remove(old)
                    fill = etree.Element(a("solidFill"))
                    etree.SubElement(fill, a("srgbClr")).set("val", color)
                    r_pr.insert(0, fill)
            tree.append(shape)

    # ------------------------------------------------------------------ text

    def write_paragraphs(
        self,
        slide: PptxSlide,
        body: etree._Element,
        paragraphs: list[Paragraph],
        scale: float = 1.0,
        color: str | None = None,
    ) -> None:
        """Replace the paragraphs; a scale below 1 shrinks the text the way PowerPoint's
        "shrink text on overflow" does (``normAutofit``), so it stays fitted when edited."""
        for old in body.findall(a("p")):
            body.remove(old)
        if scale < 1.0:
            body_pr = body.find(a("bodyPr"))
            if body_pr is None:
                body_pr = etree.Element(a("bodyPr"))
                body.insert(0, body_pr)
            for child in list(body_pr):
                body_pr.remove(child)
            autofit = etree.SubElement(body_pr, a("normAutofit"))
            autofit.set("fontScale", str(round(scale * 100000)))
        for paragraph in paragraphs or [Paragraph(())]:
            body.append(self.paragraph_element(slide, paragraph, color=color))

    def paragraph_element(
        self,
        slide: PptxSlide,
        paragraph: Paragraph,
        factor: float | None = None,
        color: str | None = None,
        first: bool = False,
    ) -> etree._Element:
        """A paragraph at its level of the master; on flow slides with explicit sizes (the
        level's size at ``factor``, see ``fitting.level_pt``), a colour, and no space before
        the ``first`` paragraph of a box."""
        element = etree.Element(a("p"))
        p_pr = etree.SubElement(element, a("pPr"))
        if paragraph.level:
            p_pr.set("lvl", str(paragraph.level))
        if first:
            spacing = etree.SubElement(p_pr, a("spcBef"))
            etree.SubElement(spacing, a("spcPts")).set("val", "0")
        if paragraph.kind is Kind.NUMBERED:
            auto = etree.SubElement(p_pr, a("buAutoNum"))
            auto.set("type", "arabicPeriod")
            if paragraph.start != 1:
                auto.set("startAt", str(paragraph.start))
        if not len(p_pr) and not p_pr.attrib:
            element.remove(p_pr)
        size = (
            round(fitting.level_pt(self.body_style, paragraph.level, factor) * 100)
            if factor is not None
            else None
        )
        for run in paragraph.runs:
            if run.is_break:
                br = etree.SubElement(element, a("br"))
                br_pr = etree.SubElement(br, a("rPr"))
                br_pr.set("lang", self.lang)
                if size is not None:
                    br_pr.set("sz", str(size))
                continue
            element.append(self.run_element(slide, run, size, color))
        end = etree.SubElement(element, a("endParaRPr"))
        end.set("lang", self.lang)
        if size is not None:
            end.set("sz", str(size))
        return element

    def run_element(
        self, slide: PptxSlide, run: Run, size: int | None, color: str | None = None
    ) -> etree._Element:
        """A run; ``color`` is its text colour (None: the placeholder's or the theme's).

        ``==mark==`` is bold on the PTA yellow, ``[words]{.x}`` bold in the signal colour of its
        status, the dot of a status label in that colour: on every slide.
        """
        r = etree.Element(a("r"))
        r_pr = etree.SubElement(r, a("rPr"))
        r_pr.set("lang", self.lang)
        if size is not None:
            r_pr.set("sz", str(size))
        bold = run.bold or run.mark or (run.status is not None and not run.label)
        if bold:
            r_pr.set("b", "1")
        if run.italic:
            r_pr.set("i", "1")
        if run.strike:
            r_pr.set("strike", "sngStrike")
        r_pr.set("dirty", "0")
        fill = colors.STATUS_COLORS[run.status] if run.status is not None else color
        if fill is not None:
            etree.SubElement(etree.SubElement(r_pr, a("solidFill")), a("srgbClr")).set("val", fill)
        if run.mark:
            highlight = etree.SubElement(r_pr, a("highlight"))
            etree.SubElement(highlight, a("srgbClr")).set("val", design.FLOW.highlight)
        if run.code:
            etree.SubElement(r_pr, a("latin")).set("typeface", design.CODE_FONT)
        elif bold:
            # PTA rule: emphasis in Segoe UI (the heading font), not in Segoe UI Light.
            etree.SubElement(r_pr, a("latin")).set("typeface", "+mj-lt")
        if run.link:
            r_id = slide.part.relate_to(run.link, RT.HYPERLINK, is_external=True)
            etree.SubElement(r_pr, a("hlinkClick")).set(f"{{{R}}}id", r_id)
        t = etree.SubElement(r, a("t"))
        t.text = run.text
        return r


def _flat(paragraph: Paragraph) -> Paragraph:
    """A paragraph as plain text at the placeholder's own first level."""
    return Paragraph(paragraph.runs, Kind.SUBHEADLINE)


def _placeholders(layout: SlideLayout) -> list[tuple[int, str]]:
    """(idx, type) of the layout's placeholders, in the order they are drawn."""
    result: list[tuple[int, str]] = []
    for ph in layout._element.iter(p("ph")):
        result.append((int(ph.get("idx", "0")), ph.get("type", "obj")))
    return result


def _decorative(layout: SlideLayout) -> set[int]:
    """Placeholders that only draw graphics: their prompt is "x" (see the design analysis)."""
    result: set[int] = set()
    for shape in layout.placeholders:
        if _text(shape._element).strip() == design.DECORATIVE_PROMPT:
            result.add(shape.placeholder_format.idx)
    return result


def _text(element: etree._Element) -> str:
    # itertext() on python-pptx elements repeats text; read the a:t elements instead.
    return "".join(t.text or "" for t in element.iter(a("t")))


def title_text(runs: tuple[Run, ...]) -> str:
    return plain_text(runs)
