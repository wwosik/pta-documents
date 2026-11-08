"""The flowables the layout engine adds to reportlab's: paragraphs with a number or bullet that
moves with their first line, a rule on the left, a bookmark; the "keep with the start of what
follows" break before headings; the anchor that reserves room for footnotes at the foot of the
page.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final

from reportlab.lib import colors as rl_colors
from reportlab.platypus import Flowable, Image, Paragraph, Table
from reportlab.platypus.flowables import CondPageBreak
from reportlab.rl_config import paraFontSizeHeightOffset

SQUARE_SHARE: Final = 0.45
"""The side of the bullet square as a share of the font size (Wingdings ``n`` in Word)."""
DASH_SHARE: Final = 0.75
"""The length of the dash (``―``) as a share of the font size."""
BOX_SHARE: Final = 0.7
"""The side of a task-list box as a share of the font size."""
START_LINES: Final = 2
"""What has to fit below a heading: two lines of a paragraph (a single one may not stay)."""


class MarkerKind(StrEnum):
    TEXT = "text"
    SQUARE = "square"
    DASH = "dash"
    BOX = "box"
    CHECKED_BOX = "checked-box"


@dataclass(frozen=True)
class Marker:
    """What stands in the hanging indent of the first line: a number, a bullet or a box."""

    kind: MarkerKind
    color: rl_colors.Color
    x: float = 0.0
    """Where it starts, from the left of the paragraph."""
    text: str = ""
    font: str = ""
    """The font of ``text``."""


@dataclass(frozen=True)
class Rule:
    """A rule on the left of the paragraph, over its full height (note boxes)."""

    color: rl_colors.Color
    width: float


@dataclass(frozen=True)
class Outline:
    """An entry in the bookmarks of the PDF."""

    title: str
    level: int


class PtaParagraph(Paragraph):
    """A paragraph with an optional ``marker``, ``rule``, ``anchor`` and ``outline``.

    When reportlab splits it over a page, the marker, anchor and outline go with the first part
    only, the rule with every part.
    """

    def __init__(
        self,
        text: str | None,
        style: Any = None,
        bulletText: str | None = None,
        frags: Any = None,
        caseSensitive: int = 1,
        encoding: str = "utf8",
        *,
        marker: Marker | None = None,
        rule: Rule | None = None,
        anchor: str | None = None,
        outline: Outline | None = None,
    ) -> None:
        super().__init__(text, style, bulletText, frags, caseSensitive, encoding)  # type: ignore[arg-type]
        self.marker = marker
        self.rule = rule
        self.anchor = anchor
        self.outline = outline

    def split(self, availWidth: float, availHeight: float) -> list[Flowable]:
        parts: list[Flowable] = super().split(availWidth, availHeight)
        if len(parts) > 1:
            for n, part in enumerate(parts):
                if isinstance(part, PtaParagraph):
                    part.rule = self.rule
                    part.marker = self.marker if n == 0 else None
                    part.anchor = self.anchor if n == 0 else None
                    part.outline = self.outline if n == 0 else None
        return parts

    def draw(self) -> None:
        canvas: Any = self.canv
        if self.anchor is not None:
            canvas.bookmarkHorizontal(self.anchor, 0, self.height + self.style.fontSize)
            if self.outline is not None:
                canvas.addOutlineEntry(
                    self.outline.title, self.anchor, self.outline.level, closed=False
                )
        if self.rule is not None:
            canvas.saveState()
            canvas.setFillColor(self.rule.color)
            canvas.rect(0, 0, self.rule.width, self.height, stroke=0, fill=1)
            canvas.restoreState()
        super().draw()
        if self.marker is not None:
            self._draw_marker(canvas, self.marker)

    def first_baseline(self) -> float:
        """The baseline of the first line, from the bottom of the paragraph (as reportlab's
        ``drawPara`` places it)."""
        lines: Any = getattr(self, "blPara", None)
        if lines is None:
            return self.height - self.style.fontSize
        first = lines if lines.kind == 0 else (lines.lines[0] if lines.lines else lines)
        if paraFontSizeHeightOffset:
            offset = float(getattr(first, "fontSize", self.style.fontSize))
        else:
            offset = float(getattr(first, "ascent", self.style.fontSize))
        return self.height - offset

    def _draw_marker(self, canvas: Any, marker: Marker) -> None:
        size = float(self.style.fontSize)
        y = self.first_baseline()
        x = marker.x
        canvas.saveState()
        canvas.setFillColor(marker.color)
        canvas.setStrokeColor(marker.color)
        match marker.kind:
            case MarkerKind.TEXT:
                canvas.setFont(marker.font, size)
                canvas.drawString(x, y, marker.text)
            case MarkerKind.SQUARE:
                side = size * SQUARE_SHARE
                canvas.rect(x, y + size * 0.12, side, side, stroke=0, fill=1)
            case MarkerKind.DASH:
                canvas.setLineWidth(size * 0.07)
                middle = y + size * 0.3
                canvas.line(x, middle, x + size * DASH_SHARE, middle)
            case MarkerKind.BOX | MarkerKind.CHECKED_BOX:
                side = size * BOX_SHARE
                bottom = y - size * 0.05
                canvas.setLineWidth(size * 0.06)
                canvas.rect(x, bottom, side, side, stroke=1, fill=0)
                if marker.kind is MarkerKind.CHECKED_BOX:
                    inset = side * 0.2
                    canvas.line(x + inset, bottom + inset, x + side - inset, bottom + side - inset)
                    canvas.line(x + inset, bottom + side - inset, x + side - inset, bottom + inset)
        canvas.restoreState()


def start_height(flowable: Flowable, width: float, frame_height: float) -> float:
    """How much of ``flowable`` must fit on a page for it to start there: two lines of a
    paragraph that can split (all of one that cannot), the header and first row of a table,
    all of anything else; before a footnote anchor, its footnotes and the start of its
    paragraph."""
    if isinstance(flowable, FootnoteAnchor):
        notes = flowable.area.needed(flowable.notes, width)
        return notes + start_height(flowable.following, width, frame_height)
    _, height = flowable.wrap(width, frame_height)
    before = float(flowable.getSpaceBefore())
    if isinstance(flowable, Paragraph):
        lines: Any = getattr(flowable, "blPara", None)
        count = len(lines.lines) if lines is not None else 1
        if count > START_LINES + 1:
            return before + START_LINES * float(flowable.style.leading)
        return before + height
    if isinstance(flowable, Table):
        heights: Sequence[float] = getattr(flowable, "_rowHeights", None) or [height]
        repeat = int(getattr(flowable, "repeatRows", 0) or 0)
        return before + float(sum(heights[: repeat + 1]))
    return before + height


def _frame(flowable: Flowable) -> Any:
    """The frame being filled (reportlab's ``_doctemplateAttr("frame")``), None outside a
    document build."""
    canvas = getattr(flowable, "canv", None)
    return getattr(getattr(canvas, "_doctemplate", None), "frame", None)


class KeepWithStart(CondPageBreak):
    """Before a heading (or a run of them): a page break unless the headings and the start of
    what follows them fit below (DocLibs ``KeepHeight``). Never breaks at the top of a page —
    what does not fit there would not fit on the next one either."""

    def __init__(self, keep: Sequence[Flowable], following: Flowable | None) -> None:
        super().__init__(0)
        self.keep = list(keep)
        self.following = following

    def wrap(self, aW: float, aH: float) -> tuple[float, float]:
        frame: Any = _frame(self)
        if frame is not None and frame._atTop:
            return 0, 0
        full = float(frame._aH) if frame is not None else aH
        needed = 0.0
        for flowable in self.keep:
            _, height = flowable.wrap(aW, full)
            needed += float(flowable.getSpaceBefore()) + height + float(flowable.getSpaceAfter())
        if self.following is not None:
            needed += start_height(self.following, aW, full)
        self.height = needed if needed <= full else 0
        return super().wrap(aW, aH)


class FootnoteArea:
    """The footnotes of the page being laid out, drawn at its foot by the document template."""

    def __init__(self, gap: float, rule_width: float, rule_color: rl_colors.Color) -> None:
        self.gap = gap
        """Room between the text and the rule above the footnotes."""
        self.rule_width = rule_width
        self.rule_color = rule_color
        self.page: list[Flowable] = []
        self.height = 0.0

    def needed(self, notes: Sequence[Flowable], width: float) -> float:
        """The height ``notes`` add to the page (with the rule if they are its first)."""
        height = sum(n.wrap(width, 1e6)[1] + float(n.getSpaceBefore()) for n in notes)
        return height + (0.0 if self.page else self.gap)

    def place(self, notes: Sequence[Flowable], height: float) -> None:
        self.page.extend(notes)
        self.height += height

    def take(self) -> list[Flowable]:
        """The footnotes of the finished page; the next one starts empty."""
        page = self.page
        self.page = []
        self.height = 0.0
        return page


class FootnoteAnchor(Flowable):
    """Placed before the paragraph that refers to ``notes``: reserves their room at the foot
    of the page, so that the text above stops in time. If they do not fit with the start of
    the paragraph, both go to the next page."""

    def __init__(self, area: FootnoteArea, notes: Sequence[Flowable], following: Flowable) -> None:
        super().__init__()
        self.area = area
        self.notes = list(notes)
        self.following = following
        self.reserved = 0.0

    def wrap(self, aW: float, aH: float) -> tuple[float, float]:
        frame: Any = _frame(self)
        self.reserved = self.area.needed(self.notes, aW)
        full = float(frame._aH) if frame is not None else aH
        start = start_height(self.following, aW, full)
        if frame is not None and not frame._atTop and self.reserved + start > aH:
            return aW, aH + 1  # does not fit: on to the next page
        return aW, 0

    def split(self, availWidth: float, availHeight: float) -> list[Flowable]:
        return []

    def draw(self) -> None:
        frame: Any = _frame(self)
        self.area.place(self.notes, self.reserved)
        if frame is not None:
            frame._y1p += self.reserved


def picture(
    content: Any, width: float, height: float, space_before: float, space_after: float
) -> Image:
    """An image at ``width`` × ``height`` points, left as in a Word paragraph."""
    image = Image(content, width=width, height=height)
    image.hAlign = "LEFT"
    image.spaceBefore = space_before
    image.spaceAfter = space_after
    return image
