"""E10-S02: an HTML deck as one PNG per slide and a contact sheet.

The browser tests need Playwright (extra ``preview``) and its Chromium and are skipped without
them. ``samples/funktionen/funktionen-praesentation.md`` is compared with reference pictures in
``tests/preview/expected/funktionen-praesentation/`` (renew with PTA_DOCUMENTS_UPDATE_EXPECTED=1
and look at the diff before committing it). The pictures land in ``.tmp/review/preview/``.
"""

from __future__ import annotations

import datetime as dt
import io
import os
import sys
from pathlib import Path
from typing import Final

import pytest
from PIL import Image, ImageChops

from pta_documents.charts.renderer import ChartRenderer
from pta_documents.generation.html.generator import HtmlDeckGenerator
from pta_documents.generation.html.options import HtmlDeckOptions
from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of
from pta_documents.preview import (
    PreviewUnavailableError,
    SlidePicture,
    contact_sheet,
    render_deck,
)
from pta_documents.preview import deck as preview_deck
from tests.conftest import REPO_ROOT, REVIEW_DIR
from tests.expected import UPDATE_VARIABLE

PPTX_SAMPLES: Final = REPO_ROOT / "tests" / "generation" / "pptx" / "samples"
FUNKTIONEN: Final = REPO_ROOT / "samples" / "funktionen"
EXPECTED: Final = Path(__file__).parent / "expected" / "funktionen-praesentation"
REVIEW: Final = REVIEW_DIR / "preview"
REFERENCE_SIZE: Final = (800, 450)
"""The reference pictures are the 1600 × 900 slides at half size: a few MB instead of 14."""
PIXEL_TOLERANCE: Final = 16
"""A pixel differs when one of its channels differs by more than this (of 255)."""
SHARE_TOLERANCE: Final = 0.005
"""A picture matches its reference when less than 0.5 % of its pixels differ."""
IMAGE_SUFFIXES: Final = {".png", ".jpg", ".jpeg", ".gif", ".svg"}
THRESHOLD: Final = [255 if v > PIXEL_TOLERANCE else 0 for v in range(256)]
STEPS: Final = "# Deck\n\n## Eins\n\n{marker}- a\n- b\n- c\n"


def deck_html(
    markdown: str,
    resources: tuple[DocumentResource, ...] = (),
    options: HtmlDeckOptions | None = None,
) -> bytes:
    output = io.BytesIO()
    HtmlDeckGenerator().generate(
        MarkdownDocument(markdown, resources),
        output,
        options or HtmlDeckOptions(code_block_renderers=()),
    )
    return output.getvalue()


def slide_count(html: bytes) -> int:
    return html.count(b'<section class="slide"')


def image(png: bytes) -> Image.Image:
    with Image.open(io.BytesIO(png)) as opened:
        return opened.convert("RGB")


def save_review(folder: str, pictures: list[SlidePicture]) -> None:
    target = REVIEW / folder
    target.mkdir(parents=True, exist_ok=True)
    for old in target.glob("*.png"):
        old.unlink()
    for picture in pictures:
        (target / f"folie-{picture.number:02d}.png").write_bytes(picture.png)
    (target / "uebersicht.png").write_bytes(contact_sheet(pictures))


def solid(color: tuple[int, int, int], size: tuple[int, int] = (1600, 900)) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", size, color).save(output, format="PNG")
    return output.getvalue()


# ---------------------------------------------------------------------- without a browser


def test_the_contact_sheet_has_a_tile_per_picture_in_rows() -> None:
    colours = [(200, 0, 0), (0, 200, 0), (0, 0, 200), (200, 200, 0), (0, 200, 200)]
    pictures = [SlidePicture(n, solid(c)) for n, c in enumerate(colours, start=3)]
    sheet = image(contact_sheet(pictures, columns=4))
    gap, label, width = preview_deck.SHEET_GAP, preview_deck.SHEET_LABEL, 400
    tile_height = 225
    assert sheet.size == (gap + 4 * (width + gap), gap + 2 * (tile_height + label + gap))
    for index, colour in enumerate(colours):
        x = gap + (index % 4) * (width + gap) + width // 2
        y = gap + (index // 4) * (tile_height + label + gap) + tile_height // 2
        assert sheet.getpixel((x, y)) == colour
    REVIEW.mkdir(parents=True, exist_ok=True)
    sheet.save(REVIEW / "contact-sheet.png")


def test_a_contact_sheet_of_few_pictures_is_only_as_wide_as_needed() -> None:
    sheet = image(contact_sheet([SlidePicture(1, solid((9, 9, 9)))]))
    assert sheet.width == 2 * preview_deck.SHEET_GAP + 400


def test_a_contact_sheet_needs_pictures() -> None:
    with pytest.raises(ValueError, match="at least one"):
        contact_sheet([])


def test_without_playwright_the_preview_says_what_to_install(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)
    with pytest.raises(PreviewUnavailableError, match=r"\[preview\].*playwright install chromium"):
        render_deck(b"<html><head></head><body></body></html>")
    assert preview_deck.chromium_available() is False


def test_the_preview_style_goes_into_the_head() -> None:
    html = deck_html("# Deck\n\n## Eins\n\nText\n")
    styled = preview_deck._with_preview_style(html)
    head = styled[: styled.index(b"</head>")]
    assert b'font-family:"Segoe UI"' in head and b'font-family:"Consolas"' in head
    assert preview_deck.PREVIEW_CSS.encode() in head
    with pytest.raises(ValueError, match="no </head>"):
        preview_deck._with_preview_style(b"<p>no page</p>")


# ---------------------------------------------------------------------- in the browser


@pytest.mark.usefixtures("browser")
def test_every_slide_becomes_a_1600_by_900_picture() -> None:
    html = deck_html(
        (PPTX_SAMPLES / "deck.md").read_text(encoding="utf-8"),
        (
            DocumentResource(
                "diagram.png", "image/png", (PPTX_SAMPLES / "diagram.png").read_bytes()
            ),
        ),
    )
    pictures = render_deck(html)
    save_review("deck", pictures)
    assert [p.number for p in pictures] == list(range(1, slide_count(html) + 1))
    for picture in pictures:
        shown = image(picture.png)
        assert shown.size == (1600, 900)
        assert shown.getextrema() != ((255, 255), (255, 255), (255, 255)), picture.number
    sheet = image(contact_sheet(pictures))
    rows = -(-len(pictures) // 4)
    gap, label = preview_deck.SHEET_GAP, preview_deck.SHEET_LABEL
    assert sheet.size == (gap + 4 * (400 + gap), gap + rows * (225 + label + gap))


@pytest.mark.usefixtures("browser")
def test_a_selection_at_double_scale() -> None:
    html = deck_html("# Deck\n\n## Eins\n\nText\n\n## Zwei\n\nMehr\n")
    pictures = render_deck(html, scale=2, slides={3, 99})
    assert [p.number for p in pictures] == [3]
    assert image(pictures[0].png).size == (3200, 1800)


@pytest.mark.usefixtures("browser")
def test_two_runs_give_the_same_pictures() -> None:
    html = deck_html("# Deck\n\n## Eins\n\n**Fett** und *kursiv*\n\n- a\n- b\n")
    first = render_deck(html)
    second = render_deck(html)
    assert [p.png for p in first] == [p.png for p in second]


@pytest.mark.usefixtures("browser")
def test_a_slide_with_builds_shows_every_step() -> None:
    built = render_deck(deck_html(STEPS.format(marker="{.build}\n")), slides={2})
    still = render_deck(deck_html(STEPS.format(marker="")), slides={2})
    save_review("builds", built)
    assert built[0].png == still[0].png


def funktionen_html() -> bytes:
    resources = tuple(
        DocumentResource(
            path.relative_to(FUNKTIONEN).as_posix(), content_type_of(path.name), path.read_bytes()
        )
        for path in sorted(FUNKTIONEN.rglob("*"))
        if path.is_file()
        and path.suffix.lower() in IMAGE_SUFFIXES
        and "vorschau" not in path.relative_to(FUNKTIONEN).parts
    )
    return deck_html(
        (FUNKTIONEN / "funktionen-praesentation.md").read_text(encoding="utf-8"),
        resources,
        # Charts are drawn by the library itself; Mermaid would depend on the machine.
        HtmlDeckOptions(code_block_renderers=(ChartRenderer(),), date=dt.date(2026, 11, 6)),
    )


def reference(png: bytes) -> Image.Image:
    return image(png).resize(REFERENCE_SIZE, Image.Resampling.LANCZOS)


def differing_share(actual: Image.Image, expected: Image.Image) -> float:
    difference = ImageChops.difference(actual, expected)
    channels = [band.point(THRESHOLD) for band in difference.split()]
    mask = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
    histogram = mask.histogram()
    return histogram[255] / (actual.width * actual.height)


@pytest.mark.usefixtures("browser")
def test_the_feature_tour_looks_like_its_reference_pictures() -> None:
    pictures = render_deck(funktionen_html())
    save_review("funktionen-praesentation", pictures)
    names = [f"folie-{p.number:02d}.png" for p in pictures]
    if os.environ.get(UPDATE_VARIABLE) == "1":
        EXPECTED.mkdir(parents=True, exist_ok=True)
        for old in EXPECTED.glob("*.png"):
            old.unlink()
        for name, picture in zip(names, pictures, strict=True):
            reference(picture.png).save(EXPECTED / name, format="PNG", optimize=True)
        return
    expected_names = sorted(p.name for p in EXPECTED.glob("*.png"))
    assert names == expected_names, f"the slides changed; run with {UPDATE_VARIABLE}=1"
    worse: list[str] = []
    for name, picture in zip(names, pictures, strict=True):
        with Image.open(EXPECTED / name) as opened:
            expected = opened.convert("RGB")
        share = differing_share(reference(picture.png), expected)
        if share >= SHARE_TOLERANCE:
            worse.append(f"{name}: {share:.2%} of the pixels differ")
    assert worse == [], (
        "\n".join(worse) + f"\nsee .tmp/review/preview/funktionen-praesentation/; "
        f"if the change is meant, run with {UPDATE_VARIABLE}=1"
    )
