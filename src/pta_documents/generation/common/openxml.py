"""Small helpers for editing WordprocessingML with lxml."""

from __future__ import annotations

from typing import Final

from lxml import etree

W: Final = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R: Final = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def w(name: str) -> str:
    return f"{{{W}}}{name}"


def paragraph_text(paragraph: etree._Element) -> str:
    return "".join(t.text or "" for t in paragraph.iter(w("t")))


def replace_in_paragraph(paragraph: etree._Element, old: str, new: str) -> bool:
    """Replace ``old`` by ``new`` across the ``w:t`` runs of a paragraph (Word splits text).

    The replacement goes into the run where ``old`` starts, so it keeps that run's format.
    """
    texts = list(paragraph.iter(w("t")))
    joined = "".join(t.text or "" for t in texts)
    start = joined.find(old)
    if start < 0:
        return False
    end = start + len(old)
    position = 0
    placed = False
    for t in texts:
        value = t.text or ""
        t_start, t_end = position, position + len(value)
        position = t_end
        if t_end <= start or t_start >= end:
            continue
        before = value[: max(0, start - t_start)]
        after = value[max(0, end - t_start) :] if end < t_end else ""
        t.text = before + ("" if placed else new) + after
        placed = True
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return True


def remove(element: etree._Element) -> None:
    parent = element.getparent()
    if parent is not None:
        parent.remove(element)


def field_paragraph_runs(instruction: str, cached: str = "") -> list[etree._Element]:
    """Runs of a complex field: begin, instruction, separate, cached result, end."""
    runs: list[etree._Element] = []

    def run() -> etree._Element:
        r = etree.Element(w("r"))
        runs.append(r)
        return r

    etree.SubElement(run(), w("fldChar")).set(w("fldCharType"), "begin")
    instr = etree.SubElement(run(), w("instrText"))
    instr.text = f" {instruction} "
    instr.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    etree.SubElement(run(), w("fldChar")).set(w("fldCharType"), "separate")
    if cached:
        t = etree.SubElement(run(), w("t"))
        t.text = cached
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    etree.SubElement(run(), w("fldChar")).set(w("fldCharType"), "end")
    return runs


# CT_Settings elements that come after w:updateFields in the schema sequence.
_AFTER_UPDATE_FIELDS: Final = (
    "hdrShapeDefaults",
    "footnotePr",
    "endnotePr",
    "compat",
    "docVars",
    "rsids",
    "mathPr",
    "attachedSchema",
    "themeFontLang",
    "clrSchemeMapping",
    "doNotIncludeSubdocsInStats",
    "doNotAutoCompressPictures",
    "forceUpgrade",
    "captions",
    "readModeInkLockDown",
    "smartTagType",
    "schemaLibrary",
    "shapeDefaults",
    "doNotEmbedSmartTags",
    "decimalSymbol",
    "listSeparator",
)


def set_update_fields(settings: etree._Element) -> None:
    """Make Word update all fields (TOC, SEQ, STYLEREF) when it opens the document."""
    existing = settings.find(w("updateFields"))
    if existing is None:
        existing = etree.Element(w("updateFields"))
        anchor = next(
            (
                child
                for child in settings.iterchildren(tag=etree.Element)
                if etree.QName(child).localname in _AFTER_UPDATE_FIELDS
                and etree.QName(child).namespace == W
            ),
            None,
        )
        if anchor is None:
            settings.append(existing)
        else:
            anchor.addprevious(existing)
    existing.set(w("val"), "true")
