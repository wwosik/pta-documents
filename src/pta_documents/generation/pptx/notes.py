"""Speaker notes: the notes page of a slide, on the notes master of the PTA template.

The template brings its notes master (slide image above, notes below); a notes slide is made
only for a slide with notes, so a deck without ``::: notes`` has no notes pages at all. The
paragraphs keep bold, italic, code and links; list items go on the master's bulleted levels.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Final

from lxml import etree
from pptx.slide import Slide as PptxSlide

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.pptx.model import Kind, Paragraph

if TYPE_CHECKING:
    from pta_documents.generation.pptx.writer import DeckWriter

FORMAT: Final = DocumentFormat.PPTX
A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
MAX_LIST_LEVEL: Final = 3
"""The deepest level of the notes master a list item goes on (``a:lvl4pPr``, "Vierte Ebene");
levels 1-3 carry the PTA bullets, level 0 is plain text."""


def a(name: str) -> str:
    return f"{{{A}}}{name}"


def level(paragraph: Paragraph) -> int:
    """The zero-based level of the notes master for ``paragraph``: 0 for text, 1-3 for list
    items by depth."""
    if paragraph.kind in (Kind.BULLET, Kind.NUMBERED):
        return min(1 + paragraph.depth, MAX_LIST_LEVEL)
    return 0


def write_notes(deck: DeckWriter, slide: PptxSlide, paragraphs: Sequence[Paragraph]) -> None:
    """Give ``slide`` its notes page with ``paragraphs`` in the notes placeholder."""
    notes_slide = slide.notes_slide
    placeholder: Any = notes_slide.notes_placeholder
    if placeholder is None:
        raise DocumentConversionError(
            FORMAT, "The notes master of the PTA template has no notes placeholder."
        )
    body: etree._Element = placeholder._element.txBody
    for old in body.findall(a("p")):
        body.remove(old)
    for paragraph in paragraphs:
        element = etree.SubElement(body, a("p"))
        p_pr = etree.SubElement(element, a("pPr"))
        lvl = level(paragraph)
        if lvl:
            p_pr.set("lvl", str(lvl))
        if paragraph.kind is Kind.NUMBERED:
            auto = etree.SubElement(p_pr, a("buAutoNum"))
            auto.set("type", "arabicPeriod")
            if paragraph.start != 1:
                auto.set("startAt", str(paragraph.start))
        if not len(p_pr) and not p_pr.attrib:
            element.remove(p_pr)
        for run in paragraph.runs:
            if run.is_break:
                etree.SubElement(etree.SubElement(element, a("br")), a("rPr")).set(
                    "lang", deck.lang
                )
                continue
            element.append(deck.run_element(notes_slide, run, None))
        etree.SubElement(element, a("endParaRPr")).set("lang", deck.lang)
