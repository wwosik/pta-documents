"""A bundled icon as a PNG, drawn with Pillow (E15-S03): no extra needed.

Pillow draws lines but no Bézier curves: every curve becomes ``CURVE_STEPS`` straight pieces.
Round ends and joins are discs of the line width at every point. The icon is drawn
``SUPERSAMPLING`` times larger and scaled down, so its edges are smooth; the background is
transparent. The same icon gives the same bytes on every call. The PNG names its icon in a
text chunk ``TEXT_KEY``, so that the converters can write ``:icon-name:`` again (``name_of``).
"""

from __future__ import annotations

import io
from typing import Final

from PIL import Image, ImageDraw, UnidentifiedImageError
from PIL.PngImagePlugin import PngInfo

from pta_documents.design import icons
from pta_documents.design.icons import loader
from pta_documents.drawing.model import ClosePath, CubicTo, LineTo, MoveTo, PathSegment, Point

CURVE_STEPS: Final = 16
SUPERSAMPLING: Final = 4
TEXT_KEY: Final = "pta-documents-icon"
"""The key of the PNG text chunk that holds the icon's name."""


def png(name: str, color: str, pixels: int) -> bytes:
    """The icon ``name`` as a ``pixels`` × ``pixels`` PNG in ``color`` (``RRGGBB``) on a
    transparent background."""
    big = pixels * SUPERSAMPLING
    scale = big / icons.GRID
    width = icons.STROKE_WIDTH * scale
    mask = Image.new("L", (big, big), 0)
    pen = ImageDraw.Draw(mask)
    for outline in loader.outlines(name):
        for line in polylines(outline):
            points = [(x * scale, y * scale) for x, y in line]
            if len(points) > 1:
                pen.line(points, fill=255, width=max(1, round(width)))
            radius = width / 2
            for x, y in points:
                pen.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)
    alpha = mask.resize((pixels, pixels), Image.Resampling.LANCZOS)
    picture = Image.new("RGBA", (pixels, pixels), (*_rgb(color), 0))
    picture.putalpha(alpha)
    info = PngInfo()
    info.add_text(TEXT_KEY, name)
    out = io.BytesIO()
    picture.save(out, format="PNG", optimize=True, pnginfo=info)
    return out.getvalue()


def name_of(data: bytes) -> str | None:
    """The name of the bundled icon a PNG of ``png`` shows; None for any other picture."""
    if not data.startswith(b"\x89PNG"):
        return None
    try:
        with Image.open(io.BytesIO(data)) as picture:
            text = picture.info.get(TEXT_KEY)
    except (OSError, UnidentifiedImageError, ValueError):
        return None
    return text if isinstance(text, str) and icons.is_icon(text) else None


def polylines(outline: list[PathSegment]) -> list[list[Point]]:
    """The subpaths of an outline as lists of points, curves cut into straight pieces."""
    result: list[list[Point]] = []
    current: list[Point] = []
    for segment in outline:
        match segment:
            case MoveTo(x, y):
                if len(current) > 1:
                    result.append(current)
                current = [(x, y)]
            case LineTo(x, y):
                current.append((x, y))
            case CubicTo(x1, y1, x2, y2, x, y):
                x0, y0 = current[-1] if current else (x1, y1)
                for step in range(1, CURVE_STEPS + 1):
                    t = step / CURVE_STEPS
                    u = 1 - t
                    current.append(
                        (
                            u**3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t**3 * x,
                            u**3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t**3 * y,
                        )
                    )
            case ClosePath():
                if current:
                    current.append(current[0])
                    result.append(current)
                    current = [current[0]]
    if len(current) > 1:
        result.append(current)
    return result


def _rgb(color: str) -> tuple[int, int, int]:
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
