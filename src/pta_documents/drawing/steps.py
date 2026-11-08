"""Steps as a row of chevrons (E15-S02), the same ``Drawing`` for every format.

``draw`` spreads the steps over the whole width as chevrons pointing right — the first one a home
plate with a straight left side — with each title in the chevron and its text below it (not in
it: PTA patterns are plain). Light blue with dark blue titles; with a ``{.current}`` step, that
one in PTA blue with white text and those before it in light grey. Sizes are CSS pixels (a
pixel is 0.75 pt); colours come from ``design.colors``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from pta_documents.design import colors
from pta_documents.drawing.model import Drawing, DrawingItem, DrawingText, TextAnchor
from pta_documents.drawing.schedule import px, wrap
from pta_documents.drawing.shapes import chevron
from pta_documents.drawing.svg_output import estimate_width
from pta_documents.generation.common.steps import Steps

UNLIMITED: Final = 1000
"""As many lines as a text needs."""


@dataclass(frozen=True)
class StepsStyle:
    """Sizes of a row of steps in pixels (sizes of text in points)."""

    title_pt: float = 16
    text_pt: float = 12
    min_text_pt: float = 10
    """No text of a drawing is smaller (E15)."""
    height: float = px(1.6 / 2.54 * 72)
    """A chevron: 1.6 cm."""
    depth_share: float = 0.35
    """How deep the point is, as a share of the height."""
    gap: float = 4
    """Between two chevrons."""
    pad: float = 6
    """Between a title and the edges of its chevron."""
    text_gap: float = 8
    """Between the chevrons and the texts below them."""
    line_spacing: float = 1.25
    title_lines: int = 2
    """Lines a title is wrapped into; longer titles are drawn smaller (``max_width``)."""
    text_lines: int = 5
    """Lines a text may take below its chevron before it goes below the picture (Word)."""


STEPS: Final = StepsStyle()


@dataclass(frozen=True)
class _Slot:
    x: float
    """The left edge of the chevron."""
    width: float
    depth: float
    first: bool

    @property
    def title_left(self) -> float:
        return self.x + (0 if self.first else self.depth)

    @property
    def title_right(self) -> float:
        return self.x + self.width - self.depth / 2

    @property
    def centre(self) -> float:
        return (self.title_left + self.title_right) / 2


def _slots(count: int, width: float, style: StepsStyle) -> list[_Slot]:
    """Chevrons side by side over ``width``: each fits into the notch of the next, ``gap`` apart."""
    depth = style.height * style.depth_share
    each = (width + (count - 1) * (depth - style.gap)) / count
    pitch = each - depth + style.gap
    return [_Slot(n * pitch, each, depth, n == 0) for n in range(count)]


def text_room(steps: Steps, width: float, style: StepsStyle = STEPS) -> float:
    """How wide the text below a chevron may be: the part of the row its chevron takes."""
    slot = _slots(len(steps.steps), width, style)[0]
    return slot.width - slot.depth


def texts_fit(steps: Steps, width: float, size_pt: float, style: StepsStyle = STEPS) -> bool:
    """Whether every text fits below its chevron at ``size_pt``: no word wider than its room and
    at most ``style.text_lines`` lines."""
    room = text_room(steps, width, style)
    size = px(size_pt)
    for step in steps.steps:
        if any(estimate_width(word, size) > room for word in step.text.split()):
            return False
        if len(wrap(step.text, size, room, UNLIMITED)) > style.text_lines:
            return False
    return True


def draw(
    steps: Steps,
    width: float,
    *,
    dark: bool = False,
    text_pt: float | None = None,
    texts: bool = True,
    style: StepsStyle = STEPS,
) -> Drawing:
    """The steps ``width`` pixels wide; ``dark``: on a dark slide (texts in white); the texts
    below the chevrons at ``text_pt`` (default ``style.text_pt``), none without ``texts``."""
    current = steps.current
    slots = _slots(len(steps.steps), width, style)
    items: list[DrawingItem] = []
    title_size = px(style.title_pt)
    title_height = title_size * style.line_spacing
    text_size = px(text_pt if text_pt is not None else style.text_pt)
    text_height = text_size * style.line_spacing
    room = slots[0].width - slots[0].depth
    text_color = colors.WHITE if dark else colors.TEXT_SLIDES
    deepest = 0
    for n, (step, slot) in enumerate(zip(steps.steps, slots, strict=True)):
        if current is not None and n == current:
            fill, title_color = colors.PTA_BLUE, colors.WHITE
        elif current is not None and n < current:
            fill, title_color = colors.GREY_LIGHT, colors.TEXT_SLIDES
        else:
            fill, title_color = colors.LIGHT_BLUE, colors.DARK_BLUE
        items.append(
            chevron(slot.x, 0, slot.width, style.height, slot.depth, fill, first=slot.first)
        )
        title_room = slot.title_right - slot.title_left - 2 * style.pad
        lines = wrap(step.title, title_size, title_room, style.title_lines)
        top = (style.height - len(lines) * title_height) / 2
        for k, line in enumerate(lines):
            items.append(
                DrawingText.line(
                    slot.centre,
                    top + k * title_height + title_height * 0.75,
                    line,
                    title_size,
                    title_color,
                    bold=True,
                    anchor=TextAnchor.MIDDLE,
                    max_width=title_room,
                )
            )
        if not texts or not step.text:
            continue
        centre = slot.x + (slot.width + (0 if slot.first else slot.depth) - slot.depth) / 2
        below = wrap(step.text, text_size, room, UNLIMITED)
        deepest = max(deepest, len(below))
        for k, line in enumerate(below):
            items.append(
                DrawingText.line(
                    centre,
                    style.height + style.text_gap + k * text_height + text_height * 0.75,
                    line,
                    text_size,
                    text_color,
                    anchor=TextAnchor.MIDDLE,
                )
            )
    height = style.height + (style.text_gap + deepest * text_height if deepest else 0)
    return Drawing(width, height, tuple(items))
