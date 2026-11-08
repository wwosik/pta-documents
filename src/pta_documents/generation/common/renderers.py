"""Code-block renderers: turn a fenced code block (``mermaid``, ``chart`` …) into a graphic.

Port of DocLibs ``CodeBlockRenderer.cs``. The generators ask their renderers in order; the first
graphic wins, and a block nobody renders stays code. Every error of a renderer reaches the caller
as ``DocumentConversionError`` in the generator's format.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from pta_documents.charts.spec import ChartSpec
from pta_documents.design.variants import Language
from pta_documents.drawing.model import Drawing
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.markdown.document import DocumentResource


@dataclass(frozen=True, slots=True)
class CodeBlockRequest:
    """A fenced code block to render."""

    info: str
    """The info string after the opening fence, e.g. ``mermaid`` or ``chart bar``."""
    code: str
    """The block's content."""
    line: int | None
    """The line of the opening fence, from 1, front matter included; None if unknown."""
    format: DocumentFormat
    """The format being generated (DOCX, PPTX, later PDF)."""
    language: Language
    """The document language (``sprache:``), for generated texts and number formats."""
    dark: bool = False
    """The graphic sits on a dark slide (``## Title {.dark}``); colours come from design.colors."""


@dataclass(frozen=True, slots=True)
class DrawingGraphic:
    """A vector drawing of the drawing model (``pta_documents.drawing``)."""

    drawing: Drawing


@dataclass(frozen=True, slots=True)
class ImageGraphic:
    """An image, placed like a Markdown image whose alt text is the info string."""

    image: DocumentResource


@dataclass(frozen=True, slots=True)
class ChartGraphic:
    """A chart: native and editable where the format has charts, else ``drawing``."""

    chart: ChartSpec
    drawing: Drawing


CodeBlockGraphic = DrawingGraphic | ImageGraphic | ChartGraphic


class RendererUnavailableError(Exception):
    """A renderer that takes the block cannot draw it here — its tool is not set up, or the
    format has no place for its graphic yet. The block stays code, with a ``code-not-drawn``
    note whose message is this error's (what to set up)."""


class CodeBlockRenderer(Protocol):
    """Turns fenced code blocks of a language it knows into a graphic."""

    def render(self, request: CodeBlockRequest) -> CodeBlockGraphic | None:
        """The graphic for the block, or None when the block is not this renderer's."""
        ...

    @property
    def authoring_guide(self) -> str | None:
        """What a Markdown writer needs to know about this renderer's blocks: German Markdown
        under a ``##`` heading of its own, for the authoring guides (E02-S05); None: nothing."""
        ...


def default_renderers() -> tuple[CodeBlockRenderer, ...]:
    """The renderers the generators use unless their options say otherwise: every renderer of
    the library that is available: the chart renderer (E06-S01, core) and, when mermaid-cli is
    found, the Mermaid renderer (E06-S03)."""
    from pta_documents.charts.renderer import ChartRenderer
    from pta_documents.diagrams.mermaid import MermaidRenderer, find_command

    if find_command() is None:
        return (ChartRenderer(),)
    return (ChartRenderer(), MermaidRenderer())


def render(
    renderers: Sequence[CodeBlockRenderer], request: CodeBlockRequest
) -> CodeBlockGraphic | None:
    """The first graphic of ``renderers`` for ``request``; None when no renderer takes it.

    A ``DocumentConversionError`` or ``RendererUnavailableError`` of a renderer passes
    unchanged; any other exception becomes a
    ``DocumentConversionError`` in ``request.format`` with the original as ``__cause__``.
    """
    for renderer in renderers:
        try:
            graphic = renderer.render(request)
        except (DocumentConversionError, RendererUnavailableError):
            raise
        except Exception as error:
            raise DocumentConversionError(request.format, str(error)) from error
        if graphic is not None:
            return graphic
    return None
