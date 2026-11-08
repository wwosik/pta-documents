"""Image converters: turn an image a generator cannot place (SVG …) into a PNG or JPEG.

Port of DocLibs ``IImageConverter`` and ``ImageConverters``. The generators ask their converters
in order, with ``scale = 2``, for every image in a format they do not take; the first result wins,
and an image nobody converts stays an error, as without converters.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Protocol

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.markdown.document import DocumentResource

GENERATOR_SCALE: Final = 2.0
"""The scale the generators ask for: twice the natural size, so it stays sharp when enlarged."""


@dataclass(frozen=True, slots=True)
class ConvertedImage:
    """An image converted by an ``ImageConverter``."""

    content: bytes
    """The PNG or JPEG."""
    content_type: str
    """``image/png`` or ``image/jpeg``."""
    width: float
    """The natural width in pixels: what the image is placed at, before any scaling."""
    height: float
    """The natural height in pixels."""
    svg: bytes | None = None
    """The original as a cleaned SVG, for formats that embed it beside the PNG (``asvg:svgBlip``
    in PowerPoint and Word); None: there is none."""


@dataclass(frozen=True, slots=True)
class Conversion:
    """What ``convert_image`` returns: the converted image at the original's path, its
    natural size in pixels (at 96 dpi) and the SVG to embed beside it, if any."""

    image: DocumentResource
    width: float
    height: float
    svg: bytes | None = None


class ImageConverter(Protocol):
    """Turns an image in a format the generators cannot place into a PNG or JPEG."""

    def convert(self, image: DocumentResource, scale: float) -> ConvertedImage | None:
        """The image drawn at ``scale`` pixels per pixel of its natural size; None when the image
        is not in a format this converter takes. Raises ``DocumentConversionError`` when it is,
        but cannot be converted."""
        ...

    @property
    def format(self) -> str | None:
        """The format this converter takes as the authoring guides name it (``SVG``); None
        leaves it out of the guides."""
        ...


def default_converters() -> tuple[ImageConverter, ...]:
    """The converters the generators use unless their options say otherwise: every converter of
    the library that is available — SVG to PNG (``SvgImageConverter``) with the extra ``svg``."""
    if not svg_available():
        return ()
    from pta_documents.svg.image_converter import SvgImageConverter

    return (SvgImageConverter(),)


def svg_available() -> bool:
    """Whether resvg (extra ``svg``) is installed, which SVG to PNG needs."""
    return importlib.util.find_spec("resvg_py") is not None


def refusal_hint(image: DocumentResource, converters: Sequence[ImageConverter]) -> str:
    """What a generator adds to its error for an image no converter takes: that the extra
    ``svg`` is missing for an SVG, else that no converter takes it (when there are any)."""
    from pta_documents.svg.image_converter import is_svg

    if is_svg(image) and not svg_available():
        return "; SVG images need the extra 'svg' (pip install 'pta-documents[svg]')"
    return ", and no image converter takes it" if converters else ""


def convert_image(
    converters: Sequence[ImageConverter],
    image: DocumentResource,
    scale: float,
    format: DocumentFormat,
) -> Conversion | None:
    """The first conversion of ``image`` by ``converters``; None when no converter takes it.

    A ``DocumentConversionError`` of a converter passes unchanged; any other exception becomes a
    ``DocumentConversionError`` in ``format`` with the original as ``__cause__``.
    """
    for converter in converters:
        try:
            converted = converter.convert(image, scale)
        except DocumentConversionError:
            raise
        except Exception as error:
            raise DocumentConversionError(
                format, f"The image '{image.path}' cannot be converted: {error}"
            ) from error
        if converted is not None:
            return Conversion(
                DocumentResource(image.path, converted.content_type, converted.content),
                converted.width,
                converted.height,
                converted.svg,
            )
    return None
