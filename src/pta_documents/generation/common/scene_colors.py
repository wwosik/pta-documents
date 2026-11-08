"""The colours of scene shapes (E09-S04): PTA roles, ``#RRGGBB`` from the Markdown, or ``none``.

Port of vt-tools-libs ``SceneColors`` on the PTA palette (``design.colors``): the roles map to the
PowerPoint theme ``PTA 2020`` — ``primary`` PTA blue, ``text`` the slide text, ``muted`` and
``line`` the dark grey, ``border`` the middle grey, ``surface`` the light grey of PTA areas,
``background`` white, ``accent1``–``accent6`` the theme accents, the status colours those of
coloured words. A box filled in a colour other than PTA blue is drawn "soft": the colour at
``SOFT_SHARE`` on white, with the colour as its line and its text in ``text``; ``solid`` keeps it
full.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from pta_documents.design import colors
from pta_documents.design.colors import StatusCategory

if TYPE_CHECKING:
    from pta_documents.generation.common.scene import SceneShape

NONE: Final = "none"
"""No fill or no line."""
SOFT_SHARE: Final = 0.12
"""The share of the colour in a soft fill."""

ROLES: Final = {
    "primary": colors.PTA_BLUE,
    "text": colors.TEXT_SLIDES,
    "muted": colors.GREY_DARK,
    "background": colors.WHITE,
    **{f"accent{n}": color for n, color in enumerate(colors.ACCENTS, start=1)},
    "surface": colors.GREY_LIGHT,
    "border": colors.GREY_MID,
    "line": colors.GREY_DARK,
    **{category.value: colors.STATUS_COLORS[category] for category in StatusCategory},
}
"""Every role and its colour."""
VALID: Final = "primary, text, muted, background, accent1–accent6, surface, border, line, " + (
    ", ".join(category.value for category in StatusCategory)
)
"""The roles, for error messages."""

_HEX: Final = re.compile(r"^#[0-9A-Fa-f]{6}$")
_COLOURED: Final = (
    *(f"accent{n}" for n in range(1, len(colors.ACCENTS) + 1)),
    *(category.value for category in StatusCategory),
)
"""The roles that are colours rather than greys or text: filled boxes in them are soft."""


def is_valid(value: str) -> bool:
    return value == NONE or value in ROLES or _HEX.match(value) is not None


def hex_of(color: str) -> str | None:
    """The colour as upper-case hex without ``#``; None for ``none``."""
    if color == NONE:
        return None
    if color in ROLES:
        return ROLES[color]
    return color.removeprefix("#").upper()


def fill(shape: SceneShape) -> str:
    """The fill as written, or the kind's default: ``surface`` for boxes, none for the others."""
    if shape.fill is not None:
        return shape.fill
    return "surface" if shape.is_box else NONE


def stroke(shape: SceneShape) -> str:
    """The line as written, or the kind's default: ``line`` for lines and arrows; around a box
    filled in ``primary`` or a colour its fill, around other boxes ``border``; none for the
    others (text, image)."""
    if shape.stroke is not None:
        return shape.stroke
    if shape.is_line:
        return "line"
    if not shape.is_box:
        return NONE
    if shape.fill is not None and (shape.fill == "primary" or _is_colour(shape.fill)):
        return shape.fill
    return "border"


def is_soft(shape: SceneShape) -> bool:
    """Whether the shape is a box filled in a colour (an accent, a status colour or
    ``#RRGGBB``) that is not PTA blue, without ``solid``."""
    return (
        shape.is_box
        and not shape.solid
        and shape.fill is not None
        and _is_colour(shape.fill)
        and hex_of(shape.fill) != colors.PTA_BLUE
    )


def soft_fill(hex_color: str) -> str:
    """The fill of a soft shape in ``hex_color``: the colour at 12 % on white."""
    return colors.tint(hex_color, SOFT_SHARE)


def text(shape: SceneShape, soft: bool, dark: bool) -> str:
    """The text colour as written, or ``text`` — on a dark slide ``background`` for a ``text``
    shape, which stands on the slide itself; on a soft shape ``background`` is ``text`` too,
    since white cannot be read on the tint."""
    if shape.text_color is None:
        return "background" if dark and not shape.is_box else "text"
    if soft and shape.text_color == "background":
        return "text"
    return shape.text_color


def _is_colour(color: str) -> bool:
    return color in _COLOURED or color.startswith("#")
