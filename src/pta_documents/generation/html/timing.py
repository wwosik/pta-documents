"""Builds and transitions of a slide, read back from what the PPTX generator wrote (E09).

Builds: the main sequence of ``p:timing`` has one group per click; each effect in it names its
shape (``p:spTgt/@spid``) and, for text built paragraph by paragraph, the paragraph
(``p:txEl/p:pRg``). The HTML deck shows them as steps: an entrance appears on its step, an exit
leaves, an emphasis turns the text PTA blue. Transitions: the effect of ``p:transition``
(``mc:AlternateContent`` for morph, which the browser fades).
"""

from __future__ import annotations

from typing import Final

from pta_documents.generation.html.ooxml import MC, P159, Element, integer, local, p
from pta_documents.generation.html.shapes import Builds

_ENTRANCES: Final = {"1": "appear", "2": "fly", "10": "fade", "22": "wipe"}


def builds(slide: Element) -> Builds:
    """The steps of ``slide`` (``p:sld``)."""
    result = Builds()
    sequence = next(
        (node for node in slide.iter(p("cTn")) if node.get("nodeType") == "mainSeq"),
        None,
    )
    if sequence is None:
        return result
    children = sequence.find(p("childTnLst"))
    if children is None:
        return result
    step = 0
    for click in children.iterfind(p("par")):
        effects = [node for node in click.iter(p("cTn")) if node.get("presetClass") is not None]
        if not effects:
            continue
        step += 1
        for effect in effects:
            name = _effect(effect)
            for target in effect.iter(p("spTgt")):
                shape = integer(target, "spid", -1)
                paragraph = target.find(f"{p('txEl')}/{p('pRg')}")
                if paragraph is not None:
                    index = integer(paragraph, "st")
                    result.paragraphs.setdefault(shape, {}).setdefault(index, (step, name))
                else:
                    result.shapes.setdefault(shape, (step, name))
                break
    result.steps = step
    return result


def _effect(node: Element) -> str:
    kind = node.get("presetClass")
    if kind == "exit":
        return "exit"
    if kind == "emph":
        return "emphasize"
    return _ENTRANCES.get(node.get("presetID", ""), "fade")


_DIRECTIONS: Final = {"l": "left", "r": "right", "u": "up", "d": "down"}


def transition(slide: Element) -> str | None:
    """The transition of ``slide`` as the name of ``SlideTransition``; None without one."""
    for child in slide:
        if child.tag == f"{{{MC}}}AlternateContent":
            choice = child.find(f"{{{MC}}}Choice")
            if choice is not None and choice.find(f".//{{{P159}}}morph") is not None:
                return "morph"
            fallback = child.find(f"{{{MC}}}Fallback/{p('transition')}")
            if fallback is not None:
                return _named(fallback)
        if child.tag == p("transition"):
            return _named(child)
    return None


def _named(element: Element) -> str | None:
    effect = next(iter(element), None)
    if effect is None:
        return None
    kind = local(effect)
    if kind in ("push", "wipe"):
        return f"{kind}-{_DIRECTIONS.get(effect.get('dir', 'l'), 'left')}"
    return {
        "fade": "fade",
        "split": "split",
        "cover": "cover",
        "pull": "uncover",
        "zoom": "zoom",
        "cut": "cut",
    }.get(kind)
