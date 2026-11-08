"""SVG images (E06-S04): cleaning (``sanitizer``), size and PNG (``converter``, extra ``svg``)
and the image converter the generators use for ``.svg`` images (``SvgImageConverter``).

Importing this package loads neither resvg nor ``design.fonts``; ``converter.to_png`` does.
"""

from pta_documents.svg.converter import MAX_PIXELS, PngOptions, natural_size, to_png
from pta_documents.svg.image_converter import SvgImageConverter, is_svg
from pta_documents.svg.sanitizer import clean

__all__ = [
    "MAX_PIXELS",
    "PngOptions",
    "SvgImageConverter",
    "clean",
    "is_svg",
    "natural_size",
    "to_png",
]
