"""What the braces after an image say (E15-S04): ``![Foto](a.jpg){focus=top fit=contain}``.

``focus`` is the point of the image that stays in view where a picture placeholder crops it
(PowerPoint): ``center`` (the default), ``top``, ``bottom``, ``left``, ``right`` or ``x%,y%``
(``30%,20%``: the point 30 % from the left and 20 % from the top). ``fit=contain`` fits the
image into the placeholder instead of cropping it (``cover``, the default, crops). ``scale=N``
scales the image (0 < N ≤ 5; Word and PDF: its size, slides: at most its fitted size). The
styles ``.grey`` (greyscale) and ``.round`` (a circle around the focus) change the picture in
every format (``image_styles``). Word and PDF never crop: ``focus`` and ``fit`` have no effect
there, so that one source serves every format.

``scale=N`` in the title (E11-S04) still works for a year (until 2027-11) and gives the note
``image-scale-in-title``. ``take`` reads all this once per image (``generated_images.
add_generated`` calls it for every generator), takes ``scale=`` out of the title and keeps the
result in ``Token.meta[KEY]``, where ``of`` finds it.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Final

from markdown_it.token import Token

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.result import NoteCodes, Notes
from pta_documents.markdown.image_attributes import ATTRIBUTES

KEY: Final = "pta_documents.image"
"""``Token.meta`` key of an image token: its ``ImageAttributes`` (``take``)."""
MAX_SCALE: Final = 5.0
VALID: Final = "focus=…, fit=cover|contain, scale=N, .round, .grey"
"""Every image attribute, as it is written, for error messages."""
FOCUS_VALUES: Final = "center, top, bottom, left, right or x%,y% (e.g. 30%,20%)"

_ITEM: Final = re.compile(
    r'\s*(?:\.(?P<cls>[^\s.=]+)|(?P<key>[A-Za-z][\w-]*)=(?:"(?P<quoted>[^"]*)"|(?P<value>[^\s"]*)))'
)
_POINT: Final = re.compile(r"(\d+(?:\.\d+)?)%\s*,\s*(\d+(?:\.\d+)?)%")
_TITLE_SCALE: Final = re.compile(r"(?<!\S)scale=(\S*)")


class Fit(StrEnum):
    COVER = "cover"
    """Fill the placeholder and crop what sticks out (around the focus)."""
    CONTAIN = "contain"
    """Fit the whole image into the placeholder, nothing cropped."""


@dataclass(frozen=True)
class Focus:
    """A point of the image as shares of its width and height (0 left/top, 1 right/bottom)."""

    x: float
    y: float


CENTER: Final = Focus(0.5, 0.5)
NAMED_FOCUS: Final = {
    "center": CENTER,
    "top": Focus(0.5, 0.0),
    "bottom": Focus(0.5, 1.0),
    "left": Focus(0.0, 0.5),
    "right": Focus(1.0, 0.5),
}


@dataclass(frozen=True)
class ImageAttributes:
    focus: Focus | None = None
    """The point that stays in view; None: not written, the centre."""
    fit: Fit = Fit.COVER
    round: bool = False
    """``.round``: a circle (PowerPoint: an ellipse geometry, else a masked PNG)."""
    grey: bool = False
    """``.grey``: in greyscale."""
    scale: float | None = None
    """``scale=N``; None: not written (1)."""
    scale_in_title: bool = False
    """``scale=N`` came from the title (E11-S04), not from the braces."""
    written: str = ""
    """The braces as written (``{focus=top}``), for messages; empty without."""

    @property
    def point(self) -> Focus:
        """The focus, the centre if none is written."""
        return self.focus or CENTER

    @property
    def factor(self) -> float:
        """The scale, 1 if none is written."""
        return 1.0 if self.scale is None else self.scale

    @property
    def styled(self) -> bool:
        return self.round or self.grey

    @classmethod
    def parse(
        cls, image: Token, format: DocumentFormat, line: int | None = None
    ) -> ImageAttributes:
        """The attributes of an ``image`` token: from the braces after it and ``scale=`` in its
        title (the token stays as it is).

        Raises ``DocumentConversionError`` with ``line`` for an unknown attribute or value.
        """
        meta = image.meta or {}
        written = meta.get(ATTRIBUTES)
        result = cls()
        if isinstance(written, str):
            result = _parse_braces(written, format, line)
        title_scale = _title_scale(str(image.attrs.get("title") or ""))
        if title_scale is not None:
            if result.scale is not None:
                raise _error(
                    format,
                    line,
                    f"The image has scale twice: in its title and in '{result.written}'. "
                    "Keep the one in the braces.",
                )
            result = replace(
                result, scale=_scale(title_scale[0], format, line), scale_in_title=True
            )
        return result


def take(
    image: Token, format: DocumentFormat, line: int | None = None, notes: Notes | None = None
) -> ImageAttributes:
    """Read the attributes of ``image`` (``ImageAttributes.parse``) into ``Token.meta[KEY]``
    and take ``scale=`` out of its title; with ``notes``, a ``scale=`` in the title gives the
    note ``image-scale-in-title``. Twice on one token reads it once."""
    known = (image.meta or {}).get(KEY)
    if isinstance(known, ImageAttributes):
        return known
    attributes = ImageAttributes.parse(image, format, line)
    if attributes.scale_in_title:
        title = str(image.attrs.get("title") or "")
        found = _title_scale(title)
        assert found is not None
        _, rest = found
        if rest:
            image.attrs["title"] = rest
        else:
            image.attrs.pop("title", None)
        if notes is not None:
            notes.add(
                NoteCodes.IMAGE_SCALE_IN_TITLE,
                line,
                f"'scale=' in the title of the image '{image.attrs.get('src', '')}' still works "
                f"until 2027-11; write it in braces after the image instead: "
                f"![…](…){{scale={attributes.factor:g}}}.",
            )
    image.meta = {**(image.meta or {}), KEY: attributes}
    return attributes


def of(image: Token) -> ImageAttributes:
    """The attributes ``take`` read for ``image``; the defaults if it did not."""
    known = (image.meta or {}).get(KEY)
    return known if isinstance(known, ImageAttributes) else ImageAttributes()


def visible_window(
    size: tuple[float, float], ratio: float, focus: Focus
) -> tuple[float, float, float, float]:
    """What a box of width : height ``ratio`` filled with an image of ``size`` crops off, as
    shares of the image (left, top, right, bottom): the window is as large as the proportions
    allow and centred on ``focus``, but never beyond the image's edge."""
    width, height = size
    left = top = right = bottom = 0.0
    if width <= 0 or height <= 0 or ratio <= 0:
        return left, top, right, bottom
    image_ratio = width / height
    if image_ratio > ratio:
        visible = ratio / image_ratio
        left = _clamp(focus.x - visible / 2, 0.0, 1.0 - visible)
        right = 1.0 - visible - left
    elif image_ratio < ratio:
        visible = image_ratio / ratio
        top = _clamp(focus.y - visible / 2, 0.0, 1.0 - visible)
        bottom = 1.0 - visible - top
    return left, top, right, bottom


def _clamp(value: float, lowest: float, highest: float) -> float:
    return max(lowest, min(highest, value))


def _parse_braces(inside: str, format: DocumentFormat, line: int | None) -> ImageAttributes:
    written = "{" + inside + "}"
    result = ImageAttributes(written=written)
    seen: set[str] = set()
    position = 0
    text = inside.rstrip()
    while position < len(text):
        match = _ITEM.match(text, position)
        if match is None or match.end() == position:
            rest = text[position:].strip()
            raise _error(
                format,
                line,
                f"'{rest}' in the image attributes '{written}' is no attribute. Valid "
                f"attributes: {VALID}.",
            )
        position = match.end()
        if match.group("cls") is not None:
            name = "." + match.group("cls")
            value = ""
        else:
            name = match.group("key")
            quoted = match.group("quoted")
            value = quoted if quoted is not None else match.group("value") or ""
        if name in seen:
            raise _error(format, line, f"The image attributes '{written}' name {name} twice.")
        seen.add(name)
        match name:
            case ".round":
                result = replace(result, round=True)
            case ".grey":
                result = replace(result, grey=True)
            case "focus":
                result = replace(result, focus=_focus(value, written, format, line))
            case "fit":
                try:
                    fit = Fit(value.strip().lower())
                except ValueError:
                    raise _error(
                        format,
                        line,
                        f"'fit={value}' in '{written}' is no fit. Valid values: cover (fill the "
                        "frame, crop), contain (fit in, nothing cropped).",
                    ) from None
                result = replace(result, fit=fit)
            case "scale":
                result = replace(result, scale=_scale(value, format, line))
            case _:
                raise _error(
                    format,
                    line,
                    f"Unknown image attribute '{name}' in '{written}'. Valid attributes: {VALID}.",
                )
    return result


def _focus(value: str, written: str, format: DocumentFormat, line: int | None) -> Focus:
    name = value.strip().lower()
    if name in NAMED_FOCUS:
        return NAMED_FOCUS[name]
    point = _POINT.fullmatch(name)
    if point is not None:
        x, y = float(point.group(1)), float(point.group(2))
        if x <= 100 and y <= 100:
            return Focus(x / 100, y / 100)
    raise _error(
        format,
        line,
        f"'focus={value}' in '{written}' is no focus. Valid values: {FOCUS_VALUES}, each "
        "share at most 100 %.",
    )


def _scale(written: str, format: DocumentFormat, line: int | None) -> float:
    try:
        scale = float(written.replace(",", "."))
    except ValueError:
        scale = math.nan
    if not 0 < scale <= MAX_SCALE:
        raise _error(
            format,
            line,
            f"'scale={written}' is no scale: write a number above 0 and at most "
            f"{MAX_SCALE:g}, e.g. scale=0.5.",
        )
    return scale


def _title_scale(title: str) -> tuple[str, str] | None:
    """The value of ``scale=…`` in ``title`` and the rest of the title; None without."""
    match = _TITLE_SCALE.search(title)
    if match is None:
        return None
    rest = " ".join((title[: match.start()] + title[match.end() :]).split())
    return match.group(1), rest


def _error(format: DocumentFormat, line: int | None, reason: str) -> DocumentConversionError:
    return DocumentConversionError(format, f"Line {line}: {reason}" if line else reason)
