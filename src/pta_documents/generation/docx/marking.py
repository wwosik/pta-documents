"""The marking of ``kennzeichnung:`` in Word (E12-S03): a text in every header, a line on the
cover and, for ``entwurf``, a watermark.

- **Header:** a text box without margins under the logo, just below the rule
  (``word_frame.marking_area``), with one right-aligned paragraph in „Kopfzeile", 9 pt, capitals,
  theme colour ``accent1`` (``design.word.MARKING``). It is anchored in the paragraph of the
  template's header that holds the logo and the rule and does not wrap, so the header keeps its
  height and the body does not move.
- **Watermark** (``entwurf``): the WordArt shape Word writes for a watermark
  (``design.word.WATERMARK_SHAPE``) in the same paragraph of every header — Word shows it behind
  the text of every page and removes it under *Entwurf → Wasserzeichen entfernen*.
- **Cover:** the text once more below „Autor, Ort, Datum", so that a printed cover shows it.

``kein`` changes nothing: the header parts stay those of the template, byte for byte.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final
from xml.sax.saxutils import quoteattr

from docx.document import Document
from docx.opc.part import Part
from lxml import etree

from pta_documents.design import word, word_frame
from pta_documents.design.variants import GeneratedTexts, Marking, WordVariant
from pta_documents.generation.common.openxml import w

WP: Final = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
WPS: Final = "http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
MC: Final = "http://schemas.openxmlformats.org/markup-compatibility/2006"
V: Final = "urn:schemas-microsoft-com:vml"
OFFICE: Final = "urn:schemas-microsoft-com:office:office"
W10: Final = "urn:schemas-microsoft-com:office:word"
NAMESPACES: Final = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": WP,
    "a": A,
    "wps": WPS,
    "mc": MC,
    "v": V,
    "o": OFFICE,
    "w10": W10,
}
PARSER: Final = etree.XMLParser(remove_blank_text=True)
"""Markup without the white space between elements (the templates have none)."""
EMU_PER_POINT: Final = 12700
RELATIVE_HEIGHT: Final = 251700000
"""The z-order of the text box: above the logo and the rule of the template."""


def emu(points: float) -> int:
    return round(points * EMU_PER_POINT)


def apply(
    document: Document,
    parts: Iterable[Part],
    marking: Marking,
    texts: GeneratedTexts,
    variant: WordVariant,
) -> None:
    """Put the marking (and for ``entwurf`` the watermark) into every header part of
    ``parts``."""
    if marking is Marking.NONE:
        return
    headers = [_root(p) for p in parts]
    frame = word_frame.read(variant)
    area = word_frame.marking_area(frame)
    style_id = str(document.styles[word.STYLES.header].style_id)
    next_id = _max_drawing_id(_xml_roots(document)) + 1
    for number, root in enumerate(headers, start=1):
        host = _host_paragraph(root, style_id)
        host.append(text_box(texts.marking(marking), area, next_id, style_id))
        next_id += 1
        if marking is Marking.DRAFT:
            page = frame.page
            host.append(watermark(texts.draft, page.text_width_pt, page.text_height_pt, number))


def cover_paragraph(document: Document, marking: Marking, texts: GeneratedTexts) -> None:
    """The marking below „Autor, Ort, Datum" on the cover: „Autor" in the colour and the
    capitals of the header marking."""
    if marking is Marking.NONE:
        return
    paragraph = document.add_paragraph(style=word.STYLES.author)
    run = etree.SubElement(paragraph._p, w("r"))
    run.append(_run_properties(sized=False))
    t = etree.SubElement(run, w("t"))
    t.text = texts.marking(marking)


def text_box(text: str, area: word_frame.Box, drawing_id: int, style_id: str) -> etree._Element:
    """A run with a text box over ``area`` holding ``text`` right-aligned in the paragraph style
    ``style_id`` („Kopfzeile")."""
    style = word.MARKING
    width, height = emu(area.width_pt), emu(area.height_pt)
    xml = f"""<w:r {_declarations()}><w:rPr><w:noProof/></w:rPr>
<mc:AlternateContent><mc:Choice Requires="wps"><w:drawing>
<wp:anchor distT="0" distB="0" distL="0" distR="0" simplePos="0"
 relativeHeight="{RELATIVE_HEIGHT}" behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1">
<wp:simplePos x="0" y="0"/>
<wp:positionH relativeFrom="margin"><wp:align>right</wp:align></wp:positionH>
<wp:positionV relativeFrom="page"><wp:posOffset>{emu(area.y_pt)}</wp:posOffset></wp:positionV>
<wp:extent cx="{width}" cy="{height}"/>
<wp:effectExtent l="0" t="0" r="0" b="0"/>
<wp:wrapNone/>
<wp:docPr id="{drawing_id}" name={quoteattr(style.shape_name)}/>
<wp:cNvGraphicFramePr/>
<a:graphic><a:graphicData uri="{WPS}"><wps:wsp>
<wps:cNvSpPr txBox="1"/>
<wps:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{width}" cy="{height}"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></wps:spPr>
<wps:txbx><w:txbxContent><w:p><w:pPr><w:pStyle w:val="{style_id}"/>
<w:spacing w:before="0" w:after="0"/><w:jc w:val="right"/></w:pPr></w:p></w:txbxContent></wps:txbx>
<wps:bodyPr rot="0" vert="horz" wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"
 anchorCtr="0"><a:noAutofit/></wps:bodyPr>
</wps:wsp></a:graphicData></a:graphic>
</wp:anchor></w:drawing></mc:Choice></mc:AlternateContent></w:r>"""
    run = etree.fromstring(xml, PARSER)
    paragraph = next(run.iter(w("p")))
    inner = etree.SubElement(paragraph, w("r"))
    inner.append(_run_properties())
    t = etree.SubElement(inner, w("t"))
    t.text = text
    return run


def watermark(text: str, width_pt: float, height_pt: float, number: int) -> etree._Element:
    """A run with the watermark ``text`` as large as the diagonal of ``width_pt`` ×
    ``height_pt`` (the type area) allows."""
    style = word.WATERMARK
    size = word.watermark_size(len(text) * style.capital_em, width_pt, height_pt)
    shape = word.WATERMARK_SHAPE.format(
        id=f"{style.shape_prefix}{number}",
        spid=f"_x0000_s{2048 + number}",
        width=f"{len(text) * style.capital_em * size:.2f}",
        height=f"{size:.2f}",
        rotation=f"{360 - style.angle:g}",
        color=style.color,
        opacity=f"{style.opacity:g}",
        font=style.font,
        text=quoteattr(text)[1:-1],
    )
    xml = (
        f"<w:r {_declarations()}><w:rPr><w:noProof/></w:rPr><w:pict>"
        f"{word.WATERMARK_SHAPETYPE}{shape}</w:pict></w:r>"
    )
    return etree.fromstring(xml, PARSER)


def watermarks(root: etree._Element) -> list[etree._Element]:
    """The watermark shapes of a header (``v:shape`` with Word's watermark id)."""
    prefix = word.WATERMARK.shape_prefix
    return [s for s in root.iter(f"{{{V}}}shape") if str(s.get("id", "")).startswith(prefix)]


def _run_properties(sized: bool = True) -> etree._Element:
    """Capitals in ``accent1``; ``sized``: at the size of the header marking."""
    style = word.MARKING
    r_pr = etree.Element(w("rPr"))
    if style.caps:
        etree.SubElement(r_pr, w("caps"))
    color = etree.SubElement(r_pr, w("color"))
    color.set(w("val"), style.color)
    color.set(w("themeColor"), style.theme_color)
    if sized:
        size = str(round(style.size_pt * 2))
        etree.SubElement(r_pr, w("sz")).set(w("val"), size)
        etree.SubElement(r_pr, w("szCs")).set(w("val"), size)
    return r_pr


def _declarations() -> str:
    return " ".join(f'xmlns:{prefix}="{uri}"' for prefix, uri in NAMESPACES.items())


def _root(part: Part) -> etree._Element:
    return part.element  # type: ignore[attr-defined]


def _host_paragraph(root: etree._Element, style_id: str) -> etree._Element:
    """The last paragraph of the header itself (in the templates the one with logo and rule),
    or a new one in „Kopfzeile"."""
    paragraphs = list(root.iterchildren(w("p")))
    if paragraphs:
        return paragraphs[-1]
    paragraph = etree.SubElement(root, w("p"))
    p_pr = etree.SubElement(paragraph, w("pPr"))
    etree.SubElement(p_pr, w("pStyle")).set(w("val"), style_id)
    return paragraph


def _xml_roots(document: Document) -> list[etree._Element]:
    """The XML of every part python-docx has parsed (body, headers, footers …)."""
    package = document.part.package
    assert package is not None
    return [e for p in package.iter_parts() if (e := getattr(p, "element", None)) is not None]


def _max_drawing_id(roots: Iterable[etree._Element]) -> int:
    """The highest ``wp:docPr/@id`` in ``roots``: drawing ids are unique in the document."""
    highest = 0
    for root in roots:
        for doc_pr in root.iter(f"{{{WP}}}docPr"):
            value = str(doc_pr.get("id", "0"))
            if value.isdigit():
                highest = max(highest, int(value))
    return highest
