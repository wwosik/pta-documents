"""Drawings of the code-block renderers (Mermaid, financial charts) in Word (E03-S04).

A ``DrawingGraphic`` becomes SVG (``drawing.to_svg``, text in Selawik/Segoe UI) and goes the way
of an SVG image from Markdown (E06-S04): a PNG at twice the natural size in ``a:blip``, the SVG
beside it in ``asvg:svgBlip``. Without an SVG converter (extra ``svg``) Word cannot place it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from pta_documents.drawing.model import Drawing
from pta_documents.drawing.svg_output import SvgOptions, to_svg
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.code_blocks import fence_language
from pta_documents.generation.common.images import (
    GENERATOR_SCALE,
    Conversion,
    ImageConverter,
    convert_image,
    svg_available,
)
from pta_documents.markdown.document import DocumentResource

FORMAT: Final = DocumentFormat.DOCX
SVG_TYPE: Final = "image/svg+xml"


def svg_resource(drawing: Drawing, info: str, number: int) -> DocumentResource:
    """``drawing`` as an SVG resource named after the fence language and its number in the
    document (``mermaid-1.svg``)."""
    name = fence_language(info) or "drawing"
    svg = to_svg(drawing, SvgOptions())
    return DocumentResource(f"{name}-{number}.svg", SVG_TYPE, svg.encode("utf-8"))


def convert(
    drawing: Drawing,
    info: str,
    line: int | None,
    number: int,
    converters: Sequence[ImageConverter],
) -> Conversion:
    """The PNG of ``drawing`` with its natural size and SVG; raises ``DocumentConversionError``
    when no converter takes SVG (the extra ``svg`` is missing, or the converters are off)."""
    resource = svg_resource(drawing, info, number)
    conversion = convert_image(converters, resource, GENERATOR_SCALE, FORMAT)
    if conversion is None:
        where = f"Line {line}: " if line else ""
        if not svg_available():
            why = "that needs the extra 'svg' (pip install 'pta-documents[svg]')"
        else:
            why = "no image converter takes SVG (DocxOptions.image_converters)"
        raise DocumentConversionError(
            FORMAT,
            f"{where}The `{fence_language(info) or info}` block is a drawing, which Word places "
            f"as an SVG image with a PNG beside it; {why}. Install it, or leave the block out.",
        )
    return conversion
