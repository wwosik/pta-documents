from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_TEMPLATES = REPO_ROOT / "source-templates"
REVIEW_DIR = REPO_ROOT / ".tmp" / "review"


@pytest.fixture
def review_dir() -> Path:
    """Where tests put generated files for a human to look at."""
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    return REVIEW_DIR
