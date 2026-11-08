"""E09-S04: a scene as a still drawing (port of vt-tools-libs ``SceneTests.Drawing_*``)."""

from __future__ import annotations

from pathlib import Path

from pta_documents.design import colors
from pta_documents.drawing import scene as scene_drawing
from pta_documents.drawing.model import DrawingShape, DrawingText, MoveTo
from pta_documents.drawing.svg_output import to_svg
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common.scene import Scene, read_scene
from pta_documents.markdown.parser import CONTAINER_OPEN, parse


def scene_of(lines: str) -> Scene:
    tokens = parse(f"## F\n\n::: scene\n{lines}\n:::\n")
    i = next(n for n, t in enumerate(tokens) if t.type == CONTAINER_OPEN)
    return read_scene(tokens, i, DocumentFormat.PDF, 0)


def test_the_drawing_is_the_whole_grid_with_opacity_mixed_onto_the_ground() -> None:
    drawing, images = scene_drawing.draw(
        scene_of('- a: box 10,10 20x10 "Kasten" fill=primary opacity=0.5\n- b: box 0,0 5x5')
    )
    assert (drawing.width, drawing.height) == (1600, 670)
    ground, box, text, plain = drawing.items
    assert isinstance(ground, DrawingShape) and ground.fill == colors.WHITE
    assert isinstance(box, DrawingShape)
    assert box.fill == colors.mix(colors.PTA_BLUE, 0.5, colors.WHITE)
    assert box.path.bounds == (100, 100, 200, 100)
    assert isinstance(text, DrawingText) and text.text == "Kasten" and text.color != colors.WHITE
    assert isinstance(plain, DrawingShape) and plain.fill == colors.GREY_LIGHT
    assert plain.stroke == colors.GREY_MID and images == ()


def test_soft_fills_and_a_dark_ground() -> None:
    drawing, _ = scene_drawing.draw(
        scene_of('- a: box 0,0 10x10 fill=success\n- t: text 20,0 20x5 "Hi"'), dark=True
    )
    ground, box, text = drawing.items
    assert isinstance(ground, DrawingShape) and ground.fill == colors.DARK_BLUE
    assert isinstance(box, DrawingShape)
    assert box.fill == colors.mix(colors.tint(colors.SIGNAL_GREEN, 0.12), 1, colors.DARK_BLUE)
    assert box.stroke == colors.SIGNAL_GREEN
    assert isinstance(text, DrawingText) and text.color == colors.WHITE


def test_rotation_is_baked_into_the_outline_and_invisible_shapes_are_left_out() -> None:
    drawing, _ = scene_drawing.draw(
        scene_of("- a: box 0,0 10x10 rotate=90\n- b: box 0,0 5x5 opacity=0")
    )
    _, box = drawing.items
    assert isinstance(box, DrawingShape)
    start = box.path.segments[0]
    assert isinstance(start, MoveTo)
    # The top left corner turned clockwise about the centre (50, 50) is the top right one.
    assert (round(start.x), round(start.y)) == (100, 0)


def test_an_arrow_has_a_head_and_images_come_back_in_their_place() -> None:
    drawing, images = scene_drawing.draw(
        scene_of("- a: arrow 10,10 20x0\n- i: image 50,10 10x10 image=x.png\n- b: box 0,0 1x1")
    )
    _, stem, head, box = drawing.items
    assert isinstance(stem, DrawingShape) and stem.fill is None and stem.stroke == colors.GREY_DARK
    assert isinstance(head, DrawingShape) and head.fill == colors.GREY_DARK
    assert isinstance(box, DrawingShape)
    (image,) = images
    assert image.index == 3 and (image.x, image.y, image.width, image.height) == (
        500,
        100,
        100,
        100,
    )


def test_every_kind_for_review(review_dir: Path) -> None:
    drawing, _ = scene_drawing.draw(
        scene_of(
            '- a: box 4,4 30x12 "box"\n- b: round 40,4 30x12 "round" fill=accent3\n'
            '- c: pill 76,4 40x12 "pill" fill=warning\n'
            '- d: circle 122,2 20x20 "circle" fill=primary text=background\n'
            '- e: text 4,30 60x6 "text" bold\n- f: line 4,45 60x10\n'
            "- g: arrow 80,45 60x-10 line=danger\n"
        )
    )
    (review_dir / "scene.svg").write_text(to_svg(drawing), encoding="utf-8")
