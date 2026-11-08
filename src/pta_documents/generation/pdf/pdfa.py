"""Make the renderer's PDF a PDF/A-2b with pikepdf.

reportlab (open source) writes no PDF/A. This pass adds what PDF/A-2b asks for beyond embedded
fonts: XMP metadata with ``pdfaid:part`` 2 and ``pdfaid:conformance`` B that matches the
document information dictionary, an output intent ``GTS_PDFA1`` with an embedded sRGB profile,
``/F 4`` (print) on every annotation, ``/Lang`` in the catalog, PDF 1.7 and an ``/ID`` computed
from the content. Nothing is encrypted.

The sRGB profile comes from Pillow (``ImageCms.createProfile("sRGB")``, no ICC file in the
repo). LittleCMS stamps it with the current time; the stamp is set to a fixed date so that equal
input gives equal bytes.
"""

from __future__ import annotations

import datetime as dt
import io
import struct
from typing import Final

import pikepdf
from PIL import ImageCms

from pta_documents.generation.pdf.metadata import PRODUCER, PdfInfo

OUTPUT_CONDITION: Final = "sRGB IEC61966-2.1"
PRINT_FLAG: Final = 4
"""``/F`` bit 3 (print), which PDF/A requires on every annotation."""
PDF_VERSION: Final = "1.7"
ICC_DATE_OFFSET: Final = 24
"""Where the ICC header keeps its creation time (six big-endian 16-bit numbers)."""
ICC_FIXED_DATE: Final = dt.datetime(2000, 1, 1)


def srgb_profile() -> bytes:
    """Pillow's sRGB profile with a fixed creation date."""
    profile = bytearray(ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
    date = ICC_FIXED_DATE
    stamp = struct.pack(">6H", date.year, date.month, date.day, date.hour, date.minute, date.second)
    profile[ICC_DATE_OFFSET : ICC_DATE_OFFSET + len(stamp)] = stamp
    return bytes(profile)


def to_pdfa(data: bytes, info: PdfInfo) -> bytes:
    """``data`` (a PDF with every font embedded) as PDF/A-2b."""
    with pikepdf.open(io.BytesIO(data)) as pdf:
        _document_info(pdf, info)
        _xmp(pdf, info)
        _output_intent(pdf)
        _flag_annotations(pdf)
        pdf.Root.Lang = pikepdf.String(info.language_tag)
        output = io.BytesIO()
        pdf.save(
            output,
            min_version=PDF_VERSION,
            force_version=PDF_VERSION,
            deterministic_id=True,
            fix_metadata_version=False,
        )
    return output.getvalue()


def pdf_date(value: dt.datetime) -> str:
    """A date string of the information dictionary: ``D:20261108120000Z``."""
    return value.strftime("D:%Y%m%d%H%M%SZ")


def _document_info(pdf: pikepdf.Pdf, info: PdfInfo) -> None:
    """A new information dictionary: reportlab's (``ReportLab …``, its fixed dates) goes."""
    created = pdf_date(info.created_utc)
    entries: dict[str, pikepdf.Object] = {
        "/Producer": pikepdf.String(PRODUCER),
        "/Creator": pikepdf.String(PRODUCER),
        "/CreationDate": pikepdf.String(created),
        "/ModDate": pikepdf.String(created),
    }
    if info.title:
        entries["/Title"] = pikepdf.String(info.title)
    if info.author:
        entries["/Author"] = pikepdf.String(info.author)
    if info.subject:
        entries["/Subject"] = pikepdf.String(info.subject)
    pdf.docinfo = pdf.make_indirect(pikepdf.Dictionary(entries))


def _xmp(pdf: pikepdf.Pdf, info: PdfInfo) -> None:
    created = info.created_utc.isoformat()
    with pdf.open_metadata(set_pikepdf_as_editor=False, update_docinfo=False) as meta:
        meta["pdfaid:part"] = "2"
        meta["pdfaid:conformance"] = "B"
        meta["pdf:Producer"] = PRODUCER
        meta["xmp:CreatorTool"] = PRODUCER
        meta["xmp:CreateDate"] = created
        meta["xmp:ModifyDate"] = created
        meta["xmp:MetadataDate"] = created
        meta["dc:language"] = {info.language_tag}
        meta["dc:format"] = "application/pdf"
        if info.title:
            meta["dc:title"] = info.title
        if info.author:
            meta["dc:creator"] = [info.author]
        if info.subject:
            meta["dc:description"] = info.subject


def _output_intent(pdf: pikepdf.Pdf) -> None:
    profile = pikepdf.Stream(pdf, srgb_profile())
    profile.N = 3
    intent = pikepdf.Dictionary(
        Type=pikepdf.Name.OutputIntent,
        S=pikepdf.Name.GTS_PDFA1,
        OutputConditionIdentifier=pikepdf.String(OUTPUT_CONDITION),
        Info=pikepdf.String(OUTPUT_CONDITION),
        DestOutputProfile=profile,
    )
    pdf.Root.OutputIntents = pikepdf.Array([pdf.make_indirect(intent)])


def _flag_annotations(pdf: pikepdf.Pdf) -> None:
    for page in pdf.pages:
        annotations = page.obj.get("/Annots")
        if not isinstance(annotations, pikepdf.Array):
            continue
        for annotation in annotations:
            if isinstance(annotation, pikepdf.Dictionary):
                annotation.F = PRINT_FLAG
