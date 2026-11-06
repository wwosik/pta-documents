"""PPTX to Markdown (port of DocLibs ``PptxConverter``)."""

from __future__ import annotations

from typing import BinaryIO, Final

from lxml import etree

from pta_documents.conversions.openxml import OpenXmlPackage, guard, read_input
from pta_documents.conversions.options import ConversionOptions, ResourceCollector
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.markdown import text as md
from pta_documents.markdown.document import MarkdownDocument, MetadataKeys

P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
R: Final = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
MC: Final = "http://schemas.openxmlformats.org/markup-compatibility/2006"

PRESENTATION_PART: Final = "ppt/presentation.xml"


def p(name: str) -> str:
    return f"{{{P}}}{name}"


def a(name: str) -> str:
    return f"{{{A}}}{name}"


class PptxConverter:
    format: Final = DocumentFormat.PPTX

    def can_convert(self, format: DocumentFormat) -> bool:
        return format is DocumentFormat.PPTX

    def convert(
        self, data: bytes | BinaryIO, options: ConversionOptions | None = None
    ) -> MarkdownDocument:
        options = options or ConversionOptions()
        content = read_input(data)
        return guard(DocumentFormat.PPTX, lambda: self._convert(content, options))

    def _convert(self, data: bytes, options: ConversionOptions) -> MarkdownDocument:
        package = OpenXmlPackage(data)
        try:
            presentation = package.read_xml(PRESENTATION_PART)
            if presentation is None:
                raise DocumentConversionError(
                    DocumentFormat.PPTX, "ppt/presentation.xml is missing."
                )
            rels = package.relationships(PRESENTATION_PART)
            images = (
                ResourceCollector(options.resource_path_prefix) if options.include_images else None
            )
            out: list[str] = []
            number = 0
            any_content = False
            for slide_id in presentation.iter(p("sldId")):
                rel_id = slide_id.get(f"{{{R}}}id")
                part = rels.get(rel_id) if rel_id else None
                if part is None:
                    continue
                number += 1
                any_content |= _render_slide(package, part, number, images, out)
            metadata = {MetadataKeys.SLIDE_COUNT: str(number)}
            package.add_core_properties(metadata)
            return MarkdownDocument(
                md.normalize("".join(out)) if any_content else "",
                tuple(images.resources) if images else (),
                metadata,
            )
        finally:
            package.close()


def _placeholder_type(shape: etree._Element) -> str | None:
    ph = shape.find(f"{p('nvSpPr')}/{p('nvPr')}/{p('ph')}")
    return ph.get("type") if ph is not None else None


def _is_title(shape: etree._Element) -> bool:
    return _placeholder_type(shape) in ("title", "ctrTitle")


def _is_footer(shape: etree._Element) -> bool:
    """Slide number, date and footer placeholders repeat on every slide and are not content."""
    return _placeholder_type(shape) in ("sldNum", "dt", "ftr")


def _render_slide(
    package: OpenXmlPackage,
    part: str,
    number: int,
    images: ResourceCollector | None,
    out: list[str],
) -> bool:
    """Returns whether the slide had any content beyond its heading."""
    slide = package.read_xml(part)
    c_sld = slide.find(p("cSld")) if slide is not None else None
    tree = c_sld.find(p("spTree")) if c_sld is not None else None
    title_shape = (
        next((s for s in tree.iter(p("sp")) if _is_title(s)), None) if tree is not None else None
    )
    title = ""
    if title_shape is not None:
        body = title_shape.find(p("txBody"))
        title = " ".join(_paragraphs(body)) if body is not None else ""
    out.append("## " + (title or f"Slide {number}") + "\n\n")
    if tree is None:
        return bool(title)

    rels = package.relationships(part)
    content = bool(title)
    for element in tree.iter():
        if any(anc.tag in (f"{{{MC}}}Fallback", a("tbl")) for anc in element.iterancestors()):
            continue
        parent = element.getparent()
        if (
            element.tag == p("txBody")
            and parent is not None
            and parent is not title_shape
            and not _is_footer(parent)
        ):
            lines = _paragraphs(element)
            if lines:
                out.append("\n\n".join(lines) + "\n\n")
                content = True
        elif element.tag == a("tbl"):
            grid = [
                ["<br>".join(_paragraphs(tc)) for tc in tr.iterfind(a("tc"))]
                for tr in element.iterfind(a("tr"))
            ]
            out.append(md.table(grid))
            content = True
        elif element.tag == p("pic") and images is not None:
            picture = _picture(element, package, rels, images)
            if picture is not None:
                out.append(picture + "\n\n")
                content = True
    return content


def _picture(
    picture: etree._Element,
    package: OpenXmlPackage,
    rels: dict[str, str],
    images: ResourceCollector,
) -> str | None:
    blip = picture.find(f"{p('blipFill')}/{a('blip')}")
    rel_id = blip.get(f"{{{R}}}embed") if blip is not None else None
    part = rels.get(rel_id) if rel_id else None
    content = package.read_bytes(part) if part else None
    if part is None or content is None:
        return None
    properties = picture.find(f"{p('nvPicPr')}/{p('cNvPr')}")
    alt = (properties.get("descr") if properties is not None else None) or ""
    path = images.add(part[part.rfind("/") + 1 :], content)
    return f"![{md.escape(alt).replace(chr(10), ' ')}]({md.destination(path)})"


def _paragraphs(container: etree._Element) -> list[str]:
    result: list[str] = []
    for paragraph in container.iter(a("p")):
        parts: list[str] = []
        for element in paragraph:
            if element.tag == a("br"):
                parts.append(" ")
            else:
                parts.append("".join(t.text or "" for t in element.iter(a("t"))))
        text = "".join(parts).strip()
        if text:
            result.append(md.escape(text))
    return result
