"""Generate PTA documents from Markdown files.

usage: ./run.sh generate <file-or-folder> [...] [--docx | --pptx] [--out <folder>]

A folder means every ``*.md`` in it. The target format comes from the file name —
``…-bericht.md`` / ``…-dokument.md`` → DOCX, ``…-praesentation.md`` / ``…-folien.md`` → PPTX —
or from ``--docx`` / ``--pptx``. Images are the image files below the Markdown file's folder,
referenced relative to it (``images/foto.jpg``). The result is written next to the Markdown
file unless ``--out`` names another folder. Mistakes in a document are reported with what to
change; the other files are still generated.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pta_documents.errors import DocumentConversionError
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".svg"}
DOCX_SUFFIXES = ("-bericht", "-dokument")
PPTX_SUFFIXES = ("-praesentation", "-folien")


def resources(folder: Path) -> list[DocumentResource]:
    return [
        DocumentResource(
            path.relative_to(folder).as_posix(), content_type_of(path.name), path.read_bytes()
        )
        for path in sorted(folder.rglob("*"))
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ]


def target_format(source: Path, forced: str | None) -> str | None:
    if forced:
        return forced
    if source.stem.endswith(DOCX_SUFFIXES):
        return "docx"
    if source.stem.endswith(PPTX_SUFFIXES):
        return "pptx"
    return None


def generate(source: Path, forced: str | None, out: Path | None) -> bool:
    format = target_format(source, forced)
    if format is None:
        print(
            f"skipped {source}: name it …-bericht.md or …-praesentation.md, or pass --docx / --pptx"
        )
        return True
    document = MarkdownDocument(source.read_text(encoding="utf-8"), resources(source.parent))
    folder = out or source.parent
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{source.stem}.{format}"
    generator = DocxGenerator() if format == "docx" else PptxGenerator()
    try:
        with target.open("wb") as stream:
            generator.generate(document, stream)
    except DocumentConversionError as error:
        target.unlink(missing_ok=True)
        print(f"ERROR {source}: {error.reason}", file=sys.stderr)
        return False
    print(f"wrote {target}")
    return True


def main(argv: list[str]) -> int:
    forced: str | None = None
    out: Path | None = None
    paths: list[Path] = []
    args = iter(argv)
    for arg in args:
        if arg in ("--docx", "--pptx"):
            forced = arg[2:]
        elif arg == "--out":
            out = Path(next(args))
        else:
            paths.append(Path(arg))
    if not paths:
        print(__doc__)
        return 1
    ok = True
    for path in paths:
        files = sorted(path.glob("*.md")) if path.is_dir() else [path]
        for source in files:
            if source.name.lower() in ("readme.md", "quellen.md"):
                continue
            ok &= generate(source, forced, out)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
