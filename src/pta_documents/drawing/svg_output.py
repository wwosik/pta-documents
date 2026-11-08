"""Writes a ``Drawing`` as a standalone SVG with tooltips that need no script.

Port of DocLibs ``DrawingSvg.cs``. Each item with a ``hover`` becomes a
``<g class="chart-hoverable">`` holding the item and a ``<g class="chart-tooltip">`` placed in
advance; an inline ``<style>`` shows the tooltip on ``:hover``. The class names stay as in
DocLibs, so a page can restyle them: ``chart-hoverable``, ``chart-tooltip``,
``chart-tooltip-bg``, ``chart-tooltip-text`` and ``chart-hover-dot``.

Fonts are named, never embedded (decision 2026-11-07): browsers substitute what is missing.
Pure Python; the module needs no extra.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Final

from pta_documents.design import colors
from pta_documents.drawing.model import (
    ClosePath,
    CubicTo,
    Drawing,
    DrawingHotspot,
    DrawingHover,
    DrawingPath,
    DrawingShape,
    DrawingText,
    LineTo,
    MoveTo,
    ShapeKind,
    TextAnchor,
)

SVG_NS: Final = "http://www.w3.org/2000/svg"

TOOLTIP_HEIGHT: Final = 17.0
TOOLTIP_PADDING: Final = 6.0
TOOLTIP_SIZE: Final = 10.0
TOOLTIP_GAP: Final = 6.0
"""Room between the tooltip's bottom and its hover point."""

CHARACTER_WIDTH: Final = 0.58
"""The share of the font size a character takes, on average, in a proportional font. The SVG is
written, not measured, so tooltips and lines that must shrink to their room use this estimate."""

MIN_TEXT_SCALE: Final = 0.7
"""A line too wide for its ``max_width`` is set smaller, down to this share of its size."""

HOT_DOT_STROKE_WIDTH: Final = 1.25


def _css_family() -> str:
    # Imported here so that importing the drawing model never loads design.fonts (core test).
    from pta_documents.design.fonts import CSS_FAMILY

    return CSS_FAMILY


def _css_mono_family() -> str:
    from pta_documents.design.fonts import CSS_MONO_FAMILY

    return CSS_MONO_FAMILY


@dataclass(frozen=True, slots=True)
class SvgOptions:
    """How ``to_svg`` writes a drawing. Colours are ``RRGGBB`` without ``#``."""

    font_family: str = field(default_factory=_css_family)
    """The CSS font family of the text; default ``design.fonts.CSS_FAMILY``."""
    mono_family: str = field(default_factory=_css_mono_family)
    """The CSS font family of mono text; default ``design.fonts.CSS_MONO_FAMILY``."""
    background: str | None = None
    """A colour filling the whole canvas first; None: transparent."""
    tooltip_fill: str = colors.TEXT_SLIDES
    """The tooltip's background, drawn at 94 % opacity."""
    tooltip_text: str = colors.WHITE
    """The tooltip's text colour."""


def to_svg(drawing: Drawing, options: SvgOptions | None = None) -> str:
    """The drawing as SVG markup, ``width`` and ``height`` in pixels with a matching ``viewBox``.

    Raises ``ValueError`` for a colour that is not ``RRGGBB`` and for a number that is not finite.
    """
    options = options or SvgOptions()
    width, height = number(drawing.width), number(drawing.height)
    parts = [
        f'<svg xmlns="{SVG_NS}" width="{width}" height="{height}" viewBox="0 0 {width} {height}"'
        f' font-family="{escape(options.font_family)}">'
    ]
    if any(item.hover is not None for item in drawing.items):
        parts.append(
            "<style>"
            ".chart-tooltip,.chart-hover-dot{opacity:0;pointer-events:none;"
            "transition:opacity .1s ease-in-out}"
            ".chart-hoverable:hover .chart-tooltip,.chart-hoverable:hover .chart-hover-dot"
            "{opacity:1}"
            f".chart-tooltip-bg{{fill:{paint(options.tooltip_fill)};fill-opacity:.94}}"
            f".chart-tooltip-text{{fill:{paint(options.tooltip_text)};"
            f"font-size:{number(TOOLTIP_SIZE)}px}}"
            "</style>"
        )
    if options.background is not None:
        parts.append(
            f'<rect x="0" y="0" width="{width}" height="{height}"'
            f' fill="{paint(options.background)}"/>'
        )
    for item in drawing.items:
        match item:
            case DrawingShape():
                markup = _shape(item)
            case DrawingText():
                markup = _text(item, options)
            case DrawingHotspot():
                markup = _hotspot(item)
        parts.append(
            markup if item.hover is None else _hoverable(markup, item.hover, drawing.width)
        )
    parts.append("</svg>")
    return "".join(parts)


def estimate_width(text: str, size: float) -> float:
    """Roughly how wide ``text`` is at ``size`` pixels, in a proportional font."""
    return len(text) * size * CHARACTER_WIDTH


def _shape(shape: DrawingShape) -> str:
    attributes = f' fill="{"none" if shape.fill is None else paint(shape.fill)}"'
    if shape.even_odd:
        attributes += ' fill-rule="evenodd"'
    if shape.stroke is not None and shape.stroke_width > 0:
        attributes += f' stroke="{paint(shape.stroke)}" stroke-width="{number(shape.stroke_width)}"'
        if shape.dash:
            attributes += f' stroke-dasharray="{",".join(number(d) for d in shape.dash)}"'
        if shape.round_joins:
            attributes += ' stroke-linejoin="round" stroke-linecap="round"'
    x, y, w, h = shape.path.bounds
    match shape.kind:
        case ShapeKind.RECTANGLE:
            return (
                f'<rect x="{number(x)}" y="{number(y)}" width="{number(w)}" height="{number(h)}"'
                f"{attributes}/>"
            )
        case ShapeKind.ROUNDED_RECTANGLE:
            return (
                f'<rect x="{number(x)}" y="{number(y)}" width="{number(w)}" height="{number(h)}"'
                f' rx="{number(shape.corner_radius)}"{attributes}/>'
            )
        case ShapeKind.ELLIPSE:
            return (
                f'<ellipse cx="{number(x + w / 2)}" cy="{number(y + h / 2)}"'
                f' rx="{number(w / 2)}" ry="{number(h / 2)}"{attributes}/>'
            )
        case ShapeKind.PATH:
            return f'<path d="{path_data(shape.path)}"{attributes}/>'


def path_data(path: DrawingPath) -> str:
    """The ``d`` attribute of a path: absolute ``M``/``L``/``C``/``Z``."""
    commands: list[str] = []
    for segment in path.segments:
        match segment:
            case MoveTo(x, y):
                commands.append(f"M{number(x)},{number(y)}")
            case LineTo(x, y):
                commands.append(f"L{number(x)},{number(y)}")
            case CubicTo(x1, y1, x2, y2, x, y):
                commands.append(
                    f"C{number(x1)},{number(y1)} {number(x2)},{number(y2)} {number(x)},{number(y)}"
                )
            case ClosePath():
                commands.append("Z")
    return " ".join(commands)


def _text(text: DrawingText, options: SvgOptions) -> str:
    size = text.size
    estimate = estimate_width(text.text, size)
    if text.max_width is not None and estimate > text.max_width:
        size *= max(MIN_TEXT_SCALE, text.max_width / estimate)
    parts = [
        f'<text x="{number(text.x)}" y="{number(text.baseline)}" font-size="{number(size)}"'
        f' fill="{paint(text.color)}"'
    ]
    if text.anchor is not TextAnchor.START:
        parts.append(f' text-anchor="{text.anchor.value}"')
    if text.mono:
        parts.append(f' font-family="{escape(options.mono_family)}"')
    parts.append(' xml:space="preserve">')
    for span in text.spans:
        if not span.bold and span.color is None:
            parts.append(escape(span.text))
            continue
        parts.append("<tspan")
        if span.bold:
            parts.append(' font-weight="bold"')
        if span.color is not None:
            parts.append(f' fill="{paint(span.color)}"')
        parts.append(f">{escape(span.text)}</tspan>")
    parts.append("</text>")
    return "".join(parts)


def _hotspot(spot: DrawingHotspot) -> str:
    centre = f'cx="{number(spot.x)}" cy="{number(spot.y)}"'
    markup = f'<circle {centre} r="{number(spot.radius)}" fill="transparent"/>'
    if spot.dot is None:
        return markup
    return (
        f'{markup}<circle class="chart-hover-dot" {centre} r="{number(spot.dot_radius)}"'
        f' fill="{paint(spot.dot)}" stroke="{paint(colors.WHITE)}"'
        f' stroke-width="{number(HOT_DOT_STROKE_WIDTH)}"/>'
    )


def _hoverable(markup: str, hover: DrawingHover, canvas_width: float) -> str:
    """The item with its tooltip: centred over the hover point, kept on the canvas horizontally,
    just above the point."""
    width = estimate_width(hover.text, TOOLTIP_SIZE) + 2 * TOOLTIP_PADDING
    left = min(max(hover.x - width / 2, 2), max(2, canvas_width - width - 2))
    top = hover.y - TOOLTIP_HEIGHT - TOOLTIP_GAP
    return (
        f'<g class="chart-hoverable">{markup}<g class="chart-tooltip">'
        f'<rect class="chart-tooltip-bg" x="{number(left)}" y="{number(top)}"'
        f' width="{number(width)}" height="{number(TOOLTIP_HEIGHT)}" rx="3"/>'
        f'<text class="chart-tooltip-text" x="{number(left + width / 2)}"'
        f' y="{number(top + TOOLTIP_HEIGHT - 5)}" text-anchor="middle">{escape(hover.text)}</text>'
        "</g></g>"
    )


def number(value: float) -> str:
    """At most two decimals, no trailing zeros, never ``-0`` (DocLibs ``0.##``)."""
    if not math.isfinite(value):
        raise ValueError(f"a drawing needs finite numbers, got {value}")
    text = f"{round(value, 2):.2f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


_COLOUR: Final = re.compile(r"[0-9A-Fa-f]{6}")
_CONTROL: Final = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def paint(colour: str) -> str:
    """``#RRGGBB`` for an ``RRGGBB`` colour."""
    if not _COLOUR.fullmatch(colour):
        raise ValueError(f"a drawing colour is RRGGBB without '#', got {colour!r}")
    return "#" + colour


def escape(text: str) -> str:
    """XML-safe text for content and attributes: control characters other than tab, line feed
    and carriage return removed (XML 1.0 has no place for them), ``& < > "`` escaped."""
    text = _CONTROL.sub("", text)
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )
