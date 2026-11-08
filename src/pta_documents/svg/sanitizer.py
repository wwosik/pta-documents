"""An SVG with everything that reaches outside it taken out, before it is drawn or embedded.

Port of DocLibs ``SvgSanitizer.cs``. resvg loads the file of an ``<image>`` whatever else it is
told, and Office would follow links of an embedded SVG; so before either sees it, these go:
scripts, ``foreignObject``, the DTD (entities are never expanded, nothing is fetched), processing
instructions, every link (``href``) that is not to the document's own elements or a ``data:``
URI, and the same in CSS ``url()`` values and ``@import`` rules.
"""

from __future__ import annotations

import re
from typing import Final

from lxml import etree

from pta_documents.errors import DocumentConversionError, DocumentFormat

REMOVED: Final = frozenset({"script", "foreignObject"})
"""Elements taken out with everything in them (by local name, in any namespace)."""

_URL: Final = re.compile(r"""url\(\s*['"]?(?P<target>[^'")]*)['"]?\s*\)""", re.IGNORECASE)
_IMPORT: Final = re.compile(r"@import[^;]*;?", re.IGNORECASE)


def clean(svg: bytes | str) -> str:
    """``svg`` without anything that reaches outside it, as markup.

    Raises ``DocumentConversionError`` (format SVG) when it is not well-formed XML or its root
    is not ``svg``.
    """
    content = svg.encode("utf-8") if isinstance(svg, str) else svg
    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        dtd_validation=False,
        huge_tree=False,
        remove_comments=True,
    )
    try:
        root = etree.fromstring(content, parser)
    except (etree.XMLSyntaxError, ValueError) as error:
        raise _error(f"it is not well-formed XML: {error}") from error
    if root is None or etree.QName(root).localname != "svg":
        raise _error("it is not an SVG document")
    for node in list(root.iter(etree.Entity, etree.ProcessingInstruction)):
        _remove(node)
    for element in list(root.iter(etree.Element)):
        if etree.QName(element).localname in REMOVED:
            _remove(element)
    for element in root.iter(etree.Element):
        for key, raw in list(element.attrib.items()):
            name, value = str(key), str(raw)
            if etree.QName(name).localname == "href" and not _internal(value):
                del element.attrib[name]
            elif "url(" in value.lower():
                element.set(name, _css(value))
        if etree.QName(element).localname == "style" and element.text:
            element.text = _css(element.text)
    return etree.tostring(root, encoding="unicode")


def _remove(node: etree._Element) -> None:
    """Take ``node`` out, keeping the text after it."""
    parent = node.getparent()
    if parent is None:
        return
    tail = node.tail
    if tail:
        previous = node.getprevious()
        if previous is not None:
            previous.tail = (previous.tail or "") + tail
        else:
            parent.text = (parent.text or "") + tail
    parent.remove(node)


def _internal(reference: str) -> bool:
    value = reference.strip()
    return value.startswith("#") or value.lower().startswith("data:")


def _css(css: str) -> str:
    """External ``url()`` values become ``none``, and ``@import`` rules go."""
    without_imports = _IMPORT.sub("", css)
    return _URL.sub(
        lambda match: match.group(0) if _internal(match.group("target")) else "none",
        without_imports,
    )


def _error(reason: str) -> DocumentConversionError:
    return DocumentConversionError(DocumentFormat.SVG, f"The SVG cannot be converted: {reason}.")
