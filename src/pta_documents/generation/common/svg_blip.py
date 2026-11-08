"""An SVG beside the PNG of a picture (``asvg:svgBlip``), for PowerPoint and Word (E06-S04).

Office 2016 and later draw the SVG, older versions and other readers the PNG. The SVG is an image
part of its own (``image/svg+xml``), related from the part that holds the picture, and named in
an extension of the picture's ``a:blip``. An SVG already in the package is reused.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Final

from lxml import etree

from pta_documents.generation.common.openxml import R

A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
ASVG: Final = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
SVG_BLIP_URI: Final = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
"""The ``uri`` of the ``a:ext`` that holds the ``asvg:svgBlip``."""
IMAGE_RELATIONSHIP: Final = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
)
CONTENT_TYPE: Final = "image/svg+xml"

PartFactory = Callable[[str, bytes], Any]
"""Makes a new part of the package from a part name and its bytes (python-docx and python-pptx
take the arguments of ``Part`` in different orders)."""


def attach(picture: etree._Element, part: Any, svg: bytes, new_part: PartFactory) -> None:
    """Put ``svg`` beside the image of ``picture`` (a ``p:pic`` or ``pic:pic``, or any element
    holding one ``a:blip``), whose relationships ``part`` holds.

    ``part.package`` gives the package; ``new_part(partname, blob)`` makes a part when the SVG is
    not in the package yet, named ``/<root>/media/imageN.svg``.
    """
    blip = next(picture.iter(f"{{{A}}}blip"))
    target = _existing(part.package, svg)
    if target is None:
        target = new_part(_partname(part.package, part), svg)
    r_id: str = part.relate_to(target, IMAGE_RELATIONSHIP)
    ext_list = blip.find(f"{{{A}}}extLst")
    if ext_list is None:
        ext_list = etree.SubElement(blip, f"{{{A}}}extLst")
    ext = etree.SubElement(ext_list, f"{{{A}}}ext")
    ext.set("uri", SVG_BLIP_URI)
    vector = etree.SubElement(ext, f"{{{ASVG}}}svgBlip", nsmap={"asvg": ASVG})
    vector.set(f"{{{R}}}embed", r_id)


def _existing(package: Any, svg: bytes) -> Any | None:
    for candidate in package.iter_parts():
        if candidate.content_type == CONTENT_TYPE and candidate.blob == svg:
            return candidate
    return None


def _partname(package: Any, part: Any) -> str:
    """``/ppt/media/imageN.svg`` or ``/word/media/imageN.svg``: the media folder of the
    package, from the part name of ``part``."""
    root = str(part.partname).split("/")[1]
    return str(package.next_partname(f"/{root}/media/image%d.svg"))
