"""Images made while generating, not taken from the resources (E11-S04).

An image reference ``![Zur Umfrage](qr:https://umfrage.example/abc "Feedback")`` is a QR code:
``add_generated`` makes a PNG for it (PTA blue on white) and returns the document with that PNG
as a resource under the reference itself, so the writers find it like any other image. Other
schemes stay what they were: a reference the resources must have.

``scale=N`` in the title of a QR code scales it (Word: from 3 cm; slides: from the room of the
layout); ``add_generated`` takes it out of the title and keeps it in ``Token.meta[SCALE]``.
"""

from __future__ import annotations

import io
import math
import re
from collections.abc import Iterable
from dataclasses import replace
from typing import Final
from urllib.parse import unquote

import segno
from markdown_it.token import Token

from pta_documents.design import colors
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.markdown.document import DocumentResource, MarkdownDocument
from pta_documents.markdown.parser import child_lines

QR_SCHEME: Final = "qr:"
SCHEMES: Final = (QR_SCHEME,)
"""The schemes of generated images; a reference with another one must be a resource."""
MAX_CHARACTERS: Final = 1000
"""The longest content of a QR code; longer ones get too dense to scan from a slide."""
EDGE_PIXELS: Final = 1000
"""The edge of the PNG at least, in pixels: sharp at any size it is shown at."""
SIZE_CM: Final = 3.0
"""The edge of a QR code in Word without ``scale``, in centimetres (from its dpi)."""
QUIET_ZONE: Final = 4
"""The white border around the code, in modules (the standard's minimum)."""
ERROR_LEVEL: Final = "m"
"""Error correction at least M (15 %); segno raises it where that costs no size."""
MAX_SCALE: Final = 5.0
SCALE: Final = "pta_documents.scale"
"""``Token.meta`` key of an image token: the ``scale=N`` taken out of its title."""
URL_SCHEMES: Final = ("http:", "https:", "mailto:")
"""Contents that are URLs and stay %-encoded as markdown-it wrote them."""
SCALE_PATTERN: Final = re.compile(r"(?<!\S)scale=(\S*)")
CONTENT_TYPE: Final = "image/png"
CM_PER_INCH: Final = 2.54


def is_generated(reference: str) -> bool:
    """Whether the image reference is made while generating (``qr:…``), not a resource."""
    return reference.strip().lower().startswith(SCHEMES)


def qr_content(reference: str) -> str:
    """What the QR code of ``qr:<content>`` holds: the content as written. markdown-it
    %-encodes link destinations; URLs stay so, other contents (``WIFI:…``, text) are decoded,
    so that ``S:Mein%20Netz`` scans as ``Mein Netz``."""
    content = reference.strip()[len(QR_SCHEME) :]
    if content.lower().startswith(URL_SCHEMES):
        return content
    return unquote(content)


def qr_png(content: str) -> bytes:
    """A QR code of ``content`` as PNG: PTA blue on white, at least ``EDGE_PIXELS`` wide, with
    the dpi that make it ``SIZE_CM`` wide."""
    # micro=False: phone scanners rarely read Micro QR codes, which segno picks for short text.
    code = segno.make(content, error=ERROR_LEVEL, micro=False)
    modules = code.symbol_size(border=QUIET_ZONE)[0]
    module_pixels = math.ceil(EDGE_PIXELS / modules)
    edge = modules * module_pixels
    output = io.BytesIO()
    code.save(
        output,
        kind="png",
        scale=module_pixels,
        border=QUIET_ZONE,
        dark="#" + colors.PTA_BLUE,
        light="#" + colors.WHITE,
        dpi=round(edge / (SIZE_CM / CM_PER_INCH)),
    )
    return output.getvalue()


def resolve(reference: str, format: DocumentFormat, line: int | None = None) -> DocumentResource:
    """The generated image of ``reference`` (``is_generated``), under the reference as path.

    Raises ``DocumentConversionError`` (with ``line``) for an empty or too long content.
    """
    content = qr_content(reference)
    if not content:
        raise _error(format, line, "The QR code has no content: write it after 'qr:'.")
    if len(content) > MAX_CHARACTERS:
        raise _error(
            format,
            line,
            f"The QR code has {len(content)} characters, more than {MAX_CHARACTERS}. Use a "
            "shorter link.",
        )
    return DocumentResource(reference, CONTENT_TYPE, qr_png(content))


def add_generated(
    document: MarkdownDocument, tokens: Iterable[Token], format: DocumentFormat, line_offset: int
) -> MarkdownDocument:
    """``document`` with a resource for every generated image of ``tokens``, which it does not
    have yet; ``scale=N`` moves from their titles into ``Token.meta[SCALE]``.

    Raises ``DocumentConversionError`` with the line for a broken QR code or ``scale``.
    """
    added: list[DocumentResource] = []
    seen: set[str] = set()
    for token in tokens:
        if token.type != "inline":
            continue
        for child, line in zip(token.children or [], child_lines(token, line_offset), strict=True):
            if child.type != "image":
                continue
            reference = str(child.attrs.get("src", ""))
            if not is_generated(reference):
                continue
            _take_scale(child, format, line)
            if reference in seen or document.find_resource(reference) is not None:
                continue
            seen.add(reference)
            added.append(resolve(reference, format, line))
    if not added:
        return document
    return replace(document, resources=(*document.resources, *added))


def scale_of(image: Token) -> float:
    """The ``scale=N`` of a generated image (``add_generated``); 1 without."""
    value = image.meta.get(SCALE) if image.meta else None
    return value if isinstance(value, float) else 1.0


def _take_scale(image: Token, format: DocumentFormat, line: int | None) -> None:
    title = str(image.attrs.get("title") or "")
    match = SCALE_PATTERN.search(title)
    if match is None:
        return
    written = match.group(1)
    try:
        scale = float(written.replace(",", "."))
    except ValueError:
        scale = math.nan
    if not 0 < scale <= MAX_SCALE:
        raise _error(
            format,
            line,
            f"'scale={written}' is no scale: write a number above 0 and at most "
            f"{MAX_SCALE:g}, e.g. scale=0.5.",
        )
    rest = " ".join((title[: match.start()] + title[match.end() :]).split())
    if rest:
        image.attrs["title"] = rest
    else:
        image.attrs.pop("title", None)
    image.meta = {**(image.meta or {}), SCALE: scale}


def _error(format: DocumentFormat, line: int | None, reason: str) -> DocumentConversionError:
    return DocumentConversionError(format, f"Line {line}: {reason}" if line else reason)
