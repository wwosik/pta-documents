"""Converters from PDF, DOCX and PPTX to Markdown."""

from pta_documents.conversions.detect import detect
from pta_documents.conversions.options import ConversionOptions
from pta_documents.conversions.registry import ConverterRegistry, DocumentConverter, convert

__all__ = ["ConversionOptions", "ConverterRegistry", "DocumentConverter", "convert", "detect"]
