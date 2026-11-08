"""Recognising a document's format from its content; the file name only refines OLE files."""

from __future__ import annotations

import io
import os
import zipfile
from typing import BinaryIO, Final

from pta_documents.errors import DocumentFormat

PROBE_LENGTH: Final = 8192
"""How many bytes from the start are looked at."""

ZIP_SIGNATURE: Final = b"PK\x03\x04"
OLE_SIGNATURE: Final = bytes([0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1])
PDF_SIGNATURE: Final = b"%PDF"
RTF_SIGNATURE: Final = b"{\\rtf"

OLE_EXTENSIONS: Final = {
    ".doc": DocumentFormat.DOC,
    ".dot": DocumentFormat.DOC,
    ".xls": DocumentFormat.XLS,
    ".xlt": DocumentFormat.XLS,
    ".xla": DocumentFormat.XLS,
    ".ppt": DocumentFormat.PPT,
    ".pps": DocumentFormat.PPT,
    ".pot": DocumentFormat.PPT,
    ".msg": DocumentFormat.MSG,
}
"""The kind of an OLE file by its extension; the content alone cannot tell them apart."""

ZIP_ENTRIES: Final = (
    ("word/document.xml", DocumentFormat.DOCX),
    ("xl/workbook.xml", DocumentFormat.XLSX),
    ("ppt/presentation.xml", DocumentFormat.PPTX),
)


def detect(data: bytes | BinaryIO, file_name: str | None = None) -> DocumentFormat:
    """The format of ``data``. The content always wins over the extension of ``file_name``,
    which only tells OLE files apart. A stream must be seekable; its position is restored."""
    if isinstance(data, bytes):
        return _detect(io.BytesIO(data), _extension(file_name))
    if not data.seekable():
        raise ValueError("The stream must be seekable; read it into bytes first.")
    start = data.tell()
    try:
        return _detect(data, _extension(file_name))
    finally:
        data.seek(start)


def _extension(file_name: str | None) -> str:
    return os.path.splitext(file_name or "")[1].lower()


def _detect(stream: BinaryIO, extension: str) -> DocumentFormat:
    start = stream.tell()
    head = stream.read(PROBE_LENGTH)
    if head.startswith(ZIP_SIGNATURE):
        stream.seek(start)
        return _detect_zip(stream)
    if head.startswith(OLE_SIGNATURE):
        return OLE_EXTENSIONS.get(extension, DocumentFormat.OLE)
    if head.startswith(PDF_SIGNATURE):
        return DocumentFormat.PDF
    if head.startswith(RTF_SIGNATURE):
        return DocumentFormat.RTF
    return DocumentFormat.TEXT if head and b"\0" not in head else DocumentFormat.UNKNOWN


def _detect_zip(stream: BinaryIO) -> DocumentFormat:
    if stream.tell() != 0:
        # zipfile locates entries relative to the end of the file; a ZIP embedded in a larger
        # stream is read from its start on.
        stream = io.BytesIO(stream.read())
    try:
        with zipfile.ZipFile(stream) as package:
            names = set(package.namelist())
    except (zipfile.BadZipFile, OSError, EOFError, ValueError):
        return DocumentFormat.UNKNOWN
    return next((format for entry, format in ZIP_ENTRIES if entry in names), DocumentFormat.ZIP)
