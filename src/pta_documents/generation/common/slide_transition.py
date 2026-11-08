"""How a slide comes in (E09-S03): for the whole deck (front matter ``uebergang``) or one slide
or chapter (``{uebergang="…"}`` on its heading).

Port of vt-tools-libs ``SlideTransition`` (``none``, ``fade``, ``push``, ``wipe``, ``morph``),
grown by the decision of 2026-11-07: directions for ``push`` and ``wipe`` and the other quiet
PowerPoint transitions ``split``, ``cover``, ``uncover``, ``zoom`` and ``cut``. The values are
English like the rest of the syntax (decision 2026-11-07); a direction is the way the slide
moves (``push-up``: the new slide pushes the old one up, coming from the bottom), as in the
``dir`` attribute of PresentationML. Word and PDF take the attribute and ignore it.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

from pta_documents.errors import DocumentConversionError, DocumentFormat


class SlideTransition(StrEnum):
    NONE = "none"
    """The slide replaces the last one at once (the default)."""
    FADE = "fade"
    """The slide fades in over the last one."""
    PUSH = "push"
    """The slide pushes the last one out to the left (as ``push-left``)."""
    PUSH_LEFT = "push-left"
    PUSH_RIGHT = "push-right"
    PUSH_UP = "push-up"
    PUSH_DOWN = "push-down"
    WIPE = "wipe"
    """The slide is wiped in over the last one, moving left (as ``wipe-left``)."""
    WIPE_LEFT = "wipe-left"
    WIPE_RIGHT = "wipe-right"
    WIPE_UP = "wipe-up"
    WIPE_DOWN = "wipe-down"
    SPLIT = "split"
    """The slide opens from the middle outwards (vertical split)."""
    COVER = "cover"
    """The slide moves in over the last one from the right."""
    UNCOVER = "uncover"
    """The last slide moves out to the left and uncovers the new one."""
    ZOOM = "zoom"
    """The slide grows from the middle."""
    CUT = "cut"
    """The slide replaces the last one at once, written as a transition."""
    MORPH = "morph"
    """Shapes of the same name move from where they were to where they are, the rest fades
    (PowerPoint 2019 and 365); older programs and LibreOffice fade."""

    @classmethod
    def parse(cls, name: str, format: DocumentFormat) -> SlideTransition:
        """The transition named ``name`` (case-insensitive); raises with the valid values."""
        for transition in cls:
            if transition.value == name.strip().lower():
                return transition
        raise DocumentConversionError(
            format, f"Unknown slide transition '{name}'. Valid transitions: {VALID}."
        )


VALID: Final = ", ".join(t.value for t in SlideTransition)
"""The names, for error messages and guides."""
