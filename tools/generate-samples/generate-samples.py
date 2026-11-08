"""Generate the documents of a sample folder under samples/ into .tmp/samples/<name>/.

usage: ./run.sh generate-samples <name> [<name> ...]   (no name: all samples)

``*-bericht.md`` / ``*-dokument.md`` becomes a DOCX, ``*-praesentation.md`` / ``*-folien.md`` a
PPTX (the names ``./run.sh generate`` knows); images are taken from the
sample's ``images/`` folder as document resources. A file with ``fassung: intern`` or
``trainer`` (E16-S01) gets ``-intern``/``-trainer`` in its name, as with ``./run.sh generate``.
The notes of each file follow it; samples are meant to produce none, so any note makes the exit
code 1.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pta_documents.errors import DocumentFormat
from pta_documents.generation.common import audience
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of

REPO = Path(__file__).resolve().parents[2]
SAMPLES = REPO / "samples"
OUTPUT = REPO / ".tmp" / "samples"
DOCX_SUFFIXES = ("-bericht", "-dokument")
PPTX_SUFFIXES = ("-praesentation", "-folien")


def resources(folder: Path) -> list[DocumentResource]:
    return [
        DocumentResource(
            str(path.relative_to(folder)).replace("\\", "/"),
            content_type_of(path.name),
            path.read_bytes(),
        )
        for path in sorted((folder / "images").glob("*"))
        if path.is_file()
    ]


def generate(name: str) -> bool:
    """Generate one sample folder; False if a file had notes."""
    folder = SAMPLES / name
    target = OUTPUT / name
    target.mkdir(parents=True, exist_ok=True)
    images = resources(folder)
    clean = True
    for source in sorted(folder.glob("*.md")):
        document = MarkdownDocument(source.read_text(encoding="utf-8"), images)
        if source.stem.endswith(DOCX_SUFFIXES):
            suffix = audience.of(document.text, DocumentFormat.DOCX).suffix
            out = target / (source.stem + suffix + ".docx")
            with out.open("wb") as stream:
                result = DocxGenerator().generate(document, stream)
        elif source.stem.endswith(PPTX_SUFFIXES):
            suffix = audience.of(document.text, DocumentFormat.PPTX).suffix
            out = target / (source.stem + suffix + ".pptx")
            with out.open("wb") as stream:
                result = PptxGenerator().generate(document, stream)
        else:
            continue
        print(f"wrote {out.relative_to(REPO)}")
        for note in result.notes:
            print(f"  - {note}")
        clean &= not result.notes
    return clean


def main(argv: list[str]) -> int:
    names = argv or sorted(p.name for p in SAMPLES.iterdir() if p.is_dir())
    clean = True
    for name in names:
        clean &= generate(name)
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
