"""Builds (E09-S02): the timing tree of a slide, as PowerPoint writes it.

Port of vt-tools-libs ``Animations.Timing``: the main sequence, one group per click in the order
of the clicks, an effect per target — the first ``clickEffect``, the others ``withEffect`` — and
the build list (``p:bldLst``): ``p:bldP build="p"`` for text built paragraph by paragraph,
``p:bldP animBg="1"`` for a shape built as a whole, ``p:bldGraphic`` with ``p:bldAsOne`` for a
table or chart; pictures and groups need no entry. Every effect takes half a second.

Effects (decision 2026-11-07): the entrances fade (preset 10), appear (1), fly in from the
bottom (2) and wipe from the bottom (22); ``{.exit}`` fades out (exit preset 10); ``{.emphasize}``
turns the text PTA blue (emphasis preset 3, font colour).

``Builds`` collects what a slide builds while the writer draws it: paragraphs of text bodies by
their index, and every shape drawn ``at`` a click; ``timing`` turns that into the XML.

Transitions (E09-S03): ``transition`` is the port of vt-tools-libs ``Animations.Transition``,
``set_transition`` puts it where the schema wants it in ``p:sld``: after ``p:clrMapOvr``, before
``p:timing`` (else PowerPoint repairs the file).
"""

from __future__ import annotations

from collections.abc import Callable, Generator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Final

from lxml import etree

from pta_documents.design import colors
from pta_documents.generation.common.slide_transition import SlideTransition
from pta_documents.generation.pptx.model import Click, Effect, Paragraph

A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
DURATION: Final = 500
"""Milliseconds of every effect."""
EMPHASIS_COLOR: Final = colors.PTA_BLUE
END_TIME: Final = 100 * 1000
"""The end of a motion path in its time list (per cent times 1000)."""
MC: Final = "http://schemas.openxmlformats.org/markup-compatibility/2006"
P159: Final = "http://schemas.microsoft.com/office/powerpoint/2015/09/main"
"""PowerPoint 2019's namespace, of ``p159:morph``."""


def p(name: str) -> str:
    return f"{{{P}}}{name}"


class Target(Enum):
    """What a build animates, for the build list."""

    TEXT = "text"
    """A shape with a text body: listed with ``p:bldP``."""
    GRAPHIC = "graphic"
    """A table or chart (graphic frame): listed with ``p:bldGraphic``."""
    OTHER = "other"
    """A picture, group or line: animated, not listed."""


@dataclass(frozen=True)
class Build:
    """The shape ``shape`` (``cNvPr/@id``), or its paragraph ``paragraph`` (-1: the whole
    shape), animated on ``click``."""

    click: Click
    shape: int
    paragraph: int
    target: Target


_CLASS: Final = {
    Effect.FADE: "entr",
    Effect.APPEAR: "entr",
    Effect.FLY: "entr",
    Effect.WIPE: "entr",
    Effect.EXIT: "exit",
    Effect.EMPHASIZE: "emph",
}
_PRESET: Final = {
    Effect.FADE: (10, 0),
    Effect.APPEAR: (1, 0),
    Effect.FLY: (2, 4),
    Effect.WIPE: (22, 4),
    Effect.EXIT: (10, 0),
    Effect.EMPHASIZE: (3, 2),
}
"""(presetID, presetSubtype) of each effect; subtype 4 is "from bottom"."""


def shape_id(element: etree._Element) -> int | None:
    """The ``cNvPr/@id`` of a shape of the shape tree (``p:sp``, ``p:pic``, ``p:graphicFrame``,
    ``p:grpSp``, ``p:cxnSp``)."""
    c_nv_pr = element.find(f"*/{p('cNvPr')}")
    if c_nv_pr is None:
        return None
    value = c_nv_pr.get("id")
    return int(value) if value is not None and value.isdigit() else None


def target_of(element: etree._Element) -> Target:
    if element.tag == p("sp"):
        return Target.TEXT
    if element.tag == p("graphicFrame"):
        return Target.GRAPHIC
    return Target.OTHER


class Builds:
    """What the slide being written builds."""

    def __init__(self) -> None:
        self.builds: list[Build] = []
        self.current: Click | None = None
        """The click of what is drawn now (``at``); paragraphs without a click of their own
        take it."""
        self.claimed: set[int] = set()
        """Shapes with a build already: drawn at an inner click, or built paragraph by
        paragraph."""

    def paragraphs(self, body: etree._Element, paragraphs: Sequence[Paragraph]) -> None:
        """The paragraphs just written as the ``a:p`` children of the text body ``body``, in
        order: those on a click (their own or the current one) are built one by one."""
        shape = body.getparent()
        number = shape_id(shape) if shape is not None else None
        if number is None:
            return
        built = False
        for index, paragraph in enumerate(paragraphs):
            click = paragraph.click or self.current
            if click is not None:
                self.builds.append(Build(click, number, index, Target.TEXT))
                built = True
        if built:
            self.claimed.add(number)

    @contextmanager
    def at(self, tree: etree._Element | None, click: Click | None) -> Generator[None]:
        """Every shape added to the shape tree ``tree`` within is built on ``click`` as a
        whole (unless an inner click or its paragraphs claimed it); None: nothing to build."""
        if tree is None or click is None:
            yield
            return
        before = list(tree)
        saved, self.current = self.current, click
        try:
            yield
        finally:
            self.current = saved
        for element in tree:
            if any(element is old for old in before):
                continue
            self.shape(element, click)

    def each(self, tree: etree._Element | None, clicks: Sequence[Click | None]) -> _Each:
        """For drawing that adds one shape per click of ``clicks`` (pictures side by side)."""
        return _Each(self, tree, clicks)

    def shape(self, element: etree._Element, click: Click) -> None:
        number = shape_id(element)
        if number is None or number in self.claimed:
            return
        target = target_of(element)
        if click.effect is Effect.EMPHASIZE and target is not Target.TEXT:
            return  # a font colour needs text
        self.claimed.add(number)
        self.builds.append(Build(click, number, -1, target))

    def write(self, slide: etree._Element) -> None:
        """The timing tree into ``slide`` (``p:sld``), for the builds whose shapes and
        paragraphs are still on it (``finish`` removes placeholders left empty)."""
        tree = slide.find(f"{p('cSld')}/{p('spTree')}")
        if tree is None or not self.builds:
            return
        paragraphs: dict[int, int] = {}
        for element in tree:
            number = shape_id(element)
            if number is not None:
                body = element.find(p("txBody"))
                paragraphs[number] = len(body.findall(f"{{{A}}}p")) if body is not None else 0
        kept = [
            b for b in self.builds if b.shape in paragraphs and b.paragraph < paragraphs[b.shape]
        ]
        element = timing(kept)
        if element is None:
            return
        old = slide.find(p("timing"))
        if old is not None:
            slide.remove(old)
        ext = slide.find(p("extLst"))
        if ext is not None:
            ext.addprevious(element)
        else:
            slide.append(element)


class _Each:
    def __init__(
        self, builds: Builds, tree: etree._Element | None, clicks: Sequence[Click | None]
    ) -> None:
        self.builds = builds
        self.tree = tree
        self.clicks = clicks
        self.before: list[etree._Element] = []

    def __enter__(self) -> None:
        if self.tree is not None:
            self.before = list(self.tree)

    def __exit__(self, *_: object) -> None:
        if self.tree is None:
            return
        added = [e for e in self.tree if not any(e is old for old in self.before)]
        if len(added) != len(self.clicks):
            return  # pragma: no cover - one shape per click, as drawn
        for element, click in zip(added, self.clicks, strict=True):
            chosen = click or self.builds.current
            if chosen is not None:
                self.builds.shape(element, chosen)


def timing(builds: Sequence[Build]) -> etree._Element | None:
    """The ``p:timing`` of ``builds``: one click per click number, in their order; None
    without builds."""
    if not builds:
        return None
    groups = _groups(builds)
    counter = [2]

    def next_id() -> int:
        counter[0] += 1
        return counter[0]

    xml: list[str] = [
        f'<p:timing xmlns:p="{P}" xmlns:a="{A}"><p:tnLst><p:par>',
        '<p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>',
        '<p:seq concurrent="1" nextAc="seek">',
        '<p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>',
    ]
    numbers = sorted({b.click.number for b in builds})
    for number in numbers:
        click = [b for b in builds if b.click.number == number]
        xml.append(
            f'<p:par><p:cTn id="{next_id()}" fill="hold"><p:stCondLst>'
            '<p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>'
            f'<p:par><p:cTn id="{next_id()}" fill="hold"><p:stCondLst>'
            '<p:cond delay="0"/></p:stCondLst><p:childTnLst>'
        )
        for n, build in enumerate(click):
            effect = build.click.effect
            preset, subtype = _PRESET[effect]
            node = "clickEffect" if n == 0 else "withEffect"
            group = groups[(build.shape, _CLASS[effect])]
            xml.append(
                f'<p:par><p:cTn id="{next_id()}" presetID="{preset}" '
                f'presetClass="{_CLASS[effect]}" presetSubtype="{subtype}" fill="hold" '
                f'grpId="{group}" nodeType="{node}"><p:stCondLst><p:cond delay="0"/>'
                "</p:stCondLst><p:childTnLst>"
            )
            xml.append(_behaviours(effect, _target(build), next_id))
            xml.append("</p:childTnLst></p:cTn></p:par>")
        xml.append("</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>")
    xml.append(
        "</p:childTnLst></p:cTn>"
        '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl>'
        "</p:cond></p:prevCondLst>"
        '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl>'
        "</p:cond></p:nextCondLst>"
        "</p:seq></p:childTnLst></p:cTn></p:par></p:tnLst>"
    )
    xml.append(_build_list(builds, groups))
    xml.append("</p:timing>")
    return etree.fromstring("".join(xml))


def _groups(builds: Sequence[Build]) -> dict[tuple[int, str], int]:
    """The build group (``grpId``) of each shape and effect class: 0, 1 … per shape, in the
    order they first come."""
    groups: dict[tuple[int, str], int] = {}
    for build in builds:
        key = (build.shape, _CLASS[build.click.effect])
        if key not in groups:
            groups[key] = sum(1 for shape, _ in groups if shape == build.shape)
    return groups


def _build_list(builds: Sequence[Build], groups: dict[tuple[int, str], int]) -> str:
    entries: list[str] = []
    for (shape, effect_class), group in groups.items():
        mine = [b for b in builds if b.shape == shape and _CLASS[b.click.effect] == effect_class]
        target = mine[0].target
        if target is Target.OTHER:
            continue
        if target is Target.GRAPHIC:
            entries.append(
                f'<p:bldGraphic spid="{shape}" grpId="{group}"><p:bldAsOne/></p:bldGraphic>'
            )
        elif any(b.paragraph >= 0 for b in mine):
            entries.append(f'<p:bldP spid="{shape}" grpId="{group}" build="p"/>')
        else:
            entries.append(f'<p:bldP spid="{shape}" grpId="{group}" animBg="1"/>')
    return f"<p:bldLst>{''.join(entries)}</p:bldLst>" if entries else ""


def _target(build: Build) -> str:
    if build.paragraph < 0:
        return f'<p:spTgt spid="{build.shape}"/>'
    return (
        f'<p:spTgt spid="{build.shape}"><p:txEl><p:pRg st="{build.paragraph}" '
        f'end="{build.paragraph}"/></p:txEl></p:spTgt>'
    )


def _set(target: str, attribute: str, value: str, cn_id: int, delay: int = 0) -> str:
    return (
        f'<p:set><p:cBhvr><p:cTn id="{cn_id}" dur="1" fill="hold"><p:stCondLst>'
        f'<p:cond delay="{delay}"/></p:stCondLst></p:cTn><p:tgtEl>{target}</p:tgtEl>'
        f"<p:attrNameLst><p:attrName>{attribute}</p:attrName></p:attrNameLst></p:cBhvr>"
        f'<p:to><p:strVal val="{value}"/></p:to></p:set>'
    )


def _visible(target: str, cn_id: int) -> str:
    return _set(target, "style.visibility", "visible", cn_id)


def _filter(target: str, transition: str, name: str, cn_id: int) -> str:
    return (
        f'<p:animEffect transition="{transition}" filter="{name}"><p:cBhvr>'
        f'<p:cTn id="{cn_id}" dur="{DURATION}"/><p:tgtEl>{target}</p:tgtEl></p:cBhvr>'
        "</p:animEffect>"
    )


def _move(target: str, attribute: str, start: str, end: str, cn_id: int) -> str:
    return (
        f'<p:anim calcmode="lin" valueType="num"><p:cBhvr additive="base">'
        f'<p:cTn id="{cn_id}" dur="{DURATION}" fill="hold"/><p:tgtEl>{target}</p:tgtEl>'
        f"<p:attrNameLst><p:attrName>{attribute}</p:attrName></p:attrNameLst></p:cBhvr>"
        f'<p:tavLst><p:tav tm="0"><p:val><p:strVal val="{start}"/></p:val></p:tav>'
        f'<p:tav tm="{END_TIME}"><p:val><p:strVal val="{end}"/></p:val></p:tav></p:tavLst>'
        "</p:anim>"
    )


def _colour(target: str, attribute: str, cn_id: int) -> str:
    return (
        f'<p:animClr clrSpc="hsl" dir="cw"><p:cBhvr override="childStyle">'
        f'<p:cTn id="{cn_id}" dur="{DURATION}" fill="hold"/><p:tgtEl>{target}</p:tgtEl>'
        f"<p:attrNameLst><p:attrName>{attribute}</p:attrName></p:attrNameLst></p:cBhvr>"
        f'<p:to><a:srgbClr val="{EMPHASIS_COLOR}"/></p:to></p:animClr>'
    )


def _behaviours(effect: Effect, target: str, next_id: Callable[[], int]) -> str:
    match effect:
        case Effect.FADE:
            return _visible(target, next_id()) + _filter(target, "in", "fade", next_id())
        case Effect.APPEAR:
            return _visible(target, next_id())
        case Effect.FLY:
            return (
                _visible(target, next_id())
                + _move(target, "ppt_x", "#ppt_x", "#ppt_x", next_id())
                + _move(target, "ppt_y", "1+#ppt_h/2", "#ppt_y", next_id())
            )
        case Effect.WIPE:
            return _visible(target, next_id()) + _filter(target, "in", "wipe(up)", next_id())
        case Effect.EXIT:
            return _filter(target, "out", "fade", next_id()) + _set(
                target, "style.visibility", "hidden", next_id(), DURATION - 1
            )
        case Effect.EMPHASIZE:
            return _colour(target, "style.color", next_id())


# ---------------------------------------------------------------------- transitions (E09-S03)

_TRANSITIONS: Final = {
    SlideTransition.FADE: "<p:fade/>",
    SlideTransition.PUSH: "<p:push/>",
    SlideTransition.PUSH_LEFT: '<p:push dir="l"/>',
    SlideTransition.PUSH_RIGHT: '<p:push dir="r"/>',
    SlideTransition.PUSH_UP: '<p:push dir="u"/>',
    SlideTransition.PUSH_DOWN: '<p:push dir="d"/>',
    SlideTransition.WIPE: "<p:wipe/>",
    SlideTransition.WIPE_LEFT: '<p:wipe dir="l"/>',
    SlideTransition.WIPE_RIGHT: '<p:wipe dir="r"/>',
    SlideTransition.WIPE_UP: '<p:wipe dir="u"/>',
    SlideTransition.WIPE_DOWN: '<p:wipe dir="d"/>',
    SlideTransition.SPLIT: '<p:split orient="vert" dir="out"/>',
    SlideTransition.COVER: "<p:cover/>",
    SlideTransition.UNCOVER: "<p:pull/>",
    SlideTransition.ZOOM: "<p:zoom/>",
    SlideTransition.CUT: "<p:cut/>",
}
"""The effect element of each transition but ``none`` and ``morph``; ``dir`` is the way the
slide moves, the default ``l``."""


def transition(kind: SlideTransition) -> etree._Element | None:
    """The ``p:transition`` of ``kind`` (``spd="med"``, as PowerPoint writes it), for ``morph``
    an ``mc:AlternateContent`` with the morph for PowerPoint 2019 (``p159``) and a fade for
    every other program, both ``spd="slow"``; None for ``none``."""
    if kind is SlideTransition.NONE:
        return None
    if kind is SlideTransition.MORPH:
        return etree.fromstring(
            f'<mc:AlternateContent xmlns:mc="{MC}">'
            f'<mc:Choice xmlns:p159="{P159}" Requires="p159">'
            f'<p:transition xmlns:p="{P}" spd="slow"><p159:morph option="byObject"/>'
            "</p:transition></mc:Choice>"
            f'<mc:Fallback><p:transition xmlns:p="{P}" spd="slow"><p:fade/></p:transition>'
            "</mc:Fallback></mc:AlternateContent>"
        )
    return etree.fromstring(
        f'<p:transition xmlns:p="{P}" spd="med">{_TRANSITIONS[kind]}</p:transition>'
    )


def set_transition(slide: etree._Element, kind: SlideTransition) -> None:
    """The transition ``kind`` into ``slide`` (``p:sld``) at its place in the schema: after
    ``p:cSld`` and ``p:clrMapOvr``, before ``p:timing`` and ``p:extLst``."""
    element = transition(kind)
    if element is None:
        return
    after = slide.find(p("clrMapOvr"))
    if after is None:
        after = slide.find(p("cSld"))
    if after is None:  # pragma: no cover - every slide has its common data
        slide.insert(0, element)
    else:
        after.addnext(element)
