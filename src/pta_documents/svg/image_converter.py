"""Lets the generators place SVG images: each becomes a PNG at twice its natural size, with the
cleaned SVG beside it for formats that can embed it (``asvg:svgBlip`` in PowerPoint and Word).

Port of DocLibs ``SvgImageConverter.cs``. Takes resources of type ``image/svg+xml``, a path
ending in ``.svg``, or content that starts like SVG. Needs the extra ``svg`` to convert; telling
an SVG apart (``is_svg``) needs nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.images import ConvertedImage
from pta_documents.markdown.document import DocumentResource
from pta_documents.svg import converter, sanitizer

CONTENT_TYPE: Final = "image/svg+xml"
_HEAD: Final = 1024
"""How many bytes of the content ``is_svg`` looks at."""


def is_svg(image: DocumentResource) -> bool:
    """Whether ``image`` is an SVG: by its type, its path, or content that starts like one."""
    if image.content_type.lower() == CONTENT_TYPE or image.path.lower().endswith(".svg"):
        return True
    head = image.content[:_HEAD].decode("utf-8", errors="replace").lstrip("﻿ \t\r\n")
    return (head.startswith("<svg") or head.startswith("<?xml")) and "<svg" in head


@dataclass(frozen=True, slots=True)
class SvgImageConverter:
    """An ``ImageConverter`` for SVG; see the module."""

    system_fonts: bool = False
    """Also use the system's fonts (Segoe UI where installed); default off, so the PNG is the
    same on every machine."""

    @property
    def format(self) -> str | None:
        return "SVG"

    def convert(self, image: DocumentResource, scale: float) -> ConvertedImage | None:
        if not is_svg(image):
            return None
        try:
            clean = sanitizer.clean(image.content)
            width, height = converter.natural_size(clean)
            png = converter.to_png(
                clean, converter.PngOptions(max(scale, 0.01), system_fonts=self.system_fonts)
            )
        except DocumentConversionError as error:
            raise DocumentConversionError(
                DocumentFormat.SVG,
                f"The image '{image.path}' cannot be converted: "
                + error.reason.removeprefix("The SVG cannot be converted: "),
            ) from error
        return ConvertedImage(png, "image/png", width, height, svg=clean.encode("utf-8"))
