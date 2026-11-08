"""The sticker ("VERTRAULICH", "Für den internen Gebrauch", "ENTWURF") on the slide master
(``kennzeichnung:``, E04-S05).

Like the training template, the sticker lives on the master: every slide whose layout shows the
master graphics shows it, and it is changed in one place in PowerPoint. The training master
carries it already ("Rectangle 7"), so only its text is set; the basic master gets a shape built
after it from ``design.slides.STICKER``.
"""

from __future__ import annotations

from typing import Final

from lxml import etree
from pptx.presentation import Presentation

from pta_documents.design import slides as design
from pta_documents.design.variants import GeneratedTexts, Language, Marking, SlidesVariant
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.markdown.front_matter import Keys

FORMAT: Final = DocumentFormat.PPTX
A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"


def a(name: str) -> str:
    return f"{{{A}}}{name}"


def p(name: str) -> str:
    return f"{{{P}}}{name}"


def resolve(variant: SlidesVariant, marking: Marking | None) -> Marking:
    """The marking of a deck: the given one, else the template's; the training template's
    cannot be removed."""
    if marking is None:
        return variant.default_marking
    if marking is Marking.NONE and variant is SlidesVariant.TRAINING:
        raise DocumentConversionError(
            FORMAT,
            f"'{Keys.MARKING}: {Marking.NONE.value}' is not allowed with "
            f"'{Keys.TEMPLATE}: {SlidesVariant.TRAINING.value}': PTA training slides must be "
            "marked for internal use (rule on the first slide of the training template). Valid "
            f"values here: {', '.join(m.value for m in Marking if m is not Marking.NONE)}.",
        )
    return marking


def apply(
    presentation: Presentation, marking: Marking, texts: GeneratedTexts, language: Language
) -> None:
    """Put the sticker for ``marking`` on every slide master of ``presentation``."""
    text = texts.marking(marking)
    lang = "en-US" if language is Language.EN else "de-DE"
    for master in presentation.slide_masters:
        tree = master.shapes._spTree
        found = find(tree)
        if found is not None:
            if marking is Marking.NONE:
                tree.remove(found)
            else:
                set_text(found, text, lang)
        elif marking is not Marking.NONE:
            tree.append(build(text, lang, next_id(tree)))


def find(tree: etree._Element) -> etree._Element | None:
    """The sticker among the shapes of a master, or None."""
    for shape in tree.iterchildren(p("sp")):
        c_nv_pr = shape.find(f"{p('nvSpPr')}/{p('cNvPr')}")
        if c_nv_pr is not None and c_nv_pr.get("name") == design.STICKER.shape_name:
            return shape
    return None


def set_text(shape: etree._Element, text: str, lang: str) -> None:
    """The first run keeps its formatting and takes ``text``; further runs go."""
    runs = list(shape.iter(a("r")))
    first = runs[0]
    for extra in runs[1:]:
        parent = extra.getparent()
        if parent is not None:
            parent.remove(extra)
    r_pr = first.find(a("rPr"))
    if r_pr is not None:
        r_pr.set("lang", lang)
    t = first.find(a("t"))
    assert t is not None
    t.text = text


def next_id(tree: etree._Element) -> int:
    ids = [int(e.get("id", "0")) for e in tree.iter(p("cNvPr"))]
    return max(ids, default=0) + 1


def build(text: str, lang: str, shape_id: int) -> etree._Element:
    """The sticker shape after "Rectangle 7" of the training master."""
    style = design.STICKER
    area = style.area
    sp = etree.Element(p("sp"), nsmap={"a": A, "p": P})
    nv_sp_pr = etree.SubElement(sp, p("nvSpPr"))
    etree.SubElement(nv_sp_pr, p("cNvPr"), id=str(shape_id), name=style.shape_name)
    etree.SubElement(nv_sp_pr, p("cNvSpPr"))
    etree.SubElement(nv_sp_pr, p("nvPr"), userDrawn="1")

    sp_pr = etree.SubElement(sp, p("spPr"))
    xfrm = etree.SubElement(sp_pr, a("xfrm"))
    etree.SubElement(xfrm, a("off"), x=str(area.left), y=str(area.top))
    etree.SubElement(xfrm, a("ext"), cx=str(area.width), cy=str(area.height))
    geometry = etree.SubElement(sp_pr, a("prstGeom"), prst="rect")
    etree.SubElement(geometry, a("avLst"))
    grad = etree.SubElement(sp_pr, a("gradFill"))
    stops = etree.SubElement(grad, a("gsLst"))
    for position, color, transparent in style.gradient:
        gs = etree.SubElement(stops, a("gs"), pos=str(position))
        scheme = etree.SubElement(gs, a("schemeClr"), val=color)
        if transparent:
            etree.SubElement(scheme, a("alpha"), val="0")
    etree.SubElement(grad, a("lin"), ang="0", scaled="0")
    line = etree.SubElement(sp_pr, a("ln"))
    etree.SubElement(line, a("noFill"))

    tx_body = etree.SubElement(sp, p("txBody"))
    etree.SubElement(
        tx_body,
        a("bodyPr"),
        lIns=str(style.inset_left),
        tIns=str(style.inset_top),
        rIns=str(style.inset_right),
        bIns=str(style.inset_bottom),
        rtlCol="0",
        anchor="ctr",
    )
    etree.SubElement(tx_body, a("lstStyle"))
    paragraph = etree.SubElement(tx_body, a("p"))
    etree.SubElement(paragraph, a("pPr"), algn="r")
    run = etree.SubElement(paragraph, a("r"))
    r_pr = etree.SubElement(run, a("rPr"), lang=lang, sz=str(round(style.text_size_pt * 100)))
    fill = etree.SubElement(r_pr, a("solidFill"))
    etree.SubElement(fill, a("schemeClr"), val=style.text_color)
    etree.SubElement(r_pr, a("latin"), typeface="+mj-lt")
    etree.SubElement(run, a("t")).text = text
    return sp
