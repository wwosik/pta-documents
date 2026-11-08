"""The seam between the PDF generator and its layout engine.

The generator reads the front matter, parses and checks the Markdown and hands a
``BodySource`` to a ``BodyLayout``; that returns the laid-out pages, which the generator renders
and turns into PDF/A. Which layout runs is ``generator.BODY_LAYOUT``: the interim
``simple_layout.lay_out`` until the layout engine of E05-S02 replaces it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from markdown_it.token import Token

from pta_documents.design.variants import GeneratedTexts
from pta_documents.generation.common.result import Notes
from pta_documents.generation.pdf.fonts import FontMetrics
from pta_documents.generation.pdf.options import PdfOptions
from pta_documents.generation.pdf.page_model import Layout
from pta_documents.markdown.document import MarkdownDocument
from pta_documents.markdown.front_matter import FrontMatter


@dataclass(frozen=True)
class BodySource:
    """Everything a layout engine gets: the checked tokens and what they came from."""

    tokens: Sequence[Token]
    """The block tokens of ``front.body`` after ``layout_syntax.check``."""
    document: MarkdownDocument
    """For the resources (images) and the metadata."""
    front: FrontMatter
    """``front.body_line`` is the line offset for notes and errors."""
    options: PdfOptions
    """After the front matter was applied."""
    texts: GeneratedTexts
    notes: Notes
    """Where the layout records what it had to work around."""


class BodyLayout(Protocol):
    def __call__(self, source: BodySource, fonts: FontMetrics) -> Layout:
        """The pages of ``source``; at least one, even for an empty document."""
        ...
