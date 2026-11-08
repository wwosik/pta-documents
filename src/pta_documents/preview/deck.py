"""An HTML deck (E10-S01) as one PNG per slide and a contact sheet (E10-S02).

``render_deck`` opens the deck in a headless Chromium (Playwright, extra ``preview``) and takes
a screenshot of every slide on the stage of the deck — 1600 px wide, as high as the slides —
without the page around it (chapters, progress, key hint, notes). A slide with builds shows its
final state, every step done. The pictures are the same on every run: the deck is served from
memory (nothing is fetched, nothing written), motion is reduced, and the fonts of the slides are
pinned to the embedded ones — "Segoe UI" is Selawik and "Consolas" Inconsolata, even where the
machine has Segoe UI — so that a machine's fonts do not change the line breaks.

``contact_sheet`` puts the pictures side by side with their slide numbers (Pillow).
"""

from __future__ import annotations

import base64
import importlib
import io
import math
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, Final

from PIL import Image, ImageDraw, ImageFont

from pta_documents.design import colors, fonts
from pta_documents.generation.html.writer import FONT_FACES

INSTALL_HINT: Final = (
    "The preview needs Playwright and its Chromium: "
    "'.venv/bin/pip install -e .[preview]' and '.venv/bin/python -m playwright install chromium' "
    "(or ./run.sh setup)."
)
URL: Final = "https://deck.preview/"
"""Where the page is served from memory; every other request is refused."""
STAGE_WIDTH: Final = 1600
LAUNCH_ARGS: Final = ("--font-render-hinting=none",)
PINNED_FAMILIES: Final = {"Selawik": "Segoe UI", "Inconsolata": "Consolas"}
"""The embedded fonts and the family names of the slides they stand for in the preview."""
TIMEOUT_MS: Final = 30_000

PREVIEW_CSS: Final = (
    "#deck{left:0!important;top:0!important;transform:none!important;box-shadow:none!important}"
    "#chapters,#progress,#hint,#notes,#live{display:none!important}"
    "*,*::before,*::after{animation:none!important;transition:none!important}"
)
"""The stage at the top left at its own size, nothing of the page around it."""

SETTLE_JS: Final = """async (n) => {
  const slide = document.getElementById('s' + n);
  slide.querySelectorAll('[data-build]').forEach((b) => b.classList.add('on'));
  await document.fonts.ready;
  await new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)));
}"""
"""Every build of slide ``n`` on (the final state), then wait for fonts and two frames."""

SHEET_TILE_WIDTH: Final = 400
SHEET_GAP: Final = 16
SHEET_LABEL: Final = 30
SHEET_FONT_SIZE: Final = 18


class PreviewUnavailableError(RuntimeError):
    """Playwright or its Chromium is missing; the message says how to install them."""


@dataclass(frozen=True)
class SlidePicture:
    number: int
    """The slide number, from 1."""
    png: bytes


def render_deck(
    html: bytes, *, scale: int = 1, slides: Collection[int] | None = None
) -> list[SlidePicture]:
    """One PNG per slide of the HTML deck ``html``, in slide order.

    ``scale`` multiplies the pixels (2 gives 3200 × 1800 for 16:9); ``slides`` limits the
    pictures to these slide numbers (numbers beyond the deck are left out). Raises
    ``PreviewUnavailableError`` without Playwright or Chromium.
    """
    if scale < 1:
        raise ValueError(f"scale must be at least 1, not {scale}")
    page_html = _with_preview_style(html)
    manager = _start_playwright()
    try:
        browser = _launch(manager)
        try:
            context = browser.new_context(
                viewport={"width": STAGE_WIDTH, "height": 900},
                device_scale_factor=scale,
                reduced_motion="reduce",
                color_scheme="light",
                locale="de-DE",
                timezone_id="Europe/Berlin",
            )
            context.route("**/*", lambda route: _serve(route, page_html))
            page = context.new_page()
            page.set_default_timeout(TIMEOUT_MS)
            page.goto(URL + "#1")
            count = int(page.evaluate("document.querySelectorAll('section.slide').length"))
            height = int(page.evaluate("document.getElementById('deck').offsetHeight") or 900)
            page.set_viewport_size({"width": STAGE_WIDTH, "height": height})
            wanted = [n for n in range(1, count + 1) if slides is None or n in slides]
            pictures: list[SlidePicture] = []
            for number in wanted:
                page.evaluate("(n) => { location.hash = '#' + n; }", number)
                page.wait_for_function(
                    "(n) => document.getElementById('s' + n).classList.contains('active')",
                    arg=number,
                )
                page.evaluate(SETTLE_JS, number)
                png: bytes = page.screenshot(
                    type="png",
                    animations="disabled",
                    caret="hide",
                    clip={"x": 0, "y": 0, "width": STAGE_WIDTH, "height": height},
                )
                pictures.append(SlidePicture(number, png))
            context.close()
            return pictures
        finally:
            browser.close()
    finally:
        manager.stop()


def chromium_available() -> bool:
    """Whether Playwright is installed and its Chromium starts."""
    try:
        manager = _start_playwright()
    except PreviewUnavailableError:
        return False
    try:
        _launch(manager).close()
        return True
    except PreviewUnavailableError:
        return False
    finally:
        manager.stop()


def contact_sheet(pictures: Sequence[SlidePicture], columns: int = 4) -> bytes:
    """The pictures as tiles in rows of ``columns``, each with its slide number under it; PNG."""
    if not pictures:
        raise ValueError("a contact sheet needs at least one picture")
    if columns < 1:
        raise ValueError(f"columns must be at least 1, not {columns}")
    tiles: list[tuple[int, Image.Image]] = []
    for picture in pictures:
        with Image.open(io.BytesIO(picture.png)) as image:
            rgb = image.convert("RGB")
        height = round(rgb.height * SHEET_TILE_WIDTH / rgb.width)
        tiles.append(
            (picture.number, rgb.resize((SHEET_TILE_WIDTH, height), Image.Resampling.LANCZOS))
        )
    tile_height = max(tile.height for _, tile in tiles)
    columns = min(columns, len(tiles))
    rows = math.ceil(len(tiles) / columns)
    cell_w = SHEET_TILE_WIDTH + SHEET_GAP
    cell_h = tile_height + SHEET_LABEL + SHEET_GAP
    sheet = Image.new(
        "RGB", (SHEET_GAP + columns * cell_w, SHEET_GAP + rows * cell_h), _rgb(colors.GREY_LIGHT)
    )
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(io.BytesIO(fonts.read("Selawik-Regular.ttf")), SHEET_FONT_SIZE)
    for index, (number, tile) in enumerate(tiles):
        x = SHEET_GAP + (index % columns) * cell_w
        y = SHEET_GAP + (index // columns) * cell_h
        sheet.paste(tile, (x, y))
        draw.rectangle(
            (x, y, x + tile.width - 1, y + tile.height - 1), outline=_rgb(colors.GREY_DARK)
        )
        draw.text(
            (x + SHEET_TILE_WIDTH / 2, y + tile.height + SHEET_LABEL / 2),
            str(number),
            fill=_rgb(colors.TEXT_SLIDES),
            font=font,
            anchor="mm",
        )
    output = io.BytesIO()
    sheet.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _rgb(hex_color: str) -> tuple[int, int, int]:
    value = int(hex_color, 16)
    return (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF


def _pinned_font_faces() -> str:
    rules: list[str] = []
    for family, weight, name in FONT_FACES:
        data = base64.b64encode(fonts.read(name)).decode("ascii")
        rules.append(
            f'@font-face{{font-family:"{PINNED_FAMILIES[family]}";font-weight:{weight};'
            f"font-style:normal;src:url(data:font/ttf;base64,{data}) format('truetype')}}"
        )
    return "\n".join(rules)


def _with_preview_style(html: bytes) -> bytes:
    """``html`` with the preview's own style before ``</head>`` (the deck allows inline style)."""
    style = f"<style>\n{_pinned_font_faces()}\n{PREVIEW_CSS}\n</style>\n".encode()
    head_end = html.find(b"</head>")
    if head_end < 0:
        raise ValueError("not an HTML deck: there is no </head>")
    return html[:head_end] + style + html[head_end:]


def _serve(route: Any, page_html: bytes) -> None:
    if route.request.url.split("#", 1)[0] == URL:
        route.fulfill(status=200, content_type="text/html; charset=utf-8", body=page_html)
    else:
        route.abort()


def _start_playwright() -> Any:
    try:
        sync_api: Any = importlib.import_module("playwright.sync_api")
    except ImportError as error:
        raise PreviewUnavailableError(f"Playwright is not installed. {INSTALL_HINT}") from error
    return sync_api.sync_playwright().start()


def _launch(manager: Any) -> Any:
    try:
        return manager.chromium.launch(headless=True, args=list(LAUNCH_ARGS))
    except Exception as error:  # Playwright raises its own Error for a missing browser
        first_line = str(error).strip().splitlines()[0] if str(error).strip() else type(error)
        raise PreviewUnavailableError(
            f"Chromium does not start ({first_line}). {INSTALL_HINT}"
        ) from error
