"""The CSS of an SVG resolved to plain values: the cascade of its ``<style>`` rules and the
values of colours and lengths.

Port of DocLibs ``SvgStyle.cs`` (E06-S03), widened for the SVG mermaid-cli writes: its colours
stand in a ``<style>`` with selectors (``#id .node rect { … }``), partly as ``rgb()``/``hsl()``.
``Cascade`` applies the rules by specificity (selectors through ``cssselect``, extra
``diagrams``), then the ``style`` attribute, then presentation attributes. ``SvgStyle`` resolves
values: custom properties and ``var()`` with fallbacks, ``color-mix(in srgb, …)``, hex colours,
``rgb()``/``rgba()``, ``hsl()``/``hsla()``, CSS colour names, and ``px``/``pt``/``em``/``rem``
lengths. Anything else raises ``SvgDrawingError``, so a change in the SVG fails loudly instead
of drawing wrong colours.
"""

from __future__ import annotations

import colorsys
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Final

from lxml import etree
from PIL import ImageColor

from pta_documents.drawing.svg_geometry import SvgDrawingError

ROOT_FONT_SIZE: Final = 16.0
"""The size ``rem`` (and, without a font size, ``em``) refers to, in pixels."""
POINT: Final = 4 / 3
"""Pixels per point."""
IGNORED_AT_RULES: Final = frozenset({"keyframes", "font-face", "import"})
"""At-rules that hold nothing a still drawing shows; any other at-rule raises."""

_NUMBER: Final = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
_LENGTH: Final = re.compile(rf"^({_NUMBER})\s*(px|pt|rem|em)?$")
_HEX_COLOR: Final = re.compile(r"^[0-9A-F]{6}$")
_HEX_DIGITS: Final = re.compile(r"^[0-9A-Fa-f]+$")
_MIX_ARGUMENT: Final = re.compile(rf"^(.*\S)\s+({_NUMBER})%$")
_IMPORTANT: Final = re.compile(r"\s*!\s*important\s*$", re.IGNORECASE)
_COMMENT: Final = re.compile(r"/\*.*?\*/", re.DOTALL)

type Color = tuple[str, float]
"""A colour as ``RRGGBB`` and its alpha (0 … 1)."""


def unsupported(kind: str, value: str) -> SvgDrawingError:
    return SvgDrawingError(f"The diagram's SVG has the {kind} '{value}', which cannot be drawn.")


@dataclass(slots=True)
class SvgStyle:
    """Resolves CSS values: custom properties, ``var()``, colours and lengths."""

    properties: dict[str, str] = field(default_factory=dict[str, str])
    gradients: dict[str, str] = field(default_factory=dict[str, str])
    """Colours of gradients by id, for ``url(#id)``: drawings have no gradients, so the first
    stop stands in."""

    @staticmethod
    def read(root_style: str | None, style_sheet: str | None) -> SvgStyle:
        """The custom properties of the ``svg`` rules of ``style_sheet`` and of
        ``root_style``."""
        style = SvgStyle()
        for rule in _rules(style_sheet or ""):
            if any(selector.strip() == "svg" for selector in _split_top_level(rule.selectors, ",")):
                style._declarations(rule.block)
        style._declarations(root_style or "")
        return style

    def color(self, value: str) -> str | None:
        """A colour as ``RRGGBB``, mixed with white when translucent; None for ``none`` and
        ``transparent``."""
        resolved = self.paint(value)
        if resolved is None:
            return None
        color, alpha = resolved
        return on_white(color, alpha)

    def paint(self, value: str, current: Color | None = None) -> Color | None:
        """A colour and its alpha; None for ``none`` and ``transparent``. ``current`` is the
        value of ``currentColor``."""
        evaluated = self._evaluate(value.strip(), 0)
        if evaluated is None:
            return None
        if evaluated.lower() == "currentcolor":
            if current is None:
                raise unsupported("colour", value)
            return current
        parsed = _color_function(evaluated)
        if parsed is not None:
            return None if parsed[1] <= 0 else parsed
        if _HEX_COLOR.match(evaluated):
            return evaluated, 1.0
        suffix = "" if evaluated == value else f" (resolved to '{evaluated}')"
        raise unsupported("colour", value + suffix)

    def length(self, value: str, font_size: float = ROOT_FONT_SIZE) -> float:
        """A length in pixels; ``em`` refers to ``font_size``."""
        resolved = self._evaluate(value.strip(), 0)
        match = _LENGTH.match(resolved) if resolved is not None else None
        if match is None:
            raise unsupported("length", value)
        number = float(match.group(1))
        match match.group(2):
            case "rem":
                return number * ROOT_FONT_SIZE
            case "em":
                return number * font_size
            case "pt":
                return number * POINT
            case _:
                return number

    def _declarations(self, block: str) -> None:
        for name, value, _ in declarations(block):
            if name.startswith("--"):
                self.properties[name] = value

    def _evaluate(self, value: str, depth: int) -> str | None:
        """``value`` with ``var()``, ``color-mix()``, ``url()`` and hex colours replaced; None
        for ``none`` and ``transparent``."""
        if depth > 32:
            raise unsupported(
                "value", value + " (the custom properties refer to each other in a cycle)"
            )
        if value.lower() in ("none", "transparent"):
            return None
        variable = _function(value, "var")
        if variable is not None:
            arguments = _split_top_level(variable, ",", limit=2)
            name = arguments[0].strip()
            if name in self.properties:
                return self._evaluate(self.properties[name], depth + 1)
            if len(arguments) > 1:
                return self._evaluate(arguments[1].strip(), depth + 1)
            raise unsupported("value", f"{value} ('{name}' is not defined)")
        mix = _function(value, "color-mix")
        if mix is not None:
            return self._mix(value, mix, depth)
        url = _function(value, "url")
        if url is not None:
            target = url.strip().strip("'\"")
            if target.startswith("#") and target[1:] in self.gradients:
                return self._evaluate(self.gradients[target[1:]], depth + 1)
            raise unsupported("paint", value)
        if value.startswith("#"):
            hex_color = _hex(value)
            if hex_color is None:
                raise unsupported("colour", value)
            return hex_color
        color_name = named(value)
        return color_name if color_name is not None else value

    def _mix(self, value: str, arguments: str, depth: int) -> str:
        """``color-mix(in srgb, A p%, B q%)``: a missing percentage is the rest of 100, both
        missing are 50 % each."""
        parts = _split_top_level(arguments, ",")
        if len(parts) != 3 or parts[0].strip() != "in srgb":
            raise unsupported("colour", value)
        first, p1 = self._mix_part(parts[1], value, depth)
        second, p2 = self._mix_part(parts[2], value, depth)
        if p1 is not None and p2 is not None and p1 + p2 > 0:
            share = p1 / (p1 + p2)
        elif p1 is not None and p2 is None:
            share = p1
        elif p1 is None and p2 is not None:
            share = 1 - p2
        else:
            share = 0.5

        def channel(color: str, index: int) -> int:
            return int(color[index * 2 : index * 2 + 2], 16)

        return "".join(
            f"{_round(channel(first, i) * share + channel(second, i) * (1 - share)):02X}"
            for i in range(3)
        )

    def _mix_part(self, part: str, value: str, depth: int) -> tuple[str, float | None]:
        match = _MIX_ARGUMENT.match(part.strip())
        color = self._evaluate(match.group(1) if match else part.strip(), depth + 1)
        if color is None or not _HEX_COLOR.match(color):
            raise unsupported("colour", value)
        return color, float(match.group(2)) / 100 if match else None


def on_white(color: str, alpha: float) -> str | None:
    """``color`` at ``alpha`` over white: drawings have no transparency."""
    if alpha >= 1:
        return color
    if alpha <= 0:
        return None

    def channel(index: int) -> int:
        return _round(255 - (255 - int(color[index * 2 : index * 2 + 2], 16)) * alpha)

    return "".join(f"{channel(i):02X}" for i in range(3))


def _round(value: float) -> int:
    """Rounded half away from zero, as .NET's ``MidpointRounding.AwayFromZero``."""
    return int(value + 0.5) if value >= 0 else -int(-value + 0.5)


def _hex(value: str) -> str | None:
    digits = value[1:]
    if not _HEX_DIGITS.match(digits):
        return None
    match len(digits):
        case 3 | 4:
            return "".join(c.upper() * 2 for c in digits[:3])
        case 6 | 8:
            return digits[:6].upper()
        case _:
            return None


def named(value: str) -> str | None:
    """A CSS colour name as ``RRGGBB``."""
    name = value.lower()
    if name not in ImageColor.colormap:
        return None
    red, green, blue = ImageColor.getrgb(name)[:3]
    return f"{red:02X}{green:02X}{blue:02X}"


def _color_function(value: str) -> Color | None:
    """``rgb()``, ``rgba()``, ``hsl()`` or ``hsla()``, with commas or spaces and ``/ alpha``;
    None for any other value."""
    match = re.fullmatch(r"(rgba?|hsla?)\((.*)\)", value.strip(), re.IGNORECASE)
    if match is None:
        return None
    name = match.group(1).lower()
    body = match.group(2).replace("/", " / ")
    parts = [p for p in re.split(r"[\s,]+", body.strip()) if p]
    alpha = 1.0
    if "/" in parts:
        slash = parts.index("/")
        if slash != 3 or len(parts) != 5:
            raise unsupported("colour", value)
        alpha = _fraction(parts[4], value)
        parts = parts[:3]
    elif len(parts) == 4:
        alpha = _fraction(parts[3], value)
        parts = parts[:3]
    if len(parts) != 3:
        raise unsupported("colour", value)
    if name.startswith("rgb"):
        channels = [_channel(p, value) for p in parts]
    else:
        hue = _plain(parts[0].removesuffix("deg"), value) % 360 / 360
        saturation = _fraction(parts[1], value, percent=True)
        lightness = _fraction(parts[2], value, percent=True)
        red, green, blue = colorsys.hls_to_rgb(hue, lightness, saturation)
        channels = [_round(c * 255) for c in (red, green, blue)]
    return "".join(f"{min(255, max(0, c)):02X}" for c in channels), min(1.0, max(0.0, alpha))


def _plain(text: str, value: str) -> float:
    if not re.fullmatch(_NUMBER, text):
        raise unsupported("colour", value)
    return float(text)


def _channel(text: str, value: str) -> int:
    if text.endswith("%"):
        return _round(_plain(text[:-1], value) * 2.55)
    return _round(_plain(text, value))


def _fraction(text: str, value: str, *, percent: bool = False) -> float:
    """A share 0 … 1 from ``50%`` or ``0.5``; with ``percent`` the ``%`` is required."""
    if text.endswith("%"):
        return min(1.0, max(0.0, _plain(text[:-1], value) / 100))
    if percent:
        raise unsupported("colour", value)
    return min(1.0, max(0.0, _plain(text, value)))


def _function(value: str, name: str) -> str | None:
    """The arguments of ``name( … )`` when the value is exactly that call."""
    if not (value.startswith(name + "(") and value.endswith(")")):
        return None
    depth = 0
    for i in range(len(name), len(value)):
        depth += {"(": 1, ")": -1}.get(value[i], 0)
        if depth == 0:
            return value[len(name) + 1 : -1] if i == len(value) - 1 else None
    return None


def _split_top_level(text: str, separator: str, limit: int = 1 << 30) -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0
    for i, character in enumerate(text):
        depth += {"(": 1, ")": -1}.get(character, 0)
        if character == separator and depth == 0 and len(parts) < limit - 1:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return [p for p in parts if p.strip() or separator == ","]


def declarations(block: str) -> Iterator[tuple[str, str, bool]]:
    """The declarations of a CSS block or ``style`` attribute: name (lower case for all but
    custom properties), value without ``!important``, and whether it was important."""
    for declaration in _split_top_level(block, ";"):
        name, colon, value = declaration.partition(":")
        name = name.strip()
        if not colon or not name:
            continue
        important = bool(_IMPORTANT.search(value))
        value = _IMPORTANT.sub("", value).strip()
        yield (name if name.startswith("--") else name.lower()), value, important


@dataclass(frozen=True, slots=True)
class _Rule:
    selectors: str
    block: str


def _rules(style_sheet: str) -> Iterator[_Rule]:
    """The style rules of a style sheet, in order; ignored at-rules are skipped, others raise."""
    text = _COMMENT.sub("", style_sheet)
    i = 0
    while i < len(text):
        open_brace = text.find("{", i)
        semicolon = text.find(";", i)
        prelude_end = open_brace if open_brace >= 0 else len(text)
        prelude = text[i:prelude_end].strip()
        if prelude.startswith("@") and 0 <= semicolon < prelude_end:
            # A statement at-rule such as @import: no block.
            _check_at_rule(text[i:semicolon].strip())
            i = semicolon + 1
            continue
        if open_brace < 0:
            if text[i:].strip():
                raise unsupported("CSS", text[i:].strip()[:60])
            return
        end = _block_end(text, open_brace)
        if prelude.startswith("@"):
            _check_at_rule(prelude)
        elif prelude:
            yield _Rule(prelude, text[open_brace + 1 : end])
        i = end + 1


def _check_at_rule(prelude: str) -> None:
    name = re.match(r"@([-\w]+)", prelude)
    if name is None or name.group(1).lower() not in IGNORED_AT_RULES:
        raise unsupported("CSS at-rule", prelude[:60])


def _block_end(text: str, open_brace: int) -> int:
    """The index of the brace closing the block that opens at ``open_brace``."""
    depth = 0
    for i in range(open_brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    raise unsupported("CSS", text[open_brace:][:60])


type _Specificity = tuple[int, int, int]
type _Declared = tuple[bool, _Specificity, int, str]
"""Whether important, the selector's specificity, the rule's order, the value."""

_ALWAYS_POSITIVE: Final = frozenset({"stroke-width", "font-size"})
"""Properties for which a negative number is invalid, so the declaration is dropped as CSS
drops it."""


def _valid(name: str, value: str) -> bool:
    if name in _ALWAYS_POSITIVE:
        match = _LENGTH.match(value.strip())
        return match is None or float(match.group(1)) >= 0
    return True


class Cascade:
    """The declared value of each property of each element: ``<style>`` rules by importance,
    specificity and order, the ``style`` attribute, then the presentation attribute.

    The tree's elements must have their SVG names without namespace (``rect``), so that type
    selectors match.
    """

    def __init__(self, root: etree._Element, style_sheet: str) -> None:
        self._declared: dict[etree._Element, dict[str, _Declared]] = {}
        order = 0
        rules = list(_rules(style_sheet))
        if not rules:
            return
        for rule in rules:
            for selector, specificity, select in _selectors(rule.selectors):
                try:
                    matched = select(root)
                except Exception as error:  # an XPath cssselect writes that lxml cannot run
                    raise unsupported("CSS selector", selector) from error
                for name, value, important in declarations(rule.block):
                    order += 1
                    if not value or not _valid(name, value):
                        continue
                    entry: _Declared = (important, specificity, order, value)
                    for element in matched:
                        own = self._declared.setdefault(element, {})
                        if name not in own or entry[:3] > own[name][:3]:
                            own[name] = entry

    def value(self, element: etree._Element, name: str) -> str | None:
        """The declared value of ``name`` on ``element``, trimmed; None if not declared."""
        rule = self._declared.get(element, {}).get(name)
        inline: tuple[str, bool] | None = None
        style = element.get("style")
        if style:
            for key, value, important in declarations(style):
                if key == name and value and _valid(name, value):
                    inline = (value, important)
        if inline is not None and inline[1]:
            return inline[0]
        if rule is not None and rule[0]:
            return rule[3]
        if inline is not None:
            return inline[0]
        if rule is not None:
            return rule[3]
        attribute = element.get(name)
        # An empty attribute is no value: the property is inherited as if it were missing.
        return attribute.strip() if attribute is not None and attribute.strip() else None


def _selectors(
    group: str,
) -> Iterator[tuple[str, _Specificity, Callable[[etree._Element], list[etree._Element]]]]:
    """Each selector of a selector list, its specificity and a function finding its elements;
    selectors with a pseudo-element are left out (nothing a drawing shows)."""
    try:
        import cssselect
    except ImportError as error:
        raise SvgDrawingError(
            "Reading the CSS of a diagram's SVG needs the extra 'diagrams' (cssselect): "
            "pip install 'pta-documents[diagrams]'."
        ) from error
    translator = cssselect.GenericTranslator()
    try:
        parsed = cssselect.parse(group)
    except cssselect.SelectorError as error:
        raise unsupported("CSS selector", group.strip()[:80]) from error
    for selector in parsed:
        if selector.pseudo_element is not None:
            continue
        try:
            xpath = etree.XPath(
                translator.selector_to_xpath(selector, prefix="descendant-or-self::")
            )
        except (cssselect.SelectorError, etree.XPathError) as error:
            raise unsupported("CSS selector", group.strip()[:80]) from error

        def select(root: etree._Element, xpath: etree.XPath = xpath) -> list[etree._Element]:
            result = xpath(root)
            assert isinstance(result, list)
            return [e for e in result if isinstance(e, etree._Element)]

        a, b, c = selector.specificity()
        yield group.strip(), (a, b, c), select
