from __future__ import annotations

import io
from typing import Any

import pptx
from pptx.presentation import Presentation
from pptx.slide import Slide

from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import DocumentResource, MarkdownDocument


def generate(
    markdown: str,
    options: PptxOptions | None = None,
    resources: tuple[DocumentResource, ...] = (),
) -> bytes:
    output = io.BytesIO()
    PptxGenerator().generate(MarkdownDocument(markdown, resources), output, options)
    return output.getvalue()


def open_pptx(data: bytes) -> Presentation:
    return pptx.Presentation(io.BytesIO(data))


def layout_names(data: bytes) -> list[str]:
    return [s.slide_layout.name for s in open_pptx(data).slides]


def texts(slide: Slide) -> dict[int, str]:
    """Placeholder idx -> text."""
    result: dict[int, str] = {}
    for shape in slide.placeholders:
        any_shape: Any = shape
        if any_shape.has_text_frame:
            result[shape.placeholder_format.idx] = any_shape.text_frame.text
    return result


def placeholder_texts(slide: Slide) -> dict[str, str]:
    """Placeholder type name (FOOTER, SLIDE_NUMBER, …) -> text."""
    result: dict[str, str] = {}
    for shape in slide.placeholders:
        any_shape: Any = shape
        if any_shape.has_text_frame:
            result[str(shape.placeholder_format.type).split(" ")[0]] = any_shape.text_frame.text
    return result
