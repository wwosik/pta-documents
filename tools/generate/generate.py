"""Generate PTA documents from Markdown files.

usage: ./run.sh generate <file-or-folder> [...] [--docx | --pptx | --pdf] [--out <folder>]
                         [--strict]

A folder means every ``*.md`` in it. The target format comes from the file name —
``…-bericht.md`` / ``…-dokument.md`` → DOCX, ``…-praesentation.md`` / ``…-folien.md`` → PPTX —
or from ``--docx`` / ``--pptx``; a PDF only with ``--pdf`` (extra ``pdf``; the PDF follows
the Word templates, ``vorlage:`` as in Word). Images are the image files below the Markdown
file's folder, referenced relative to it (``images/foto.jpg``). The result is written next to
the Markdown file unless ``--out`` names another folder. Mistakes in a document are reported
with what to change; the other files are still generated.

After each file come the notes on what the generator had to work around (``  - line 12: …``).
Notes are not errors: the exit code is 1 only for errors, or with ``--strict`` also for notes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from pta_documents.errors import DocumentConversionError
from pta_documents.generation.common.result import GenerationResult
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of

if TYPE_CHECKING:
    from pta_documents.generation.pdf import PdfGenerator

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".svg"}
DOCX_SUFFIXES = ("-bericht", "-dokument")
PPTX_SUFFIXES = ("-praesentation", "-folien")
FORMAT_SWITCHES = ("--docx", "--pptx", "--pdf")


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


def generator_for(format: str) -> DocxGenerator | PptxGenerator | PdfGenerator:
    """The generator of ``format``; the PDF one is imported only now (extra ``pdf``)."""
    if format == "docx":
        return DocxGenerator()
    if format == "pptx":
        return PptxGenerator()
    from pta_documents.generation.pdf import PdfGenerator

    return PdfGenerator()


def print_notes(result: GenerationResult) -> None:
    for note in result.notes:
        print(f"  - {note}")


def generate(source: Path, forced: str | None, out: Path | None, strict: bool = False) -> bool:
    """Generate one file; False on an error (or, with ``strict``, on notes)."""
    format = target_format(source, forced)
    if format is None:
        print(
            f"skipped {source}: name it …-bericht.md or …-praesentation.md, "
            "or pass --docx / --pptx / --pdf"
        )
        return True
    document = MarkdownDocument(source.read_text(encoding="utf-8"), resources(source.parent))
    folder = out or source.parent
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{source.stem}.{format}"
    try:
        generator = generator_for(format)
    except ImportError as error:  # --pdf without the extra 'pdf'
        print(f"ERROR {source}: {error}", file=sys.stderr)
        return False
    try:
        with target.open("wb") as stream:
            result = generator.generate(document, stream)
    except DocumentConversionError as error:
        target.unlink(missing_ok=True)
        print(f"ERROR {source}: {error.reason}", file=sys.stderr)
        return False
    print(f"wrote {target}")
    print_notes(result)
    return not (strict and result.notes)


def main(argv: list[str]) -> int:
    forced: str | None = None
    out: Path | None = None
    strict = False
    paths: list[Path] = []
    args = iter(argv)
    for arg in args:
        if arg in FORMAT_SWITCHES:
            forced = arg[2:]
        elif arg == "--strict":
            strict = True
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
            ok &= generate(source, forced, out, strict)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
