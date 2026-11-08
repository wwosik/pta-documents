"""Reading DrawingML for the HTML deck: namespaces, units, the theme and its colours.

The HTML deck draws the slides the PPTX generator wrote (E10-S01), so colours, fonts and sizes
come from the PresentationML of that deck — the PTA template — never from a second table.
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass
from typing import Final

from lxml import etree

A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
R: Final = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
C: Final = "http://schemas.openxmlformats.org/drawingml/2006/chart"
MC: Final = "http://schemas.openxmlformats.org/markup-compatibility/2006"
ASVG: Final = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
P159: Final = "http://schemas.microsoft.com/office/powerpoint/2015/09/main"
THEME_RELATION: Final = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"

EMU_PER_POINT: Final = 12700
STAGE_WIDTH: Final = 1600
"""The width of the stage in CSS pixels; the height follows the slide size (900 for 16:9)."""

Element = etree._Element


def a(name: str) -> str:
    return f"{{{A}}}{name}"


def p(name: str) -> str:
    return f"{{{P}}}{name}"


def r(name: str) -> str:
    return f"{{{R}}}{name}"


def local(element: Element) -> str:
    try:
        return etree.QName(element).localname
    except ValueError:  # a comment or processing instruction
        return ""


def number(value: float) -> str:
    """A CSS or SVG number: at most two decimals, no trailing zeros."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def integer(element: Element | None, name: str, default: int = 0) -> int:
    if element is None:
        return default
    value = element.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Units:
    """EMU to CSS pixels of the stage."""

    per_emu: float

    @classmethod
    def of(cls, slide_width: int) -> Units:
        return cls(STAGE_WIDTH / slide_width)

    def px(self, emu: float) -> float:
        return emu * self.per_emu

    def pt(self, points: float) -> float:
        return points * EMU_PER_POINT * self.per_emu


# ---------------------------------------------------------------------- colours


@dataclass(frozen=True)
class Color:
    """An RGB colour (``RRGGBB``) and its opacity."""

    rgb: str
    alpha: float = 1.0

    def css(self) -> str:
        if self.alpha >= 0.999:
            return "#" + self.rgb.lower()
        red, green, blue = (int(self.rgb[i : i + 2], 16) for i in (0, 2, 4))
        return f"rgba({red},{green},{blue},{number(self.alpha)})"


COLOR_TAGS: Final = ("srgbClr", "schemeClr", "sysClr", "prstClr", "scrgbClr", "hslClr")
_PRESET_COLORS: Final = {"black": (0, 0, 0), "white": (255, 255, 255)}
_SCHEME_NAMES: Final = (
    "dk1",
    "lt1",
    "dk2",
    "lt2",
    "accent1",
    "accent2",
    "accent3",
    "accent4",
    "accent5",
    "accent6",
    "hlink",
    "folHlink",
)
_DEFAULT_MAP: Final = {
    "bg1": "lt1",
    "tx1": "dk1",
    "bg2": "lt2",
    "tx2": "dk2",
}


@dataclass(frozen=True)
class Theme:
    """The colour scheme, the fonts and the line widths of a master's theme."""

    scheme: dict[str, str]
    major_font: str
    minor_font: str
    line_widths: tuple[int, ...]

    @classmethod
    def read(cls, theme: Element) -> Theme:
        scheme: dict[str, str] = {}
        colors = theme.find(f".//{a('clrScheme')}")
        if colors is not None:
            for name in _SCHEME_NAMES:
                entry = colors.find(a(name))
                if entry is None or not len(entry):
                    continue
                value = entry[0]
                rgb = value.get("lastClr") if local(value) == "sysClr" else value.get("val")
                if rgb:
                    scheme[name] = rgb.upper()
        major = theme.find(f".//{a('majorFont')}/{a('latin')}")
        minor = theme.find(f".//{a('minorFont')}/{a('latin')}")
        widths = tuple(
            integer(ln, "w", 9525) for ln in theme.iterfind(f".//{a('lnStyleLst')}/{a('ln')}")
        )
        return cls(
            scheme,
            major.get("typeface", "") if major is not None else "",
            minor.get("typeface", "") if minor is not None else "",
            widths,
        )

    def font(self, typeface: str) -> str:
        """``+mj-lt`` and ``+mn-lt`` resolved to the theme's fonts."""
        if typeface.startswith("+mj"):
            return self.major_font
        if typeface.startswith("+mn"):
            return self.minor_font
        return typeface


@dataclass(frozen=True)
class Palette:
    """The theme with the colour mapping of a slide (master map, overridden by layout or slide)."""

    theme: Theme
    mapping: dict[str, str]

    @classmethod
    def of(cls, theme: Theme, *parts: Element) -> Palette:
        """The palette of the master and the layout and slide that may override its mapping."""
        mapping = dict(_DEFAULT_MAP)
        for part in parts:
            clr_map = part.find(p("clrMap"))
            if clr_map is None:
                clr_map = part.find(f"{p('clrMapOvr')}/{a('overrideClrMapping')}")
            if clr_map is not None:
                mapping.update({str(k): str(v) for k, v in clr_map.attrib.items()})
        return cls(theme, {str(k): str(v) for k, v in mapping.items()})

    def scheme(self, name: str) -> str | None:
        name = self.mapping.get(name, name)
        return self.theme.scheme.get(name)

    def color_named(self, name: str) -> Color | None:
        """The colour of a scheme name (``tx1``, ``accent1`` …) under this mapping."""
        rgb = self.scheme(name)
        return Color(rgb) if rgb else None

    def color(self, holder: Element | None, placeholder: Color | None = None) -> Color | None:
        """The colour in ``holder`` (``a:solidFill``, ``a:buClr``, a gradient stop …: an
        element whose child is a colour), with its modifiers; ``phClr`` is ``placeholder``."""
        if holder is None:
            return None
        value = next((c for c in holder if local(c) in COLOR_TAGS), None)
        if value is None:
            return None
        return self.value(value, placeholder)

    def value(self, value: Element, placeholder: Color | None = None) -> Color | None:
        kind = local(value)
        rgb: str | None = None
        alpha = 1.0
        if kind == "srgbClr":
            rgb = value.get("val")
        elif kind == "schemeClr":
            name = value.get("val", "")
            if name == "phClr":
                if placeholder is None:
                    return None
                rgb, alpha = placeholder.rgb, placeholder.alpha
            else:
                rgb = self.scheme(name)
        elif kind == "sysClr":
            rgb = value.get("lastClr")
        elif kind == "prstClr":
            channels = _PRESET_COLORS.get(value.get("val", ""))
            rgb = "".join(f"{c:02X}" for c in channels) if channels else None
        elif kind == "scrgbClr":
            channels = (integer(value, n) / 100000 for n in ("r", "g", "b"))
            rgb = "".join(f"{round(max(0.0, min(1.0, c)) * 255):02X}" for c in channels)
        elif kind == "hslClr":
            hue = integer(value, "hue") / 60000 / 360
            red, green, blue = colorsys.hls_to_rgb(
                hue, integer(value, "lum") / 100000, integer(value, "sat") / 100000
            )
            rgb = "".join(f"{round(c * 255):02X}" for c in (red, green, blue))
        if not rgb or len(rgb) != 6:
            return None
        return modified(Color(rgb.upper(), alpha), value)


def modified(color: Color, value: Element) -> Color:
    """``color`` with the modifiers of the colour element ``value`` (``lumMod``, ``shade`` …)."""
    red, green, blue = (int(color.rgb[i : i + 2], 16) / 255 for i in (0, 2, 4))
    alpha = color.alpha
    for modifier in value:
        kind = local(modifier)
        amount = integer(modifier, "val") / 100000
        if kind in ("lumMod", "lumOff", "satMod"):
            hue, lum, sat = colorsys.rgb_to_hls(red, green, blue)
            if kind == "lumMod":
                lum *= amount
            elif kind == "lumOff":
                lum += amount
            else:
                sat *= amount
            red, green, blue = colorsys.hls_to_rgb(
                hue, max(0.0, min(1.0, lum)), max(0.0, min(1.0, sat))
            )
        elif kind == "shade":
            red, green, blue = red * amount, green * amount, blue * amount
        elif kind == "tint":
            red, green, blue = (c + (1 - c) * (1 - amount) for c in (red, green, blue))
        elif kind == "alpha":
            alpha = amount
        elif kind == "alphaMod":
            alpha *= amount
    rgb = "".join(f"{round(max(0.0, min(1.0, c)) * 255):02X}" for c in (red, green, blue))
    return Color(rgb, alpha)
