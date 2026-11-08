"""Check that mermaid blocks are drawn here, or draw one Mermaid file as SVG and PNG (E06-S03).

usage: ./run.sh mermaid                 check the setup: find mmdc, draw a small flowchart
       ./run.sh mermaid <file.mmd> ...  draw each file to .tmp/mermaid/<name>.svg (the drawing
                                        as the generators see it) and <name>.png

mermaid-cli lives next to this file (package.json, installed by ./run.sh setup with npm ci).
Exit code 1 when mermaid-cli cannot draw.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pta_documents.design.variants import Language
from pta_documents.diagrams.mermaid import MermaidRenderer, find_command, setup_hint
from pta_documents.drawing.svg_output import to_svg
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common.renderers import (
    CodeBlockRequest,
    DrawingGraphic,
    RendererUnavailableError,
)

REPO = Path(__file__).resolve().parents[2]
OUTPUT = REPO / ".tmp" / "mermaid"
SAMPLE = "flowchart LR\n  A[Markdown] --> B{Mermaid?}\n  B -->|ja| C[Formen]\n"


def draw(code: str) -> DrawingGraphic:
    request = CodeBlockRequest("mermaid", code, None, DocumentFormat.PPTX, Language.DE)
    graphic = MermaidRenderer().render(request)
    if not isinstance(graphic, DrawingGraphic):
        raise ValueError("not a supported diagram type")
    return graphic


def main(argv: list[str]) -> int:
    command = find_command()
    if command is None:
        print(setup_hint())
        return 1
    print(f"mmdc: {command}")
    try:
        if not argv:
            graphic = draw(SAMPLE)
            print(f"ok: the test diagram has {len(graphic.drawing.items)} shapes and texts")
            return 0
        OUTPUT.mkdir(parents=True, exist_ok=True)
        for name in argv:
            source = Path(name)
            svg = to_svg(draw(source.read_text(encoding="utf-8")).drawing)
            target = OUTPUT / (source.stem + ".svg")
            target.write_text(svg, encoding="utf-8")
            print(f"wrote {target.relative_to(REPO)}")
            try:
                from pta_documents.svg.converter import to_png
            except ImportError:
                continue
            png = target.with_suffix(".png")
            png.write_bytes(to_png(svg))
            print(f"wrote {png.relative_to(REPO)}")
    except (RendererUnavailableError, ValueError) as error:
        print(f"error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
