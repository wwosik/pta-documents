"""Shared by the handout tests: whether Chromium starts here (else the browser tests skip)."""

from __future__ import annotations

import pytest

from tests.preview.conftest import _browser_works  # pyright: ignore[reportPrivateUsage]


@pytest.fixture
def browser() -> None:
    """Skips the test without Playwright (extra ``preview``) or its Chromium."""
    if not _browser_works():
        pytest.skip("Playwright or its Chromium is not available (extra 'preview')")
