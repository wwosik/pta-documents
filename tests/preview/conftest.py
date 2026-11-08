"""Shared by the preview tests: whether Chromium starts here (else the browser tests skip)."""

from __future__ import annotations

import functools

import pytest

from pta_documents.preview import chromium_available


@functools.cache
def _browser_works() -> bool:
    return chromium_available()


@pytest.fixture
def browser() -> None:
    """Skips the test without Playwright (extra ``preview``) or its Chromium."""
    if not _browser_works():
        pytest.skip("Playwright or its Chromium is not available (extra 'preview')")
