"""E10-S01 in a browser: the deck loads without errors, the keys change slides, print gives a
page per slide. Needs Playwright (extra ``preview``) and its Chromium; skipped without them."""

from __future__ import annotations

import importlib
import io
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Final

import pytest

from tests.generation.html.conftest import generate, review

DECK: Final = (
    "---\nuebergang: fade\n---\n# Deck\n\nSub\n\n# Kapitel\n\n## Eins\n\n{.build}\n- a\n- b\n\n"
    "::: notes\nSag **das**.\n:::\n\n## Zwei\n\nText\n"
)
"""Title, chapter, "Eins" with two steps, "Zwei": four slides."""


@pytest.fixture(scope="module")
def browser() -> Iterator[Any]:
    try:
        sync_api: Any = importlib.import_module("playwright.sync_api")
    except ImportError:
        pytest.skip("Playwright is not installed (extra 'preview')")
    manager = sync_api.sync_playwright().start()
    try:
        launched = manager.chromium.launch()
    except Exception as error:  # no browser installed for Playwright
        manager.stop()
        pytest.skip(f"Chromium for Playwright does not start: {error}")
    yield launched
    launched.close()
    manager.stop()


@pytest.fixture(scope="module")
def deck_file() -> Path:
    return review("browser.html", generate(DECK))


def active(page: Any) -> str:
    return str(page.evaluate("document.querySelector('section.slide.active').id"))


def test_the_deck_loads_without_errors(browser: Any, deck_file: Path) -> None:
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    errors: list[str] = []
    page.on("console", lambda m: errors.append(m.text) if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(deck_file.as_uri())
    page.wait_for_timeout(100)
    assert errors == []
    assert active(page) == "s1"
    page.close()


def test_the_keys_step_through_builds_and_slides(browser: Any, deck_file: Path) -> None:
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    page.goto(deck_file.as_uri() + "#3")
    page.wait_for_timeout(50)
    assert active(page) == "s3"
    shown = "document.querySelectorAll('#s3 [data-build].on').length"
    assert page.evaluate(shown) == 0
    page.keyboard.press("ArrowRight")
    assert active(page) == "s3" and page.evaluate(shown) == 1
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    assert active(page) == "s4"
    page.keyboard.press("ArrowLeft")
    assert active(page) == "s3" and page.evaluate(shown) == 2
    page.keyboard.press("n")
    assert "Sag" in page.inner_text("#notes")
    assert "Folie 3 von 4" in page.inner_text("#live")
    page.close()


def test_print_gives_one_page_per_slide(browser: Any, deck_file: Path) -> None:
    page = browser.new_page()
    page.goto(deck_file.as_uri())
    pdf: bytes = page.pdf(prefer_css_page_size=True, print_background=True)
    page.close()
    pdfplumber: Any = pytest.importorskip("pdfplumber")
    with pdfplumber.open(io.BytesIO(pdf)) as document:
        assert len(document.pages) == 4
        first = document.pages[0]
        assert round(first.width / first.height, 2) == round(16 / 9, 2)
