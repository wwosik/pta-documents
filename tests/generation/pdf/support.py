"""Reading generated PDFs back: the text of the type area, without header and footer (E05-S03)."""

from __future__ import annotations

import io
from typing import Any

import pdfplumber

from pta_documents.design import word_styles
from pta_documents.design.variants import WordVariant


def type_area(page: Any) -> Any:
    """``page`` (pdfplumber) cropped to the type area of the template of its orientation."""
    portrait = float(page.height) > float(page.width)
    variant = WordVariant.PORTRAIT_NO_COVER if portrait else WordVariant.LANDSCAPE_NO_COVER
    setup = word_styles.read(variant).page
    return page.crop((0, setup.top_pt, page.width, page.height - setup.bottom_pt))


def body_texts(data: bytes) -> list[str]:
    """The text of the type area of every page."""
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return [type_area(page).extract_text() or "" for page in pdf.pages]
