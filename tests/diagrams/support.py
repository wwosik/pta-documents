"""Helpers for the Mermaid tests: whether mermaid-cli really draws here, the sample blocks, and
drawings as text (port of DocLibs ``DrawingFormat.cs``)."""

from __future__ import annotations

import functools
import re
from pathlib import Path
from typing import Final

import pytest

from pta_documents.design.variants import Language
from pta_documents.diagrams.mermaid import MermaidRenderer, diagram_type, find_command
from pta_documents.drawing import (
    CubicTo,
    Drawing,
    DrawingHotspot,
    DrawingShape,
    DrawingText,
    LineTo,
    MoveTo,
    ShapeKind,
)
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common.renderers import CodeBlockRequest

SAMPLES: Final = Path(__file__).parent / "samples"
DIAGRAMS: Final = SAMPLES / "diagramme.md"


@functools.cache
def mermaid_works() -> bool:
    """Whether mermaid-cli is found and draws a small flowchart (Chromium included)."""
    if find_command() is None:
        return False
    request = CodeBlockRequest(
        "mermaid", "flowchart LR\n  A --> B\n", None, DocumentFormat.PPTX, Language.DE
    )
    try:
        return MermaidRenderer().render(request) is not None
    except Exception:
        return False


def skip_without_mermaid() -> None:
    if not mermaid_works():
        pytest.skip("mermaid-cli is not set up or cannot start Chromium (./run.sh mermaid)")


def blocks(path: Path = DIAGRAMS) -> list[str]:
    """The code of each ``mermaid`` block of a Markdown file."""
    text = path.read_text(encoding="utf-8")
    return re.findall(r"```mermaid\n(.*?)```", text, re.DOTALL)


def block_of(kind: str) -> str:
    return next(code for code in blocks() if diagram_type(code) == kind)


def _n(value: float) -> str:
    text = f"{round(value, 2):.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def write(drawing: Drawing) -> str:
    """A drawing as text, one item per line, for snapshot files that diff well."""
    lines = [f"drawing {_n(drawing.width)} x {_n(drawing.height)}"]
    for item in drawing.items:
        match item:
            case DrawingShape():
                lines.append(_shape(item))
            case DrawingText():
                lines.append(_text(item))
            case DrawingHotspot():
                lines.append(f"hotspot {_n(item.x)} {_n(item.y)}")
    return "\n".join(lines) + "\n"


def _shape(shape: DrawingShape) -> str:
    names = {
        ShapeKind.RECTANGLE: "rect",
        ShapeKind.ROUNDED_RECTANGLE: "roundrect",
        ShapeKind.ELLIPSE: "ellipse",
        ShapeKind.PATH: "path",
    }
    line = f"{names[shape.kind]} fill={shape.fill or 'none'} stroke={shape.stroke or 'none'}"
    if shape.stroke is not None:
        line += f" w={_n(shape.stroke_width)}"
    if shape.dash is not None:
        line += " dash=" + ",".join(_n(d) for d in shape.dash)
    if shape.round_joins:
        line += " round"
    if shape.even_odd:
        line += " evenodd"
    if shape.kind is not ShapeKind.PATH:
        x, y, w, h = shape.path.bounds
        line += f" at {_n(x)} {_n(y)} size {_n(w)} {_n(h)}"
        if shape.kind is ShapeKind.ROUNDED_RECTANGLE:
            line += f" r={_n(shape.corner_radius)}"
        return line
    line += " :"
    for segment in shape.path.segments:
        match segment:
            case MoveTo(x, y):
                line += f" M {_n(x)} {_n(y)}"
            case LineTo(x, y):
                line += f" L {_n(x)} {_n(y)}"
            case CubicTo(x1, y1, x2, y2, x, y):
                line += f" C {_n(x1)} {_n(y1)} {_n(x2)} {_n(y2)} {_n(x)} {_n(y)}"
            case _:
                line += " Z"
    return line


def _text(text: DrawingText) -> str:
    line = (
        f"text {_n(text.x)} {_n(text.baseline)} {text.anchor.value} size={_n(text.size)} "
        f"color={text.color}"
    )
    if text.max_width is not None:
        line += f" max={_n(text.max_width)}"
    if text.mono:
        line += " mono"
    line += " :"
    for span in text.spans:
        marks = "**" if span.bold else ""
        line += f' {marks}"{span.text}"{marks}'
    return line


def drawable(markdown: str) -> bool:
    """Whether a sample can generate without notes here: it has no ``mermaid`` block, or
    mermaid-cli works (samples with Mermaid are left out where it is not set up)."""
    return "```mermaid" not in markdown or mermaid_works()
