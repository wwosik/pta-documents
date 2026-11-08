"""Text bodies of DrawingML as HTML: paragraphs with their levels, bullets and runs.

Paragraph and run properties are inherited the way PowerPoint inherits them — the presentation's
default text style, the master's title, body or other style, the list styles of the master's and
the layout's placeholder, the shape's own list style, then the paragraph and the run. Sizes are
points on a 1600 px stage; ``normAutofit`` shrinks them as PowerPoint does. All text is escaped:
nothing of the Markdown reaches the page as markup.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from html import escape
from typing import Final

from pta_documents.design import fonts
from pta_documents.generation.html.ooxml import (
    Color,
    Element,
    Palette,
    Units,
    a,
    integer,
    local,
    number,
    r,
)

LINE_HEIGHT: Final = 1.33
"""Single line spacing of Segoe UI (and the metrically equal Selawik) in em: Windows ascent and
descent, (2210 + 514) / 2048 — PowerPoint's "single" for this font."""
MONO_LINE_HEIGHT: Final = 1.17
"""Single line spacing of Consolas in em (Windows ascent and descent, (1884 + 514) / 2048)."""
DEFAULT_SIZE_PT: Final = 18.0
DEFAULT_INSETS: Final = (91440, 45720, 91440, 45720)
"""left, top, right, bottom of ``a:bodyPr`` without its own (0.25 cm and 0.13 cm)."""
SAFE_SCHEMES: Final = ("http://", "https://", "mailto:")
"""Links in the deck lead only here; any other target is shown as plain text."""
WINGDINGS: Final = {
    "§": "▪",
    "l": "●",
    "n": "■",
    "q": "❑",
    "u": "◆",
    "v": "❖",
    "Ø": "➢",
    "ü": "✓",
    "Ÿ": "•",
}
"""Wingdings bullets as the Unicode characters they show."""
_BULLET_PARTS: Final = {
    "buClrTx": "color",
    "buClr": "color",
    "buSzTx": "size",
    "buSzPct": "size",
    "buSzPts": "size",
    "buFontTx": "font",
    "buFont": "font",
    "buNone": "type",
    "buAutoNum": "type",
    "buChar": "type",
    "buBlip": "type",
}
_PARAGRAPH_PARTS: Final = {"lnSpc": "lnSpc", "spcBef": "spcBef", "spcAft": "spcAft"}
_BLACK: Final = "0" * 6
_RUN_PARTS: Final = {
    "noFill": "fill",
    "solidFill": "fill",
    "gradFill": "fill",
    "latin": "latin",
    "highlight": "highlight",
    "hlinkClick": "link",
}


@dataclass
class RunProps:
    attributes: dict[str, str] = field(default_factory=dict[str, str])
    parts: dict[str, Element] = field(default_factory=dict[str, Element])

    def merge(self, r_pr: Element | None) -> RunProps:
        result = RunProps(dict(self.attributes), dict(self.parts))
        if r_pr is None:
            return result
        result.attributes.update({str(k): str(v) for k, v in r_pr.attrib.items()})
        for child in r_pr:
            part = _RUN_PARTS.get(local(child))
            if part is not None:
                result.parts[part] = child
        return result


@dataclass
class ParagraphProps:
    attributes: dict[str, str] = field(default_factory=dict[str, str])
    parts: dict[str, Element] = field(default_factory=dict[str, Element])
    run: RunProps = field(default_factory=RunProps)

    def merge(self, p_pr: Element | None) -> ParagraphProps:
        result = ParagraphProps(dict(self.attributes), dict(self.parts), self.run)
        if p_pr is None:
            return result
        result.attributes.update({str(k): str(v) for k, v in p_pr.attrib.items()})
        for child in p_pr:
            name = local(child)
            part = _PARAGRAPH_PARTS.get(name) or _BULLET_PARTS.get(name)
            if part is not None:
                result.parts[part] = child
            elif name == "defRPr":
                result.run = result.run.merge(child)
        return result


@dataclass(frozen=True)
class TextStyles:
    """The list styles a text body inherits, the outermost first (``a:lstStyle``, a master's
    ``p:titleStyle`` …, all with ``a:lvlNpPr`` children)."""

    styles: tuple[Element, ...]

    def level(self, level: int) -> ParagraphProps:
        props = ParagraphProps()
        for style in self.styles:
            props = props.merge(style.find(a("defPPr")))
            props = props.merge(style.find(a(f"lvl{level + 1}pPr")))
        return props


@dataclass
class TextContext:
    units: Units
    palette: Palette
    link: Callable[[str], str | None]
    """The target of a relationship id (``r:id`` of ``a:hlinkClick``)."""
    image: Callable[[str], str | None]
    """The CSS class of the image of a relationship id (a picture bullet)."""
    font_color: Color | None = None
    """The colour of ``p:style/a:fontRef``: the text colour unless the text has its own."""
    builds: dict[int, int] = field(default_factory=dict[int, int])
    """Paragraph index -> the build step it appears on (E09-S02)."""
    effects: dict[int, str] = field(default_factory=dict[int, str])
    """Paragraph index -> its build effect."""


@dataclass(frozen=True)
class BodyLayout:
    """Insets (px), vertical anchor, wrapping and the shrink of ``normAutofit``."""

    insets: tuple[float, float, float, float]
    anchor: str
    wrap: bool
    font_scale: float
    spacing_reduction: float


def body_layout(body_prs: Sequence[Element], units: Units) -> BodyLayout:
    """The ``a:bodyPr`` of a text body over those it inherits (outermost first)."""
    attributes: dict[str, str] = {}
    for body_pr in body_prs:
        attributes.update({str(k): str(v) for k, v in body_pr.attrib.items()})
    insets = tuple(
        units.px(int(attributes.get(name, str(default))))
        for name, default in zip(("lIns", "tIns", "rIns", "bIns"), DEFAULT_INSETS, strict=True)
    )
    scale, reduction = 1.0, 0.0
    own = body_prs[-1] if body_prs else None
    autofit = own.find(a("normAutofit")) if own is not None else None
    if autofit is not None:
        scale = integer(autofit, "fontScale", 100000) / 100000
        reduction = integer(autofit, "lnSpcReduction", 0) / 100000
    return BodyLayout(
        (insets[0], insets[1], insets[2], insets[3]),
        attributes.get("anchor", "t"),
        attributes.get("wrap", "square") != "none",
        scale,
        reduction,
    )


def css_family(typeface: str) -> tuple[str, int | None]:
    """The CSS font family of a typeface and the weight it implies (Segoe UI Light: 300)."""
    lower = typeface.lower()
    if lower in ("segoe ui light", "segoe ui semilight"):
        return fonts.CSS_FAMILY, 300
    if lower == "segoe ui semibold":
        return fonts.CSS_FAMILY, 600
    if lower in ("segoe ui", ""):
        return fonts.CSS_FAMILY, None
    if lower in ("consolas", "courier new", "inconsolata"):
        return fonts.CSS_MONO_FAMILY, None
    if lower == "georgia":
        return fonts.CSS_QUOTE_FAMILY, None
    return f'"{typeface}", {fonts.CSS_FAMILY}', None


def html_text(
    tx_body: Element,
    styles: TextStyles,
    layout: BodyLayout,
    context: TextContext,
) -> str:
    """The paragraphs of ``tx_body`` (``p:txBody`` or ``a:txBody``) as HTML."""
    own = tx_body.find(a("lstStyle"))
    styles = TextStyles((*styles.styles, own)) if own is not None else styles
    parts: list[str] = []
    numbers: dict[int, int] = {}
    for index, paragraph in enumerate(tx_body.iterfind(a("p"))):
        p_pr = paragraph.find(a("pPr"))
        level = integer(p_pr, "lvl", 0)
        props = styles.level(level).merge(p_pr)
        parts.append(_paragraph(paragraph, props, layout, context, index, numbers, level))
    return "".join(parts)


def _size_pt(run: RunProps, scale: float) -> float:
    size = run.attributes.get("sz")
    return (int(size) / 100 if size and size.isdigit() else DEFAULT_SIZE_PT) * scale


def _paragraph(
    paragraph: Element,
    props: ParagraphProps,
    layout: BodyLayout,
    context: TextContext,
    index: int,
    numbers: dict[int, int],
    level: int,
) -> str:
    units = context.units
    elements = [c for c in paragraph if local(c) in ("r", "br", "fld")]
    runs = [props.run.merge(e.find(a("rPr"))) for e in elements]
    end = props.run.merge(paragraph.find(a("endParaRPr")))
    first = runs[0] if runs else end
    size_pt = max((_size_pt(run, layout.font_scale) for run in runs), default=0.0)
    size_pt = size_pt or _size_pt(end, layout.font_scale)
    styles: list[str] = [f"font-size:{number(units.pt(size_pt))}px"]
    margin = units.px(int(props.attributes.get("marL", "0") or 0))
    indent = units.px(int(props.attributes.get("indent", "0") or 0))
    align = {"ctr": "center", "r": "right", "just": "justify", "dist": "justify"}.get(
        props.attributes.get("algn", "l"), "left"
    )
    if align != "left":
        styles.append(f"text-align:{align}")
    latin = first.parts.get("latin")
    family, _ = css_family(
        context.palette.theme.font(latin.get("typeface", "") if latin is not None else "")
    )
    factor = MONO_LINE_HEIGHT if family == fonts.CSS_MONO_FAMILY else LINE_HEIGHT
    styles.append(f"line-height:{_line_height(props, layout, units, factor)}")
    before = _spacing(props.parts.get("spcBef"), size_pt, units)
    after = _spacing(props.parts.get("spcAft"), size_pt, units)
    if before and index > 0:
        # PowerPoint leaves out the space before the first paragraph of a text body.
        styles.append(f"margin-top:{number(before)}px")
    if after:
        styles.append(f"margin-bottom:{number(after)}px")
    bullet = _bullet(props, first, layout, context, numbers, level, margin + indent)
    if not bullet:
        numbers.pop(level, None)
    if margin:
        styles.append(f"padding-left:{number(margin)}px")
    if not bullet and indent:
        styles.append(f"text-indent:{number(indent)}px")
    if not layout.wrap:
        styles.append("white-space:pre")
    attributes = f' style="{";".join(styles)}"'
    if index in context.builds:
        effect = context.effects.get(index, "fade")
        attributes += f' data-build="{context.builds[index]}" data-effect="{effect}"'
    content = "".join(
        _run(element, run, layout, context) for element, run in zip(elements, runs, strict=True)
    )
    if not content or (elements and local(elements[-1]) == "br"):
        # An empty paragraph, or a line break at its end: one more line as high as its text.
        content += f'<span style="{_run_style(end, layout, context)}">&#8203;</span>'
    return f'<p class="pa"{attributes}>{bullet}{content}</p>'


def _line_height(props: ParagraphProps, layout: BodyLayout, units: Units, factor: float) -> str:
    spacing = props.parts.get("lnSpc")
    if spacing is not None and len(spacing):
        value = spacing[0]
        if local(value) == "spcPts":
            points = integer(value, "val") / 100 * layout.font_scale
            return f"{number(units.pt(points))}px"
        share = integer(value, "val", 100000) / 100000 - layout.spacing_reduction
        return number(max(share, 0.1) * factor)
    return number(max(1.0 - layout.spacing_reduction, 0.1) * factor)


def _spacing(spacing: Element | None, size_pt: float, units: Units) -> float:
    if spacing is None or not len(spacing):
        return 0.0
    value = spacing[0]
    if local(value) == "spcPts":
        return units.pt(integer(value, "val") / 100)
    return units.pt(size_pt * LINE_HEIGHT * integer(value, "val") / 100000)


_AUTO_NUMBERS: Final = {
    "arabicPeriod": ("1", "."),
    "arabicParenR": ("1", ")"),
    "arabicParenBoth": ("1", ")"),
    "arabicPlain": ("1", ""),
    "alphaLcPeriod": ("a", "."),
    "alphaUcPeriod": ("A", "."),
    "alphaLcParenR": ("a", ")"),
    "romanLcPeriod": ("i", "."),
    "romanUcPeriod": ("I", "."),
}


def _counter(value: int, kind: str) -> str:
    if kind in ("a", "A"):
        text = ""
        while value > 0:
            value, rest = divmod(value - 1, 26)
            text = chr(ord("a") + rest) + text
        return text.upper() if kind == "A" else text
    if kind in ("i", "I"):
        numerals = (
            (1000, "m"),
            (900, "cm"),
            (500, "d"),
            (400, "cd"),
            (100, "c"),
            (90, "xc"),
            (50, "l"),
            (40, "xl"),
            (10, "x"),
            (9, "ix"),
            (5, "v"),
            (4, "iv"),
            (1, "i"),
        )
        text = ""
        for amount, numeral in numerals:
            while value >= amount:
                text += numeral
                value -= amount
        return text.upper() if kind == "I" else text
    return str(value)


def _bullet(
    props: ParagraphProps,
    first: RunProps,
    layout: BodyLayout,
    context: TextContext,
    numbers: dict[int, int],
    level: int,
    left: float,
) -> str:
    """The bullet of a paragraph, placed at ``left`` px (``marL`` + ``indent``)."""
    kind = props.parts.get("type")
    if kind is None or local(kind) == "buNone":
        return ""
    size_pt = _size_pt(first, layout.font_scale)
    size = props.parts.get("size")
    if size is not None and local(size) == "buSzPct":
        size_pt *= integer(size, "val", 100000) / 100000
    elif size is not None and local(size) == "buSzPts":
        size_pt = integer(size, "val") / 100 * layout.font_scale
    styles = [f"left:{number(left)}px", f"font-size:{number(context.units.pt(size_pt))}px"]
    color_part = props.parts.get("color")
    color = (
        context.palette.color(color_part)
        if color_part is not None and local(color_part) == "buClr"
        else _run_color(first, context)
    )
    if color is not None:
        styles.append(f"color:{color.css()}")
    name = local(kind)
    if name == "buBlip":
        blip = kind.find(a("blip"))
        target = context.image(blip.get(r("embed"), "")) if blip is not None else None
        if target is None:
            return ""
        side = number(context.units.pt(size_pt))
        styles.append(f"width:{side}px;height:{side}px")
        return f'<span class="bu bi {target}" style="{";".join(styles)}" aria-hidden="true"></span>'
    if name == "buAutoNum":
        scheme = kind.get("type", "arabicPeriod")
        counter, suffix = _AUTO_NUMBERS.get(scheme, ("1", "."))
        start = integer(kind, "startAt", 1)
        value = numbers.get(level, start - 1) + 1
        numbers[level] = value
        for deeper in [k for k in numbers if k > level]:
            numbers.pop(deeper)
        text = _counter(value, counter) + suffix
        if scheme == "arabicParenBoth":
            text = "(" + text
    else:
        text = kind.get("char", "•")
        font_part = props.parts.get("font")
        typeface = font_part.get("typeface", "") if font_part is not None else ""
        if typeface.lower().startswith("wingdings"):
            text = WINGDINGS.get(text, "▪")
        elif font_part is not None and local(font_part) == "buFont":
            family, weight = css_family(typeface)
            styles.append(f"font-family:{escape(family)}")
            if weight:
                styles.append(f"font-weight:{weight}")
    return f'<span class="bu" style="{";".join(styles)}" aria-hidden="true">{escape(text)}</span>'


def _run_color(run: RunProps, context: TextContext) -> Color | None:
    fill = run.parts.get("fill")
    if fill is not None and local(fill) == "noFill":
        return Color(_BLACK, 0.0)
    if fill is not None and local(fill) == "solidFill":
        return context.palette.color(fill)
    if fill is not None and local(fill) == "gradFill":
        stop = fill.find(f"{a('gsLst')}/{a('gs')}")
        return context.palette.color(stop)
    return context.font_color


def _run_style(run: RunProps, layout: BodyLayout, context: TextContext) -> str:
    units = context.units
    styles = [f"font-size:{number(units.pt(_size_pt(run, layout.font_scale)))}px"]
    latin = run.parts.get("latin")
    typeface = context.palette.theme.font(latin.get("typeface", "") if latin is not None else "")
    if not typeface:
        typeface = context.palette.theme.minor_font
    family, weight = css_family(typeface)
    styles.append(f"font-family:{escape(family)}")
    bold = run.attributes.get("b") in ("1", "true")
    if bold:
        styles.append("font-weight:700")
    elif weight:
        styles.append(f"font-weight:{weight}")
    if run.attributes.get("i") in ("1", "true"):
        styles.append("font-style:italic")
    decorations: list[str] = []
    if run.attributes.get("u", "none") != "none":
        decorations.append("underline")
    if run.attributes.get("strike", "noStrike") != "noStrike":
        decorations.append("line-through")
    if decorations:
        styles.append(f"text-decoration:{' '.join(decorations)}")
    color = _run_color(run, context)
    if color is not None:
        styles.append(f"color:{color.css()}")
    highlight = context.palette.color(run.parts.get("highlight"))
    if highlight is not None:
        styles.append(f"background-color:{highlight.css()}")
    baseline = int(run.attributes.get("baseline", "0") or 0)
    if baseline:
        styles.append(f"vertical-align:{number(baseline / 1000)}%")
    cap = run.attributes.get("cap", "none")
    if cap == "all":
        styles.append("text-transform:uppercase")
    elif cap == "small":
        styles.append("font-variant:small-caps")
    return ";".join(styles)


def _run(element: Element, run: RunProps, layout: BodyLayout, context: TextContext) -> str:
    if local(element) == "br":
        return "<br>"
    text = "".join(t.text or "" for t in element.iter(a("t")))
    if not text:
        return ""
    style = _run_style(run, layout, context)
    link = run.parts.get("link")
    target = context.link(link.get(r("id"), "")) if link is not None else None
    content = escape(text).replace("\t", " ")
    if target is not None and target.lower().startswith(SAFE_SCHEMES):
        hlink = context.palette.scheme("hlink")
        if hlink is not None:
            style += f";color:{Color(hlink).css()}"
        external = target.lower().startswith(("http://", "https://"))
        extra = ' target="_blank" rel="noopener noreferrer"' if external else ""
        return f'<a href="{escape(target)}"{extra} style="{style}">{content}</a>'
    return f'<span style="{style}">{content}</span>'
