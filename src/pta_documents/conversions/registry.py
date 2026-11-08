"""One entry point for all converters: detect the format, hand the document to its converter."""

from __future__ import annotations

import dataclasses
import importlib
import importlib.util
from collections.abc import Iterable
from typing import BinaryIO, Final, Protocol, cast

from pta_documents.conversions.detect import detect
from pta_documents.conversions.docx import DocxConverter
from pta_documents.conversions.openxml import read_input
from pta_documents.conversions.options import ConversionOptions
from pta_documents.conversions.pptx import PptxConverter
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.markdown.document import MarkdownDocument

PDF_CONVERTER_MODULE: Final = "pta_documents.conversions.pdf"
"""Module of the PDF converter (E07-S04): a class ``PdfConverter`` with a constructor without
arguments. ``ConverterRegistry.default()`` registers it when the module and the extra ``pdf``
can be imported."""

PDF_EXTRA_MODULES: Final = ("pdfplumber", "pikepdf")
"""The packages of the extra ``pdf`` the PDF converter needs."""

NO_CONVERTER: Final = "No converter is registered for this format."

PDF_EXTRA_MISSING: Final = "PDF needs the optional extra 'pdf' (pip install -e '.[pdf]')."

_LEGACY: Final = "Legacy binary Office files ({kind}) are not supported. {advice}"

_LEGACY_ADVICE: Final = {
    DocumentFormat.DOC: ("Word 97-2003, .doc", "Save the file in Word as .docx and convert that."),
    DocumentFormat.PPT: (
        "PowerPoint 97-2003, .ppt",
        "Save the file in PowerPoint as .pptx and convert that.",
    ),
    DocumentFormat.XLS: (
        "Excel 97-2003, .xls",
        "Excel workbooks cannot be converted; copy the tables into a Word document, save it "
        "as .docx and convert that.",
    ),
    DocumentFormat.MSG: (
        "Outlook message, .msg",
        "Save the attachments as .docx or .pptx, or the message in Word as .docx, and convert "
        "those.",
    ),
    DocumentFormat.OLE: (
        "OLE compound file",
        "Save the file as .docx or .pptx and convert that.",
    ),
}

_OTHER_ADVICE: Final = {
    DocumentFormat.RTF: "RTF files are not supported. Save the file in Word as .docx and "
    "convert that.",
    DocumentFormat.XLSX: "Excel workbooks are not supported. Copy the tables into a Word "
    "document, save it as .docx and convert that.",
    DocumentFormat.TEXT: f"{NO_CONVERTER[:-1]}; Markdown and plain text need no conversion.",
}


class DocumentConverter(Protocol):
    """Converts documents of the formats it accepts to Markdown."""

    def can_convert(self, format: DocumentFormat) -> bool: ...

    def convert(
        self, data: bytes | BinaryIO, options: ConversionOptions | None = None
    ) -> MarkdownDocument: ...


class ConverterRegistry:
    """Detects a document's format and hands it to the first converter that accepts it."""

    def __init__(self, converters: Iterable[DocumentConverter]) -> None:
        self.converters: tuple[DocumentConverter, ...] = tuple(converters)
        """The converters, in order of precedence."""

    @classmethod
    def default(cls, *additional: DocumentConverter) -> ConverterRegistry:
        """The converters of this package — PDF (only with the extra ``pdf``), DOCX, PPTX —
        followed by ``additional``."""
        pdf = _pdf_converter()
        builtin: list[DocumentConverter] = [DocxConverter(), PptxConverter()]
        return cls([*([pdf] if pdf else []), *builtin, *additional])

    def can_convert(self, format: DocumentFormat) -> bool:
        return any(converter.can_convert(format) for converter in self.converters)

    @property
    def formats(self) -> tuple[DocumentFormat, ...]:
        """The formats some registered converter accepts."""
        return tuple(format for format in DocumentFormat if self.can_convert(format))

    def convert(
        self,
        data: bytes | BinaryIO,
        file_name: str | None = None,
        options: ConversionOptions | None = None,
    ) -> MarkdownDocument:
        """Detect the format of ``data`` and convert it. The input is read once, so streams
        need not be seekable. ``file_name`` (or ``options.file_name``) refines the detection of
        OLE files and is passed on to the converter in ``options``."""
        options = options or ConversionOptions()
        if file_name is not None:
            options = dataclasses.replace(options, file_name=file_name)
        content = read_input(data)
        format = detect(content, options.file_name)
        converter = next((c for c in self.converters if c.can_convert(format)), None)
        if converter is None:
            raise DocumentConversionError(format, self._rejection(format))
        return converter.convert(content, options)

    def _rejection(self, format: DocumentFormat) -> str:
        if format in _LEGACY_ADVICE:
            kind, advice = _LEGACY_ADVICE[format]
            return _LEGACY.format(kind=kind, advice=advice)
        if format is DocumentFormat.PDF and not pdf_extra_available():
            return PDF_EXTRA_MISSING
        supported = ", ".join(format.value for format in self.formats) or "none"
        reason = _OTHER_ADVICE.get(format, NO_CONVERTER)
        return f"{reason} Supported formats: {supported}."


def pdf_extra_available() -> bool:
    """Whether the packages of the extra ``pdf`` are installed."""
    return all(importlib.util.find_spec(module) is not None for module in PDF_EXTRA_MODULES)


def _pdf_converter() -> DocumentConverter | None:
    if not pdf_extra_available():
        return None
    try:
        module = importlib.import_module(PDF_CONVERTER_MODULE)
    except ModuleNotFoundError as error:
        if error.name != PDF_CONVERTER_MODULE:
            raise
        return None  # The PDF converter follows with E07-S04.
    return cast(DocumentConverter, module.PdfConverter())


def convert(
    data: bytes | BinaryIO,
    file_name: str | None = None,
    options: ConversionOptions | None = None,
) -> MarkdownDocument:
    """Convert a document of any supported format with ``ConverterRegistry.default()``."""
    return ConverterRegistry.default().convert(data, file_name, options)
