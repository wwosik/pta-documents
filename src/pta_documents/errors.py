"""The one error type of the library and the document formats it names."""

from __future__ import annotations

from enum import StrEnum


class DocumentFormat(StrEnum):
    """A document format the library detects, reads or writes."""

    UNKNOWN = "unknown"
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    ZIP = "zip"
    OLE = "ole"
    DOC = "doc"
    XLS = "xls"
    PPT = "ppt"
    MSG = "msg"
    RTF = "rtf"
    TEXT = "text"
    SVG = "svg"
    MARKDOWN = "markdown"


class DocumentConversionError(Exception):
    """A document could not be read or written; ``reason`` says why, for the writer."""

    def __init__(self, format: DocumentFormat, reason: str) -> None:
        super().__init__(f"{format.value}: {reason}")
        self.format = format
        self.reason = reason
