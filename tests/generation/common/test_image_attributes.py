"""E15-S04: reading ``{focus=… fit=… scale=… .round .grey}`` and the crop around the focus."""

from __future__ import annotations

import pytest
from markdown_it.token import Token

from pta_documents import DocumentConversionError
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common import image_attributes
from pta_documents.generation.common.image_attributes import (
    CENTER,
    Fit,
    Focus,
    ImageAttributes,
    take,
    visible_window,
)
from pta_documents.generation.common.result import NoteCodes, Notes
from pta_documents.markdown.parser import parse

PPTX = DocumentFormat.PPTX


def image(text: str) -> Token:
    [child] = [c for c in parse(text)[1].children or [] if c.type == "image"]
    return child


def read(braces: str) -> ImageAttributes:
    return ImageAttributes.parse(image(f"![a](b.jpg){braces}"), PPTX, 3)


def test_without_braces_everything_is_the_default() -> None:
    attributes = ImageAttributes.parse(image("![a](b.jpg)"), PPTX)
    assert attributes == ImageAttributes()
    assert attributes.point == CENTER and attributes.factor == 1.0 and not attributes.styled


@pytest.mark.parametrize(
    ("written", "focus"),
    [
        ("center", Focus(0.5, 0.5)),
        ("top", Focus(0.5, 0.0)),
        ("bottom", Focus(0.5, 1.0)),
        ("left", Focus(0.0, 0.5)),
        ("RIGHT", Focus(1.0, 0.5)),
        ("30%,20%", Focus(0.3, 0.2)),
        ('"30%, 20%"', Focus(0.3, 0.2)),
        ("100%,0%", Focus(1.0, 0.0)),
        ("12.5%,50%", Focus(0.125, 0.5)),
    ],
)
def test_focus_takes_a_side_or_a_point(written: str, focus: Focus) -> None:
    assert read(f"{{focus={written}}}").focus == focus


def test_everything_together() -> None:
    attributes = read("{.round .grey fit=contain scale=0,5 focus=top}")
    assert attributes.round and attributes.grey and attributes.styled
    assert attributes.fit is Fit.CONTAIN
    assert attributes.scale == 0.5
    assert attributes.written == "{.round .grey fit=contain scale=0,5 focus=top}"


@pytest.mark.parametrize(
    ("braces", "expected"),
    [
        ("{.shadow}", "Line 3: Unknown image attribute '.shadow' in '{.shadow}'. Valid"),
        ("{width=3}", "Line 3: Unknown image attribute 'width'"),
        (
            "{focus=oben}",
            "Line 3: 'focus=oben' in '{focus=oben}' is no focus. Valid values: center",
        ),
        ("{focus=120%,0%}", "Line 3: 'focus=120%,0%' in '{focus=120%,0%}' is no focus."),
        ("{fit=fill}", "Line 3: 'fit=fill' in '{fit=fill}' is no fit. Valid values: cover"),
        ("{scale=0}", "Line 3: 'scale=0' is no scale"),
        ("{scale=6}", "Line 3: 'scale=6' is no scale"),
        ("{.round .round}", "Line 3: The image attributes '{.round .round}' name .round twice."),
        ("{focus}", "Line 3: 'focus' in the image attributes '{focus}' is no attribute."),
    ],
)
def test_an_unknown_attribute_or_value_is_an_error_with_the_line(
    braces: str, expected: str
) -> None:
    with pytest.raises(DocumentConversionError) as error:
        read(braces)
    assert error.value.reason.startswith(expected)
    if "Unknown" in expected:
        assert image_attributes.VALID in error.value.reason


def test_scale_in_the_title_still_counts_but_not_twice() -> None:
    attributes = ImageAttributes.parse(image('![a](b.jpg "Foto scale=0.5")'), PPTX)
    assert attributes.scale == 0.5 and attributes.scale_in_title
    with pytest.raises(DocumentConversionError) as error:
        ImageAttributes.parse(image('![a](b.jpg "scale=0.5"){scale=2}'), PPTX, 4)
    assert error.value.reason.startswith("Line 4: The image has scale twice")


def test_take_keeps_the_attributes_and_moves_scale_out_of_the_title_with_a_note() -> None:
    token = image('![a](b.jpg "Foto scale=2"){.grey}')
    notes = Notes()
    attributes = take(token, PPTX, 7, notes)
    assert token.attrs["title"] == "Foto"
    assert image_attributes.of(token) is attributes
    assert attributes.grey and attributes.scale == 2.0
    [note] = notes.to_tuple()
    assert note.code == NoteCodes.IMAGE_SCALE_IN_TITLE and note.line == 7
    assert "{scale=2}" in note.message
    assert take(token, PPTX, 7, notes) is attributes  # read once
    assert len(notes) == 1


def test_of_an_image_take_did_not_read_is_the_default() -> None:
    assert image_attributes.of(image("![a](b.jpg){.grey}")) == ImageAttributes()


# ---------------------------------------------------------------------- the crop


@pytest.mark.parametrize(
    ("focus", "expected"),
    [
        (Focus(0.5, 0.5), (0.0, 0.25, 0.0, 0.25)),
        (Focus(0.5, 0.0), (0.0, 0.0, 0.0, 0.5)),
        (Focus(0.5, 1.0), (0.0, 0.5, 0.0, 0.0)),
        (Focus(0.5, 0.3), (0.0, 0.05, 0.0, 0.45)),
        (Focus(0.0, 0.1), (0.0, 0.0, 0.0, 0.5)),  # clamped at the top edge
    ],
)
def test_a_tall_image_in_a_square_box_is_cut_above_and_below(
    focus: Focus, expected: tuple[float, ...]
) -> None:
    assert visible_window((100, 200), 1.0, focus) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("focus", "expected"),
    [
        (Focus(0.5, 0.5), (0.25, 0.0, 0.25, 0.0)),
        (Focus(0.0, 0.5), (0.0, 0.0, 0.5, 0.0)),
        (Focus(1.0, 0.5), (0.5, 0.0, 0.0, 0.0)),
        (Focus(0.3, 0.2), (0.05, 0.0, 0.45, 0.0)),
    ],
)
def test_a_wide_image_is_cut_left_and_right(focus: Focus, expected: tuple[float, ...]) -> None:
    assert visible_window((400, 100), 2.0, focus) == pytest.approx(expected)


@pytest.mark.parametrize("ratio", [0.5, 0.8, 1.0, 1.5, 2.38])
@pytest.mark.parametrize("size", [(100, 300), (300, 100), (1920, 1280), (880, 1000)])
@pytest.mark.parametrize("focus", [Focus(0.0, 0.0), Focus(0.3, 0.7), Focus(1.0, 1.0), CENTER])
def test_the_window_has_the_box_proportions_and_keeps_the_focus_in_view(
    ratio: float, size: tuple[int, int], focus: Focus
) -> None:
    left, top, right, bottom = visible_window(size, ratio, focus)
    assert min(left, top, right, bottom) >= 0
    width = size[0] * (1 - left - right)
    height = size[1] * (1 - top - bottom)
    assert width / height == pytest.approx(ratio)
    assert left - 1e-9 <= focus.x <= 1 - right + 1e-9
    assert top - 1e-9 <= focus.y <= 1 - bottom + 1e-9


def test_an_image_in_its_own_proportions_is_not_cut() -> None:
    assert visible_window((300, 200), 1.5, Focus(0.0, 0.0)) == (0.0, 0.0, 0.0, 0.0)
