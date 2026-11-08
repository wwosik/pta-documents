"""The image styles ``.grey`` and ``.round`` (E15-S04), made with Pillow before placing.

``.grey`` makes a greyscale PNG; ``.round`` a square around the focus with a circle as alpha
channel, as PNG (JPEG has no transparency). ``apply`` puts the result into the document as a
new resource beside the original (``images/foto-round.png``) and points the image token at it,
so the writers and converters place it like any other picture. PowerPoint draws ``.round`` as an
ellipse geometry on the picture instead (editable, nothing lost): there only ``.grey`` is made
here.
"""

from __future__ import annotations

import io
import posixpath
from collections.abc import Iterable
from dataclasses import replace
from typing import Final

from markdown_it.token import Token
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import image_attributes
from pta_documents.generation.common.image_attributes import Focus
from pta_documents.markdown.document import DocumentResource, MarkdownDocument

CONTENT_TYPE: Final = "image/png"
SUPERSAMPLING: Final = 4
"""The circle mask is drawn this many times larger and shrunk, for a smooth edge."""


def grey(content: bytes) -> bytes:
    """The image as a greyscale PNG; transparency stays."""
    with Image.open(io.BytesIO(content)) as opened:
        dpi = opened.info.get("dpi")
        picture = opened.convert("RGBA") if _has_alpha(opened) else opened.convert("RGB")
    result = ImageOps.grayscale(picture)
    if picture.mode == "RGBA":
        result = Image.merge("LA", (result, picture.getchannel("A")))
    return _png(result, dpi)


def round_png(content: bytes, focus: Focus) -> bytes:
    """A square of the image, as large as it allows and centred on ``focus`` (at its edge at
    most), with everything outside the inscribed circle transparent, as PNG."""
    with Image.open(io.BytesIO(content)) as opened:
        dpi = opened.info.get("dpi")
        picture = opened.convert("RGBA")
    width, height = picture.size
    left, top, right, bottom = image_attributes.visible_window((width, height), 1.0, focus)
    box = (
        round(left * width),
        round(top * height),
        round(width - right * width),
        round(height - bottom * height),
    )
    square = picture.crop(box)
    edge = min(square.size)
    square = square.crop((0, 0, edge, edge))
    large = Image.new("L", (edge * SUPERSAMPLING, edge * SUPERSAMPLING), 0)
    ImageDraw.Draw(large).ellipse((0, 0, *large.size), fill=255)
    mask = large.resize((edge, edge), Image.Resampling.LANCZOS)
    alpha = square.getchannel("A")
    square.putalpha(Image.composite(alpha, Image.new("L", alpha.size, 0), mask))
    return _png(square, dpi)


def apply(
    document: MarkdownDocument,
    images: Iterable[tuple[Token, int | None]],
    format: DocumentFormat,
) -> MarkdownDocument:
    """``document`` with a styled resource for every image of ``images`` with ``.grey`` or
    ``.round`` (read by ``image_attributes.take``), each image token pointing at its styled
    resource. PowerPoint keeps ``.round`` for its ellipse geometry.

    Raises ``DocumentConversionError`` with the line for a missing resource or one Pillow does
    not read (an SVG: styles take PNG, JPEG, GIF, BMP, TIFF and WebP).
    """
    added: list[DocumentResource] = []
    for image, line in images:
        attributes = image_attributes.of(image)
        circle = attributes.round and format is not DocumentFormat.PPTX
        if not (attributes.grey or circle):
            continue
        source = str(image.attrs.get("src", ""))
        resource = _find(document, added, source)
        if resource is None:
            continue  # the writers report the missing resource with their own message
        content = resource.content
        try:
            if attributes.grey:
                content = grey(content)
            if circle:
                content = round_png(content, attributes.point)
        except (UnidentifiedImageError, OSError) as error:
            styles = " ".join(
                name
                for name, used in ((".grey", attributes.grey), (".round", attributes.round))
                if used
            )
            reason = (
                f"The image '{source}' is a {resource.content_type}; {styles} takes PNG, JPEG, "
                "GIF, BMP, TIFF and WebP. Leave the style out or use a raster image."
            )
            raise DocumentConversionError(
                format, f"Line {line}: {reason}" if line else reason
            ) from error
        suffix = "-grey" if attributes.grey else ""
        suffix += "-round" if circle else ""
        path = _path(document, added, source, suffix, content)
        if _find(document, added, path) is None:
            added.append(DocumentResource(path, CONTENT_TYPE, content))
        image.attrs["src"] = path
    if not added:
        return document
    return replace(document, resources=(*document.resources, *added))


def _find(
    document: MarkdownDocument, added: list[DocumentResource], path: str
) -> DocumentResource | None:
    found = document.find_resource(path)
    if found is not None:
        return found
    return next((r for r in added if r.path == path), None)


def _path(
    document: MarkdownDocument,
    added: list[DocumentResource],
    source: str,
    suffix: str,
    content: bytes,
) -> str:
    """A free resource path for the styled ``content`` of ``source`` (``a/foto-round.png``),
    or the path of a resource that already holds it."""
    stem, _ = posixpath.splitext(source)
    candidate = f"{stem}{suffix}.png"
    number = 1
    while (existing := _find(document, added, candidate)) is not None:
        if existing.content == content:
            return candidate
        number += 1
        candidate = f"{stem}{suffix}-{number}.png"
    return candidate


def _has_alpha(picture: Image.Image) -> bool:
    return picture.mode in ("RGBA", "LA", "PA") or "transparency" in picture.info


def _png(picture: Image.Image, dpi: object) -> bytes:
    output = io.BytesIO()
    if isinstance(dpi, tuple) and len(dpi) == 2:  # pyright: ignore[reportUnknownArgumentType]
        picture.save(output, "PNG", dpi=dpi)
    else:
        picture.save(output, "PNG")
    return output.getvalue()
