"""The shape trees of a slide, its layout and its master as absolutely placed HTML.

Each shape becomes a box at its place on the 1600 px stage: its outline and fill as inline SVG
(``geometry``), its text as HTML (``text``), a picture as a box whose background is the image
(once per document, ``ImageStore``), a table as an HTML table, a chart as the drawing of its data
(``charts``). Placeholders take place, outline, fill and text style from their layout and master
the way PowerPoint does; placeholders of layouts and masters are prompts and are not shown.
"""

from __future__ import annotations

import base64
import hashlib
import math
from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from html import escape
from typing import Any, Final

from pta_documents.design import logos
from pta_documents.design import slides as design
from pta_documents.generation.html import charts, geometry
from pta_documents.generation.html.ooxml import (
    ASVG,
    MC,
    Color,
    Element,
    Palette,
    Units,
    a,
    integer,
    local,
    number,
    p,
    r,
)
from pta_documents.generation.html.text import (
    BodyLayout,
    TextContext,
    TextStyles,
    body_layout,
    html_text,
)

SVG_BLIP: Final = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
"""The ``a:ext`` of a blip that carries the picture as SVG beside its PNG."""
TITLE_TYPES: Final = ("title", "ctrTitle")
OTHER_TYPES: Final = ("dt", "ftr", "sldNum", "hdr")
DEFAULT_LINE: Final = 9525
"""EMU of a line that names no width (0.75 pt)."""
WEB_IMAGES: Final = ("image/png", "image/jpeg", "image/gif", "image/svg+xml", "image/bmp")
METAFILES: Final = ("image/x-emf", "image/x-wmf")
_ARROWS: Final = ("triangle", "arrow", "stealth", "diamond", "oval")


class ImageStore:
    """Every image of the document once, as a CSS class with the image as ``data:`` URI."""

    def __init__(self) -> None:
        self.rules: dict[str, tuple[str, str]] = {}
        """sha256 -> (class, data URI)."""

    def add(self, content: bytes, content_type: str) -> str:
        key = hashlib.sha256(content).hexdigest()
        if key not in self.rules:
            uri = f"data:{content_type};base64,{base64.b64encode(content).decode('ascii')}"
            self.rules[key] = (f"im{len(self.rules) + 1}", uri)
        return self.rules[key][0]

    def css(self) -> str:
        return "".join(
            f".{name}{{background-image:url({uri})}}\n" for name, uri in self.rules.values()
        )


@dataclass(frozen=True)
class Layer:
    """A part with a shape tree: a slide, a layout or a master (python-pptx part)."""

    part: Any
    element: Element

    @property
    def tree(self) -> Element | None:
        return self.element.find(f"{p('cSld')}/{p('spTree')}")

    def related(self, r_id: str) -> Any | None:
        try:
            return self.part.related_part(r_id)
        except KeyError:
            return None

    def link(self, r_id: str) -> str | None:
        relation = self.part.rels.get(r_id)
        if relation is None or not relation.is_external:
            return None
        return str(relation.target_ref)


@dataclass(frozen=True)
class Transform:
    """Child coordinates (EMU) of a group to slide coordinates (EMU)."""

    x: float = 0.0
    y: float = 0.0
    sx: float = 1.0
    sy: float = 1.0

    def box(self, x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
        return self.x + x * self.sx, self.y + y * self.sy, w * self.sx, h * self.sy

    def inner(self, xfrm: Element) -> Transform:
        off, ext = xfrm.find(a("off")), xfrm.find(a("ext"))
        ch_off, ch_ext = xfrm.find(a("chOff")), xfrm.find(a("chExt"))
        ox, oy = integer(off, "x"), integer(off, "y")
        cx, cy = integer(ext, "cx"), integer(ext, "cy")
        chx, chy = integer(ch_off, "x"), integer(ch_off, "y")
        chcx, chcy = integer(ch_ext, "cx", cx), integer(ch_ext, "cy", cy)
        sx = cx / chcx if chcx else 1.0
        sy = cy / chcy if chcy else 1.0
        return Transform(
            self.x + (ox - chx * sx) * self.sx,
            self.y + (oy - chy * sy) * self.sy,
            self.sx * sx,
            self.sy * sy,
        )


@dataclass(frozen=True)
class Paint:
    """A fill: none, a colour, a gradient (stops and angle) or an image (relationship id)."""

    kind: str
    color: Color | None = None
    stops: tuple[tuple[float, Color], ...] = ()
    angle: float = 0.0
    radial: bool = False
    image: str | None = None
    owner: Layer | None = None
    """The part whose relationship ``image`` is (a layout's fill on a slide's placeholder)."""


NO_PAINT: Final = Paint("none")


@dataclass(frozen=True)
class Stroke:
    color: Color
    width: float
    """EMU."""
    dash: tuple[float, ...] = ()
    """Multiples of the width."""
    cap: str = "butt"
    head: str = "none"
    tail: str = "none"


@dataclass
class Builds:
    """What a slide builds (E09-S02): shape id -> (step, effect); paragraphs by shape."""

    shapes: dict[int, tuple[int, str]] = field(default_factory=dict[int, tuple[int, str]])
    paragraphs: dict[int, dict[int, tuple[int, str]]] = field(
        default_factory=dict[int, dict[int, tuple[int, str]]]
    )
    steps: int = 0


@dataclass
class Scene:
    """What drawing one slide needs: its layers, palette, images and builds."""

    units: Units
    palette: Palette
    images: ImageStore
    master: Layer
    layout: Layer
    slide: Layer
    defaults: Element | None
    """``p:defaultTextStyle`` of the presentation."""
    language: str
    layout_name: str = ""
    builds: Builds = field(default_factory=Builds)
    serial: list[int] = field(default_factory=lambda: [0])
    """A counter shared by the whole deck, for ids within inline SVG."""

    def next_id(self) -> str:
        self.serial[0] += 1
        return f"d{self.serial[0]}"


# ---------------------------------------------------------------------- placeholders


def placeholder(element: Element) -> Element | None:
    return element.find(f"*/{p('nvPr')}/{p('ph')}")


def _matches(ph: Element, wanted_type: str, wanted_idx: int, by_type: bool) -> bool:
    kind = ph.get("type", "obj")
    if by_type:
        if wanted_type in TITLE_TYPES:
            return kind in TITLE_TYPES
        if wanted_type in OTHER_TYPES:
            return kind == wanted_type
        return kind not in (*TITLE_TYPES, *OTHER_TYPES)
    return integer(ph, "idx", 0) == wanted_idx and (
        wanted_idx != 0 or (kind in TITLE_TYPES) == (wanted_type in TITLE_TYPES)
    )


def _find(layer: Layer, ph: Element, by_type: bool) -> Element | None:
    tree = layer.tree
    if tree is None:
        return None
    kind = ph.get("type", "obj")
    idx = integer(ph, "idx", 0)
    for element in tree.iter(p("sp"), p("pic"), p("graphicFrame")):
        other = placeholder(element)
        if other is not None and _matches(other, kind, idx, by_type):
            return element
    if not by_type and idx == 0:
        return _find(layer, ph, True)
    return None


def inherited(element: Element, scene: Scene, own: Layer) -> list[Element]:
    """The placeholders ``element`` inherits from, the outermost (master) first."""
    ph = placeholder(element)
    if ph is None:
        return []
    chain: list[Element] = []
    if own is scene.slide:
        layout_shape = _find(scene.layout, ph, by_type=ph.get("type") in OTHER_TYPES)
        if layout_shape is not None:
            chain.insert(0, layout_shape)
            layout_ph = placeholder(layout_shape)
            if layout_ph is not None:
                ph = layout_ph
    if own is not scene.master:
        master_shape = _find(scene.master, ph, by_type=True)
        if master_shape is not None:
            chain.insert(0, master_shape)
    return chain


def text_kind(element: Element, chain: list[Element]) -> str:
    """``title``, ``body`` or ``other``: which master style the text of a shape inherits."""
    ph = placeholder(element)
    if ph is None:
        return "other"
    kind = ph.get("type")
    for outer in reversed(chain):
        if kind is None:
            outer_ph = placeholder(outer)
            kind = outer_ph.get("type") if outer_ph is not None else None
    kind = kind or "obj"
    if kind in TITLE_TYPES:
        return "title"
    if kind in OTHER_TYPES:
        return "other"
    return "body"


# ---------------------------------------------------------------------- fills and lines


def paint(holder: Element | None, scene: Scene, group: Paint | None = None) -> Paint | None:
    """The fill among the children of ``holder``; None if it names none."""
    if holder is None:
        return None
    for child in holder:
        kind = local(child)
        if kind == "noFill":
            return NO_PAINT
        if kind == "solidFill":
            color = scene.palette.color(child)
            return Paint("solid", color) if color is not None else NO_PAINT
        if kind == "gradFill":
            stops: list[tuple[float, Color]] = []
            for stop in child.iterfind(f"{a('gsLst')}/{a('gs')}"):
                color = scene.palette.color(stop)
                if color is not None:
                    stops.append((integer(stop, "pos") / 100000, color))
            stops.sort(key=lambda s: s[0])
            linear = child.find(a("lin"))
            return Paint(
                "gradient",
                stops=tuple(stops),
                angle=integer(linear, "ang") / 60000 if linear is not None else 90.0,
                radial=child.find(a("path")) is not None,
            )
        if kind == "blipFill":
            blip = child.find(a("blip"))
            return Paint("image", image=blip.get(r("embed")) if blip is not None else None)
        if kind == "grpFill":
            return group or NO_PAINT
        if kind == "pattFill":
            color = scene.palette.color(child.find(a("fgClr")))
            return Paint("solid", color) if color is not None else NO_PAINT
    return None


def style_color(element: Element, ref: str, scene: Scene) -> tuple[int, Color | None]:
    """The index and colour of ``p:style/a:<ref>`` of a shape."""
    entry = element.find(f"{p('style')}/{a(ref)}")
    if entry is None:
        return 0, None
    return integer(entry, "idx"), scene.palette.color(entry)


def shape_paint(
    sp_prs: list[Element], element: Element, scene: Scene, group: Paint | None
) -> Paint:
    for sp_pr in reversed(sp_prs):
        found = paint(sp_pr, scene, group)
        if found is not None:
            if found.kind == "image":
                root = sp_pr.getroottree().getroot()
                owner = next(
                    (
                        layer
                        for layer in (scene.slide, scene.layout, scene.master)
                        if layer.element is root
                    ),
                    None,
                )
                return replace(found, owner=owner)
            return found
    index, color = style_color(element, "fillRef", scene)
    if index and color is not None:
        return Paint("solid", color)
    return NO_PAINT


def shape_stroke(sp_prs: list[Element], element: Element, scene: Scene) -> Stroke | None:
    lines = [ln for sp_pr in sp_prs if (ln := sp_pr.find(a("ln"))) is not None]
    index, style = style_color(element, "lnRef", scene)
    color: Color | None = style if index else None
    widths = scene.palette.theme.line_widths
    width = float(widths[index - 1]) if index and index <= len(widths) else float(DEFAULT_LINE)
    dash: tuple[float, ...] = ()
    cap = "butt"
    head = tail = "none"
    for ln in lines:
        if ln.get("w") is not None:
            width = float(integer(ln, "w"))
        fill = paint(ln, scene)
        if fill is not None:
            color = (
                fill.color
                if fill.kind == "solid"
                else (fill.stops[0][1] if fill.kind == "gradient" and fill.stops else None)
            )
        cap = {"rnd": "round", "sq": "square"}.get(ln.get("cap", ""), cap)
        preset_dash = ln.find(a("prstDash"))
        if preset_dash is not None:
            dash = _DASHES.get(preset_dash.get("val", "solid"), ())
        custom = ln.find(a("custDash"))
        if custom is not None:
            dash = tuple(
                v
                for ds in custom.iterfind(a("ds"))
                for v in (integer(ds, "d") / 100000, integer(ds, "sp") / 100000)
            )
        head_end, tail_end = ln.find(a("headEnd")), ln.find(a("tailEnd"))
        if head_end is not None:
            head = head_end.get("type", "none")
        if tail_end is not None:
            tail = tail_end.get("type", "none")
    if color is None or color.alpha <= 0 or width <= 0:
        return None
    return Stroke(color, width, dash, cap, head, tail)


_DASHES: Final = {
    "dash": (4.0, 3.0),
    "dashDot": (4.0, 3.0, 1.0, 3.0),
    "dot": (1.0, 3.0),
    "lgDash": (8.0, 3.0),
    "lgDashDot": (8.0, 3.0, 1.0, 3.0),
    "sysDash": (3.0, 1.0),
    "sysDot": (1.0, 1.0),
    "sysDashDot": (3.0, 1.0, 1.0, 1.0),
}


def css_background(fill: Paint, scene: Scene, layer: Layer) -> str:
    """A fill as CSS ``background`` (slide backgrounds)."""
    if fill.kind == "solid" and fill.color is not None:
        return f"background:{fill.color.css()}"
    if fill.kind == "gradient" and fill.stops:
        stops = ",".join(f"{c.css()} {number(pos * 100)}%" for pos, c in fill.stops)
        if fill.radial:
            return f"background:radial-gradient(circle,{stops})"
        return f"background:linear-gradient({number(fill.angle + 90)}deg,{stops})"
    if fill.kind == "image" and fill.image:
        css_class = _image_class(layer, fill.image, scene)
        if css_class:
            return f"--bg:{css_class}"
    return ""


def image_data(layer: Layer, r_id: str, scene: Scene) -> tuple[bytes, str] | None:
    """The bytes and type of the image ``r_id`` of ``layer`` as a browser shows it; None if it
    cannot.

    The PTA logos of the layouts are EMF, which no browser shows: the SVG logo that
    ``prepare-templates`` converted from them (E01-S04) takes their place — without slogan on
    the closing layout, with it elsewhere.
    """
    part = layer.related(r_id)
    if part is None:
        return None
    content_type = str(part.content_type)
    if content_type in METAFILES and layer is not scene.slide:
        closing = layer is scene.layout and scene.layout_name == design.LAYOUTS.closing
        logo = logos.Logo.SLIDES_PLAIN if closing else logos.Logo.SLIDES
        return logos.svg(logo), "image/svg+xml"
    if content_type not in WEB_IMAGES:
        return None
    return bytes(part.blob), content_type


def _image_class(layer: Layer, r_id: str, scene: Scene) -> str | None:
    data = image_data(layer, r_id, scene)
    return scene.images.add(*data) if data is not None else None


# ---------------------------------------------------------------------- shapes


def render_tree(tree: Element, layer: Layer, scene: Scene) -> str:
    """The shapes of ``tree`` (a shape tree) on ``layer``; placeholders only on slides."""
    return "".join(
        f"\n{html}" for html in _children(tree, layer, scene, Transform(), None, top=True)
    )


def _children(
    tree: Element, layer: Layer, scene: Scene, transform: Transform, group: Paint | None, top: bool
) -> Iterator[str]:
    for element in tree:
        kind = local(element)
        if kind == "AlternateContent" and element.tag == f"{{{MC}}}AlternateContent":
            fallback = element.find(f"{{{MC}}}Fallback")
            if fallback is not None:
                yield from _children(fallback, layer, scene, transform, group, top)
            continue
        if kind not in ("sp", "pic", "grpSp", "graphicFrame", "cxnSp"):
            continue
        c_nv_pr = element.find(f"*/{p('cNvPr')}")
        if c_nv_pr is not None and c_nv_pr.get("hidden") in ("1", "true"):
            continue
        if layer is not scene.slide and placeholder(element) is not None:
            continue
        html = _shape(element, kind, layer, scene, transform, group)
        if not html:
            continue
        if top and layer is scene.slide and c_nv_pr is not None:
            number_id = integer(c_nv_pr, "id", -1)
            build = scene.builds.shapes.get(number_id)
            if build is not None:
                html = html.replace(
                    "<div ", f'<div data-build="{build[0]}" data-effect="{build[1]}" ', 1
                )
        yield html


def _xfrm(element: Element, kind: str, chain: list[Element]) -> Element | None:
    def own(shape: Element) -> Element | None:
        if local(shape) == "graphicFrame":
            return shape.find(p("xfrm"))
        if local(shape) == "grpSp":
            return shape.find(f"{p('grpSpPr')}/{a('xfrm')}")
        return shape.find(f"{p('spPr')}/{a('xfrm')}")

    for shape in (element, *reversed(chain)):
        xfrm = own(shape)
        if xfrm is not None and xfrm.find(a("off")) is not None:
            return xfrm
    return None


def _box(xfrm: Element, transform: Transform) -> tuple[float, float, float, float]:
    off, ext = xfrm.find(a("off")), xfrm.find(a("ext"))
    return transform.box(
        integer(off, "x"), integer(off, "y"), integer(ext, "cx"), integer(ext, "cy")
    )


def _position(
    box: tuple[float, float, float, float], xfrm: Element, units: Units, extra: str = ""
) -> str:
    x, y, w, h = box
    styles = [
        f"left:{number(units.px(x))}px",
        f"top:{number(units.px(y))}px",
        f"width:{number(units.px(w))}px",
        f"height:{number(units.px(h))}px",
    ]
    rotation = integer(xfrm, "rot") / 60000
    if rotation:
        styles.append(f"transform:rotate({number(rotation)}deg)")
    if extra:
        styles.append(extra)
    return ";".join(styles)


def _shape(
    element: Element,
    kind: str,
    layer: Layer,
    scene: Scene,
    transform: Transform,
    group: Paint | None,
) -> str:
    chain = inherited(element, scene, layer) if layer is scene.slide else []
    if layer is scene.layout:
        chain = []
    xfrm = _xfrm(element, kind, chain)
    if xfrm is None:
        return ""
    if kind == "grpSp":
        group_paint = paint(element.find(p("grpSpPr")), scene, group)
        inner = transform.inner(xfrm)
        content = "".join(_children(element, layer, scene, inner, group_paint, top=False))
        name = _name(element)
        label = f' role="img" aria-label="{escape(name)}"' if name.startswith("Drawing") else ""
        return f'<div class="gr"{label}>{content}</div>' if content else ""
    box = _box(xfrm, transform)
    if kind == "pic":
        return _picture(element, chain, layer, scene, box, xfrm)
    if kind == "graphicFrame":
        return _graphic_frame(element, layer, scene, box, xfrm)
    return _sp(element, chain, layer, scene, box, xfrm, group)


def _name(element: Element) -> str:
    c_nv_pr = element.find(f"*/{p('cNvPr')}")
    return c_nv_pr.get("name", "") if c_nv_pr is not None else ""


def _sp_prs(element: Element, chain: list[Element]) -> list[Element]:
    return [sp_pr for shape in (*chain, element) if (sp_pr := shape.find(p("spPr"))) is not None]


def _geometry_source(sp_prs: list[Element]) -> Element | None:
    for sp_pr in reversed(sp_prs):
        if sp_pr.find(a("prstGeom")) is not None or sp_pr.find(a("custGeom")) is not None:
            return sp_pr
    return None


def _sp(
    element: Element,
    chain: list[Element],
    layer: Layer,
    scene: Scene,
    box: tuple[float, float, float, float],
    xfrm: Element,
    group: Paint | None,
) -> str:
    units = scene.units
    sp_prs = _sp_prs(element, chain)
    fill = shape_paint(sp_prs, element, scene, group)
    stroke = shape_stroke(sp_prs, element, scene)
    source = _geometry_source(sp_prs)
    width, height = units.px(box[2]), units.px(box[3])
    parts: list[str] = []
    svg = _svg(source, fill, stroke, width, height, xfrm, layer, scene)
    if svg:
        parts.append(svg)
    tx_body = element.find(p("txBody"))
    if tx_body is not None and any(t.text for t in tx_body.iter(a("t"))):
        parts.append(_text_box(element, tx_body, chain, layer, scene))
    if not parts:
        return ""
    return f'<div class="sh" style="{_position(box, xfrm, units)}">{"".join(parts)}</div>'


def _svg(
    source: Element | None,
    fill: Paint,
    stroke: Stroke | None,
    width: float,
    height: float,
    xfrm: Element,
    layer: Layer,
    scene: Scene,
) -> str:
    if fill.kind == "none" and stroke is None:
        return ""
    outlines = geometry.outlines(source, width, height)
    if not outlines:
        return ""
    defs: list[str] = []
    fill_value = "none"
    if fill.kind == "solid" and fill.color is not None:
        fill_value = fill.color.css()
    elif fill.kind == "gradient" and fill.stops:
        identifier = scene.next_id()
        stops = "".join(
            f'<stop offset="{number(pos)}" stop-color="{c.css()}"/>' for pos, c in fill.stops
        )
        if fill.radial:
            defs.append(f'<radialGradient id="{identifier}">{stops}</radialGradient>')
        else:
            angle = math.radians(fill.angle)
            dx, dy = math.cos(angle) / 2, math.sin(angle) / 2
            defs.append(
                f'<linearGradient id="{identifier}" x1="{number(0.5 - dx)}" '
                f'y1="{number(0.5 - dy)}" x2="{number(0.5 + dx)}" y2="{number(0.5 + dy)}">'
                f"{stops}</linearGradient>"
            )
        fill_value = f"url(#{identifier})"
    image = ""
    if fill.kind == "image" and fill.image:
        found = image_data(fill.owner or layer, fill.image, scene)
        if found is not None:
            identifier = scene.next_id()
            data = base64.b64encode(found[0]).decode("ascii")
            clip = "".join(f'<path d="{o.data}"/>' for o in outlines)
            defs.append(f'<clipPath id="{identifier}">{clip}</clipPath>')
            image = (
                f'<image href="data:{found[1]};base64,{data}" width="{number(width)}" '
                f'height="{number(height)}" preserveAspectRatio="none" '
                f'clip-path="url(#{identifier})"/>'
            )
    stroke_attributes = ""
    if stroke is not None:
        stroke_width = max(scene.units.px(stroke.width), 0.5)
        stroke_attributes = (
            f' stroke="{stroke.color.css()}" stroke-width="{number(stroke_width)}"'
            f' stroke-linecap="{stroke.cap}"'
        )
        if stroke.dash:
            dashes = " ".join(number(d * stroke_width) for d in stroke.dash)
            stroke_attributes += f' stroke-dasharray="{dashes}"'
        for end, name in ((stroke.head, "marker-start"), (stroke.tail, "marker-end")):
            if end in _ARROWS:
                identifier = scene.next_id()
                defs.append(_marker(identifier, end, stroke.color, name == "marker-start"))
                stroke_attributes += f' {name}="url(#{identifier})"'
    paths: list[str] = []
    for outline in outlines:
        own_fill = fill_value if outline.filled else "none"
        own_stroke = stroke_attributes if outline.stroked else ""
        if not outline.closed:
            own_fill = "none"
        elif "marker-" in own_stroke:
            own_stroke = " ".join(
                part for part in own_stroke.split(" ") if not part.startswith("marker-")
            )
            own_stroke = " " + own_stroke.strip()
        if own_fill == "none" and not own_stroke:
            continue
        paths.append(f'<path d="{outline.data}" fill="{own_fill}"{own_stroke}/>')
    if not paths and not image:
        return ""
    flips: list[str] = []
    if xfrm.get("flipH") in ("1", "true"):
        flips.append("scaleX(-1)")
    if xfrm.get("flipV") in ("1", "true"):
        flips.append("scaleY(-1)")
    style = f' style="transform:{" ".join(flips)}"' if flips else ""
    defs_html = f"<defs>{''.join(defs)}</defs>" if defs else ""
    return (
        f'<svg class="ge" width="{number(width)}" height="{number(height)}" '
        f'viewBox="0 0 {number(width)} {number(height)}"{style} aria-hidden="true">'
        f"{defs_html}{image}{''.join(paths)}</svg>"
    )


def _marker(identifier: str, kind: str, color: Color, start: bool) -> str:
    shape = {
        "oval": '<circle cx="5" cy="5" r="4"/>',
        "diamond": '<path d="M5 0 L10 5 L5 10 L0 5 Z"/>',
    }.get(kind, '<path d="M0 0 L10 5 L0 10 Z"/>')
    orient = "auto-start-reverse" if start else "auto"
    return (
        f'<marker id="{identifier}" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="3" '
        f'markerHeight="3" orient="{orient}" fill="{color.css()}">{shape}</marker>'
    )


def _text_styles(kind: str, element_chain: list[Element], scene: Scene) -> TextStyles:
    styles: list[Element] = []
    if scene.defaults is not None:
        styles.append(scene.defaults)
    master_styles = scene.master.element.find(p("txStyles"))
    if master_styles is not None:
        name = {"title": "titleStyle", "body": "bodyStyle"}.get(kind, "otherStyle")
        style = master_styles.find(p(name))
        if style is not None:
            styles.append(style)
    for shape in element_chain:
        list_style = shape.find(f"{p('txBody')}/{a('lstStyle')}")
        if list_style is not None:
            styles.append(list_style)
    return TextStyles(tuple(styles))


def _context(element: Element, layer: Layer, scene: Scene) -> TextContext:
    _, font_color = style_color(element, "fontRef", scene)
    context = TextContext(
        scene.units,
        scene.palette,
        layer.link,
        lambda r_id: _image_class(layer, r_id, scene),
        font_color,
    )
    if layer is scene.slide:
        c_nv_pr = element.find(f"*/{p('cNvPr')}")
        shape_id = integer(c_nv_pr, "id", -1)
        for index, (step, effect) in scene.builds.paragraphs.get(shape_id, {}).items():
            context.builds[index] = step
            context.effects[index] = effect
    return context


def _text_box(
    element: Element, tx_body: Element, chain: list[Element], layer: Layer, scene: Scene
) -> str:
    body_prs = [
        body_pr
        for shape in (*chain, element)
        if (body_pr := shape.find(f"{p('txBody')}/{a('bodyPr')}")) is not None
    ]
    layout = body_layout(body_prs, scene.units)
    styles = _text_styles(text_kind(element, chain), chain, scene)
    content = html_text(tx_body, styles, layout, _context(element, layer, scene))
    return _text_frame(layout, content)


def _text_frame(layout: BodyLayout, content: str) -> str:
    left, top, right, bottom = layout.insets
    justify = {"ctr": "center", "b": "flex-end"}.get(layout.anchor, "flex-start")
    style = (
        f"padding:{number(top)}px {number(right)}px {number(bottom)}px {number(left)}px;"
        f"justify-content:{justify}"
    )
    return f'<div class="tx" style="{style}"><div class="tb">{content}</div></div>'


def _picture(
    element: Element,
    chain: list[Element],
    layer: Layer,
    scene: Scene,
    box: tuple[float, float, float, float],
    xfrm: Element,
) -> str:
    units = scene.units
    blip_fill = element.find(p("blipFill"))
    blip = blip_fill.find(a("blip")) if blip_fill is not None else None
    if blip_fill is None or blip is None:
        return ""
    svg = next(
        (
            ext.find(f"{{{ASVG}}}svgBlip")
            for ext in blip.iterfind(f"{a('extLst')}/{a('ext')}")
            if ext.get("uri") == SVG_BLIP
        ),
        None,
    )
    r_id = (svg if svg is not None else blip).get(r("embed"), "")
    css_class = _image_class(layer, r_id, scene)
    if css_class is None and svg is not None:
        css_class = _image_class(layer, blip.get(r("embed"), ""), scene)
    if css_class is None:
        return ""
    width, height = units.px(box[2]), units.px(box[3])
    crop = blip_fill.find(a("srcRect"))
    left, top = integer(crop, "l") / 100000, integer(crop, "t") / 100000
    right, bottom = integer(crop, "r") / 100000, integer(crop, "b") / 100000
    shown_w = width / max(1 - left - right, 1e-6)
    shown_h = height / max(1 - top - bottom, 1e-6)
    image_style = (
        f"left:{number(-left * shown_w)}px;top:{number(-top * shown_h)}px;"
        f"width:{number(shown_w)}px;height:{number(shown_h)}px"
    )
    effects: list[str] = []
    alpha = blip.find(a("alphaModFix"))
    if alpha is not None:
        effects.append(f"opacity:{number(integer(alpha, 'amt', 100000) / 100000)}")
    if blip.find(a("grayscl")) is not None:
        effects.append("filter:grayscale(1)")
    if effects:
        image_style += ";" + ";".join(effects)
    sp_prs = _sp_prs(element, chain)
    source = _geometry_source(sp_prs)
    shape = geometry.preset_name(source)
    clip = ""
    if shape == "ellipse":
        clip = "border-radius:50%"
    elif shape not in ("rect",):
        outlines = geometry.outlines(source, width, height)
        if outlines:
            clip = f"clip-path:path('{outlines[0].data}')"
    c_nv_pr = element.find(f"*/{p('cNvPr')}")
    alt = (c_nv_pr.get("descr") or "") if c_nv_pr is not None else ""
    label = f' role="img" aria-label="{escape(alt)}"' if alt else ' aria-hidden="true"'
    stroke = shape_stroke(sp_prs, element, scene)
    outline = (
        _svg(source, NO_PAINT, stroke, width, height, xfrm, layer, scene)
        if stroke is not None
        else ""
    )
    return (
        f'<div class="sh pc" style="{_position(box, xfrm, units, clip)}"{label}>'
        f'<div class="im {css_class}" style="{image_style}"></div>{outline}</div>'
    )


def _graphic_frame(
    element: Element,
    layer: Layer,
    scene: Scene,
    box: tuple[float, float, float, float],
    xfrm: Element,
) -> str:
    data = element.find(f"{a('graphic')}/{a('graphicData')}")
    if data is None:
        return ""
    table = data.find(a("tbl"))
    if table is not None:
        return _table(table, layer, scene, box, xfrm)
    chart = data.find(f"{{{charts.C}}}chart")
    if chart is not None:
        part = layer.related(chart.get(r("id"), ""))
        svg = charts.chart_svg(part, scene.language) if part is not None else None
        if svg is None:
            return ""
        return f'<div class="sh ch" style="{_position(box, xfrm, scene.units)}">{svg}</div>'
    return ""


def _border(tc_pr: Element | None, side: str, scene: Scene) -> str:
    ln = tc_pr.find(a(side)) if tc_pr is not None else None
    if ln is None:
        return ""
    fill = paint(ln, scene)
    if fill is None or fill.kind != "solid" or fill.color is None:
        return ""
    width = max(scene.units.px(integer(ln, "w", 12700)), 0.5)
    css_side = {"lnL": "left", "lnR": "right", "lnT": "top", "lnB": "bottom"}[side]
    return f"border-{css_side}:{number(width)}px solid {fill.color.css()}"


def _table(
    table: Element,
    layer: Layer,
    scene: Scene,
    box: tuple[float, float, float, float],
    xfrm: Element,
) -> str:
    units = scene.units
    widths = [
        units.px(integer(col, "w")) for col in table.iterfind(f"{a('tblGrid')}/{a('gridCol')}")
    ]
    columns = "".join(f'<col style="width:{number(w)}px">' for w in widths)
    styles = TextStyles(tuple(s for s in (scene.defaults,) if s is not None))
    rows: list[str] = []
    for tr in table.iterfind(a("tr")):
        cells: list[str] = []
        for tc in tr.iterfind(a("tc")):
            if tc.get("hMerge") in ("1", "true") or tc.get("vMerge") in ("1", "true"):
                continue
            tc_pr = tc.find(a("tcPr"))
            insets = (
                units.px(integer(tc_pr, "marL", 91440)),
                units.px(integer(tc_pr, "marT", 45720)),
                units.px(integer(tc_pr, "marR", 91440)),
                units.px(integer(tc_pr, "marB", 45720)),
            )
            anchor = tc_pr.get("anchor", "t") if tc_pr is not None else "t"
            layout = BodyLayout(insets, anchor, True, 1.0, 0.0)
            css = [
                f"padding:{number(insets[1])}px {number(insets[2])}px "
                f"{number(insets[3])}px {number(insets[0])}px",
                "vertical-align:" + {"ctr": "middle", "b": "bottom"}.get(anchor, "top"),
            ]
            fill = paint(tc_pr, scene) if tc_pr is not None else None
            if fill is not None and fill.kind == "solid" and fill.color is not None:
                css.append(f"background:{fill.color.css()}")
            for side in ("lnL", "lnR", "lnT", "lnB"):
                border = _border(tc_pr, side, scene)
                if border:
                    css.append(border)
            spans = ""
            if integer(tc, "gridSpan", 1) > 1:
                spans += f' colspan="{integer(tc, "gridSpan", 1)}"'
            if integer(tc, "rowSpan", 1) > 1:
                spans += f' rowspan="{integer(tc, "rowSpan", 1)}"'
            tx_body = tc.find(a("txBody"))
            context = TextContext(
                units,
                scene.palette,
                layer.link,
                lambda r_id: _image_class(layer, r_id, scene),
                scene.palette.color_named("tx1"),
            )
            content = html_text(tx_body, styles, layout, context) if tx_body is not None else ""
            cells.append(f'<td{spans} style="{";".join(css)}">{content}</td>')
        height = units.px(integer(tr, "h"))
        rows.append(f'<tr style="height:{number(height)}px">{"".join(cells)}</tr>')
    x, y, w, _ = box
    position = f"left:{number(units.px(x))}px;top:{number(units.px(y))}px"
    total = sum(widths) or units.px(w)
    return (
        f'<div class="sh tl" style="{position}"><table style="width:{number(total)}px">'
        f"<colgroup>{columns}</colgroup>{''.join(rows)}</table></div>"
    )
