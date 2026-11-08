"""E15-S03: a bundled icon as a PNG without any extra."""

from __future__ import annotations

import io

from PIL import Image

from pta_documents.design.icons import loader, raster


def test_the_png_is_transparent_and_coloured() -> None:
    data = raster.png("check", "006FB9", 64)
    with Image.open(io.BytesIO(data)) as picture:
        assert picture.size == (64, 64) and picture.mode == "RGBA"
        assert picture.getpixel((0, 0))[3] == 0  # type: ignore[index]
        raw = picture.tobytes()
    pixels = [tuple(raw[k : k + 4]) for k in range(0, len(raw), 4)]
    opaque = [p for p in pixels if p[3] == 255]
    assert opaque and all(p[:3] == (0, 0x6F, 0xB9) for p in opaque)


def test_the_same_icon_gives_the_same_bytes() -> None:
    assert raster.png("users", "FFFFFF", 48) == raster.png("users", "FFFFFF", 48)


def test_the_png_names_its_icon() -> None:
    assert raster.name_of(raster.png("bulb", "006FB9", 32)) == "bulb"
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4)).save(buffer, "PNG")
    assert raster.name_of(buffer.getvalue()) is None
    assert raster.name_of(b"GIF89a") is None


def test_curves_become_straight_pieces() -> None:
    lines = raster.polylines(loader.outlines("circle-check")[0])
    assert len(lines[0]) > raster.CURVE_STEPS
