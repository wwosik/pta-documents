"""Print the authoring guide of a generator (E02-S05).

usage: ./run.sh authoring-guide docx|pptx|pdf

Writes the guide (German Markdown from ``##``) of the generator with its default options to
standard output, to hand to writers — people or AI agents — who have no Python. A generator
offers a guide once it has ``authoring_guide()`` (Word E03-S05, PowerPoint E04-S06, PDF
E05-S05); until then the tool says so and ends with exit code 1. The PDF needs the extra
``pdf``. Wrong arguments end with exit code 2.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from typing import Final, cast

GENERATORS: Final = {
    "docx": ("pta_documents.generation.docx.generator", "DocxGenerator"),
    "pptx": ("pta_documents.generation.pptx.generator", "PptxGenerator"),
    "pdf": ("pta_documents.generation.pdf", "PdfGenerator"),
}
"""The generator of each format: its module and class, imported only when asked for."""


class NoGuideError(Exception):
    """The generator of the format offers no authoring guide (yet), or cannot be loaded."""


def guide(format: str) -> str:
    """The authoring guide of the generator of ``format`` with its default options.

    Raises ``KeyError`` for an unknown format and ``NoGuideError`` when the generator has no
    guide or its extra is missing."""
    module_name, class_name = GENERATORS[format]
    try:
        module = importlib.import_module(module_name)
    except ImportError as error:
        raise NoGuideError(str(error)) from error
    generator = getattr(module, class_name)()
    method = getattr(generator, "authoring_guide", None)
    if not callable(method):
        raise NoGuideError(f"The {format} generator offers no authoring guide yet.")
    return cast(Callable[[], str], method)()


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0].lower() not in GENERATORS:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        text = guide(argv[0].lower())
    except NoGuideError as error:
        print(error, file=sys.stderr)
        return 1
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
