from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Final

from pta_documents.generation.html.generator import HtmlDeckGenerator
from pta_documents.generation.html.options import HtmlDeckOptions
from pta_documents.markdown import DocumentResource, MarkdownDocument

REPO_ROOT: Final = Path(__file__).resolve().parents[3]
REVIEW: Final = REPO_ROOT / ".tmp" / "review"
PLAIN: Final = HtmlDeckOptions(code_block_renderers=())
"""Without renderers: what the deck shows does not depend on the machine (mermaid-cli)."""


def generate(
    markdown: str,
    options: HtmlDeckOptions | None = None,
    resources: tuple[DocumentResource, ...] = (),
) -> str:
    output = io.BytesIO()
    HtmlDeckGenerator().generate(MarkdownDocument(markdown, resources), output, options or PLAIN)
    return output.getvalue().decode("utf-8")


def review(name: str, html: str) -> Path:
    """Write ``html`` to ``.tmp/review/<name>`` to look at."""
    REVIEW.mkdir(parents=True, exist_ok=True)
    path = REVIEW / name
    path.write_text(html, encoding="utf-8", newline="\n")
    return path


_SECTION = re.compile(r'<section [^>]*aria-label="([^"]*)"')


def slide_labels(html: str) -> list[str]:
    return _SECTION.findall(html)
