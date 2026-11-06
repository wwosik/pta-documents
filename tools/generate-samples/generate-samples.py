"""Generate the documents of a sample folder under samples/ into .tmp/samples/<name>/.

usage: ./run.sh generate-samples <name> [<name> ...]   (no name: all samples)

``*-bericht.md`` becomes a DOCX, ``*-praesentation.md`` a PPTX; images are taken from the
sample's ``images/`` folder as document resources.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of

REPO = Path(__file__).resolve().parents[2]
SAMPLES = REPO / "samples"
OUTPUT = REPO / ".tmp" / "samples"


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


def generate(name: str) -> None:
    folder = SAMPLES / name
    target = OUTPUT / name
    target.mkdir(parents=True, exist_ok=True)
    images = resources(folder)
    for source in sorted(folder.glob("*.md")):
        document = MarkdownDocument(source.read_text(encoding="utf-8"), images)
        if source.stem.endswith("-bericht"):
            out = target / (source.stem + ".docx")
            with out.open("wb") as stream:
                DocxGenerator().generate(document, stream)
        elif source.stem.endswith("-praesentation"):
            out = target / (source.stem + ".pptx")
            with out.open("wb") as stream:
                PptxGenerator().generate(document, stream)
        else:
            continue
        print(f"wrote {out.relative_to(REPO)}")


def main(argv: list[str]) -> int:
    names = argv or sorted(p.name for p in SAMPLES.iterdir() if p.is_dir())
    for name in names:
        generate(name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
