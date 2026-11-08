"""What a host offers through the tool ``make_document`` (E08-S04)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from pta_documents.errors import DocumentFormat

if TYPE_CHECKING:  # the PDF options need the extra ``pdf``; the tool imports them only when used
    from pta_documents.generation.docx.options import DocxOptions
    from pta_documents.generation.pdf.options import PdfOptions
    from pta_documents.generation.pptx.options import PptxOptions

DEFAULT_NAME: Final = "make_document"

NAME_PATTERN: Final = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
"""The tool names the Anthropic and the OpenAI API take."""

FORMATS: Final = (DocumentFormat.DOCX, DocumentFormat.PPTX, DocumentFormat.PDF)
"""The formats the tool can offer, in the order the schema and the guide name them."""


@dataclass(frozen=True)
class ToolOptions:
    """The formats the tool offers, each with the options of its generator; ``None`` means the
    format is not offered. At least one must be set.

    ``host_notes`` is Markdown the host adds to the guide (how links are shown, where files go);
    it comes under ``## In dieser Anwendung`` unless it starts with a heading of its own.
    """

    docx: DocxOptions | None = None
    pptx: PptxOptions | None = None
    pdf: PdfOptions | None = None
    name: str = DEFAULT_NAME
    host_notes: str | None = None

    def __post_init__(self) -> None:
        if self.docx is None and self.pptx is None and self.pdf is None:
            raise ValueError("The tool needs at least one format: set docx, pptx or pdf.")
        if not NAME_PATTERN.match(self.name):
            raise ValueError(
                f"The tool name '{self.name}' is not valid: 1 to 64 letters, digits, '_' or '-'."
            )

    @property
    def formats(self) -> tuple[DocumentFormat, ...]:
        """The formats offered, in the order of ``FORMATS``."""
        offered = (self.docx, self.pptx, self.pdf)
        return tuple(f for f, o in zip(FORMATS, offered, strict=True) if o is not None)
