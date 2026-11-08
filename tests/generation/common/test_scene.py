"""E09-S04: ``::: scene`` is read and checked alike in every format (port of vt-tools-libs
``SceneTests``: the grammar, the colours, the mistakes with their line); a scene stands alone
under a ``##`` and inside the content area."""

from __future__ import annotations

from typing import Final

import pytest

from pta_documents.design import colors
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import scene_colors
from pta_documents.generation.common.scene import (
    COLUMNS,
    DEFAULT_TEXT_PT,
    ROWS,
    UNIT_EMU,
    Scene,
    SceneShape,
    ShapeKind,
    read_scene,
)
from pta_documents.markdown import DocumentResource
from pta_documents.markdown.parser import CONTAINER_OPEN, parse
from tests.generation.common.test_layout_syntax import GENERATORS, Generate

PPTX: Final = DocumentFormat.PPTX
LOGO: Final = DocumentResource("logo.png", "image/png", b"")


def scene_of(lines: str, find: bool = False) -> Scene:
    markdown = f"## Folie\n\n::: scene\n{lines}\n:::\n"
    tokens = parse(markdown)
    i = next(n for n, t in enumerate(tokens) if t.type == CONTAINER_OPEN)
    finder = (lambda path: LOGO if path == "logo.png" else None) if find else None
    return read_scene(tokens, i, PPTX, 0, finder)


def shape(line: str) -> SceneShape:
    return scene_of(line).shapes[0]


def test_every_part_of_a_line_is_read() -> None:
    read = shape(
        '- od: round 62,40 36x14 "OneDrive" fill=accent2 line=#AABBCC text=muted rotate=-3 '
        "opacity=0.5 size=20 bold solid step=2"
    )
    assert read == SceneShape(
        "od",
        ShapeKind.ROUND,
        62,
        40,
        36,
        14,
        "OneDrive",
        line=4,
        fill="accent2",
        stroke="#AABBCC",
        text_color="muted",
        rotation=-3,
        opacity=0.5,
        size=20,
        bold=True,
        solid=True,
        step=2,
    )


def test_without_a_list_marker_and_with_blank_lines_and_comments() -> None:
    read = scene_of('a: box 0,0 10x10\n\n<!-- Kommentar -->\n* b: text 1,1 5x5 "x"')
    assert [s.name for s in read.shapes] == ["a", "b"]
    assert [s.line for s in read.shapes] == [4, 7]
    assert read.shapes[0].size == DEFAULT_TEXT_PT and read.shapes[0].step == 0
    assert read.steps == 0 and read.texts == ("x",)


def test_lines_run_both_ways_and_take_their_box() -> None:
    line = shape("- a: arrow 80,50 -20x0 step=3")
    assert line.box == (60, 50, 20, 0)
    assert line.is_line and not line.is_box


def test_an_image_finds_its_picture() -> None:
    read = scene_of('- logo: image 0,0 20x20 "Das Logo" image=logo.png', find=True)
    assert read.shapes[0].resource is LOGO and read.shapes[0].text == "Das Logo"


def test_the_grid_is_square_over_the_content_area() -> None:
    assert (COLUMNS, ROWS) == (160, 67)
    assert UNIT_EMU == 70200  # 0.195 cm
    assert ROWS * UNIT_EMU <= 13.10 * 360000


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("- b: blob 0,0 1x1", "unknown kind 'blob'. Valid kinds: box, round, pill, circle, text"),
        ("- b: box 0,0 1x1 step=-1", "'step=-1' is not a whole number from 0."),
        ("- b: box 0,0 1x1 size=0", "'size=0' is not a number above 0."),
        ("- b: box 0,0 1x1 opacity=2", "'opacity=2' is not a number from 0 to 1."),
        ('- b: box 0,0 1x1 "a" "b"', "a shape takes one text in quotes."),
        ("- b: box 0,0 1x1 fill=primary fill=text", "'fill' is given twice."),
        ("- b: line 0,0 1x1 fill=primary", "a line takes no 'fill'."),
        ('- b: arrow 0,0 1x1 "a"', "a arrow takes no text."),
        ("- b: text 0,0 1x1 solid", "a text takes no 'solid'."),
        ("- b: box 0,0 1x1 image=logo.png", "only an image takes 'image='."),
        ("- b: image 0,0 1x1", "an image needs 'image=<path>'."),
        ("- b: box 0,0", "expected a kind, a position x,y and a size wxh after the name."),
        ("- b: box 0,0 1,1", "'1,1' is not a size wxh."),
        ("- b: box 0,0 0x5", "a box needs a width and height above 0."),
        ("- b: box 0,0 1x1 fill=pink", "'pink' is no colour. Valid colours: primary, text"),
        ("- b: box 0,0 1x1 glow", "unknown attribute 'glow'. Valid attributes: fill, line"),
        ("- nur Text", "expected 'name: kind x,y wxh"),
        ("- b: box 150,0 20x10", "reaches outside the grid of 160 × 67 units"),
        ("- b: box 0,60 10x10", "y from 60 to 70"),
        ("- b: line 10,10 -20x0", "x from -10 to 10"),
    ],
)
def test_mistakes_raise_naming_the_line(line: str, message: str) -> None:
    with pytest.raises(DocumentConversionError) as caught:
        scene_of(line)
    assert caught.value.reason.startswith(f"Line 4: Scene shape '{line}': ")
    assert message in caught.value.reason


def test_a_name_twice_and_an_empty_scene_raise() -> None:
    with pytest.raises(DocumentConversionError, match=r"Line 5: .*'a' is taken"):
        scene_of("- a: box 0,0 1x1\n- a: box 2,2 1x1")
    with pytest.raises(DocumentConversionError, match=r"Line 3: The '::: scene' holds no shapes"):
        scene_of("<!-- nichts -->")


def test_a_missing_image_raises() -> None:
    with pytest.raises(DocumentConversionError, match=r"'nope\.png' is not among the document"):
        scene_of("- a: image 0,0 5x5 image=nope.png", find=True)


# ---------------------------------------------------------------------- colours


def test_colours_default_by_kind() -> None:
    box, text, line = scene_of("- a: box 0,0 1x1\n- b: text 0,0 1x1\n- c: line 0,0 1x1").shapes
    assert (scene_colors.fill(box), scene_colors.stroke(box)) == ("surface", "border")
    assert (scene_colors.fill(text), scene_colors.stroke(text)) == ("none", "none")
    assert (scene_colors.fill(line), scene_colors.stroke(line)) == ("none", "line")
    assert scene_colors.text(box, False, False) == "text"
    assert scene_colors.text(text, False, True) == "background"


def test_the_roles_are_pta_colours() -> None:
    assert scene_colors.hex_of("primary") == colors.PTA_BLUE
    assert scene_colors.hex_of("text") == colors.TEXT_SLIDES
    assert scene_colors.hex_of("accent2") == colors.DARK_BLUE
    assert scene_colors.hex_of("warning") == colors.SIGNAL_AMBER
    assert scene_colors.hex_of("#aabbcc") == "AABBCC"
    assert scene_colors.hex_of("none") is None
    palette = {*colors.ACCENTS, *colors.STATUS_COLORS.values(), colors.TEXT_SLIDES, colors.WHITE}
    assert set(scene_colors.ROLES.values()) <= palette


def test_coloured_fills_are_soft_but_pta_blue_and_solid_ones() -> None:
    soft, blue, info, solid = scene_of(
        "- a: box 0,0 1x1 fill=warning\n- b: box 0,0 1x1 fill=primary\n"
        "- c: box 0,0 1x1 fill=info\n- d: box 0,0 1x1 fill=warning solid"
    ).shapes
    assert scene_colors.is_soft(soft) and scene_colors.stroke(soft) == "warning"
    assert not scene_colors.is_soft(blue) and scene_colors.stroke(blue) == "primary"
    assert not scene_colors.is_soft(info)  # info is PTA blue
    assert not scene_colors.is_soft(solid)
    assert scene_colors.soft_fill(colors.SIGNAL_AMBER) == colors.tint(colors.SIGNAL_AMBER, 0.12)
    white_text = shape("- a: box 0,0 1x1 fill=warning text=background")
    assert scene_colors.text(white_text, True, False) == "text"


# ---------------------------------------------------------------------- every format

SLIDE: Final = '# Deck\n\n## Folie\n\n::: scene\n- a: box 10,10 20x10 "Kasten"\n:::\n'


@pytest.mark.parametrize(
    ("markdown", "message"),
    [
        ("# Deck\n\n::: scene\n- a: box 0,0 1x1\n:::\n", "Line 3: A '::: scene' stands directly"),
        ("::: scene\n- a: box 0,0 1x1\n:::\n", "Line 1: A '::: scene' stands directly under"),
        (SLIDE + "\n::: scene\n- b: box 0,0 1x1\n:::\n", "Line 9: A '::: scene' stands"),
        (SLIDE + "\nMehr Text.\n", "Line 9: A slide with a '::: scene' holds only its title"),
        ("# D\n\n## F\n\nText.\n\n::: scene\n- a: box 0,0 1x1\n:::\n", "Line 5: A slide with"),
        (
            "# D\n\n## F\n\n:::: cards\n::: scene\n- a: box 0,0 1x1\n:::\n::::\n",
            "Line 6: A '::: scene' stands directly",
        ),
        ("# D\n\n## F {.agenda}\n\n::: scene\n- a: box 0,0 1x1\n:::\n", "Line 3: A scene slide"),
        (
            '# D\n\n## F {layout="Titel und Inhalt"}\n\n::: scene\n- a: box 0,0 1x1\n:::\n',
            "Line 3: A scene slide goes on the layout 'Nur Titel'",
        ),
        ("# D\n\n## F\n\n{.build}\n::: scene\n- a: box 0,0 1x1\n:::\n", "Line 5: A scene is"),
        ("# D\n\n## F\n\n::: scene dark\n- a: box 0,0 1x1\n:::\n", "takes no arguments"),
        ("# D\n\n## F\n\n::: scene\n- a: blob 0,0 1x1\n:::\n", "Line 6: Scene shape"),
    ],
)
@GENERATORS
def test_mistakes_raise_alike(
    markdown: str, message: str, generate: Generate, format: DocumentFormat
) -> None:
    with pytest.raises(DocumentConversionError) as caught:
        generate(markdown)
    assert caught.value.format is format
    assert message in caught.value.reason


@GENERATORS
def test_a_scene_alone_with_notes_and_a_comment_is_fine(
    generate: Generate, format: DocumentFormat
) -> None:
    markdown = SLIDE + "\n<!-- Kommentar -->\n\n::: notes\nSprechen.\n:::\n\n## Weiter\n\nText\n"
    generate(markdown)
