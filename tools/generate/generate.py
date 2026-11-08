"""Generate PTA documents from Markdown files.

usage: ./run.sh generate <file-or-folder> [...] [--docx | --pptx | --pdf | --html]
                         [--out <folder>] [--strict] [--audience kunde|intern|trainer|alle]

A folder means every ``*.md`` in it. The target format comes from the file name —
``…-bericht.md`` / ``…-dokument.md`` → DOCX, ``…-praesentation.md`` / ``…-folien.md`` → PPTX —
or from ``--docx`` / ``--pptx``; a PDF only with ``--pdf`` (extra ``pdf``; the PDF follows
the Word templates, ``vorlage:`` as in Word); an HTML deck only with ``--html`` (the slides of
the PPTX in one HTML file for the browser, E10-S01). Images are the image files below the Markdown
file's folder, referenced relative to it (``images/foto.jpg``). The result is written next to
the Markdown file unless ``--out`` names another folder. Mistakes in a document are reported
with what to change; the other files are still generated.

``--audience`` chooses the version (E16-S01) and wins over ``fassung:`` in the front matter;
without either it is ``kunde``. The customer's version is ``<name>.<format>``, the others
``<name>-intern.<format>`` and ``<name>-trainer.<format>``; ``alle`` writes every version that
differs from the ones before it (``kunde``, then ``intern``, then ``trainer``).

After each file come the notes on what the generator had to work around (``  - line 12: …``).
Notes are not errors: the exit code is 1 only for errors, or with ``--strict`` also for notes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import audience as audiences
from pta_documents.generation.common.audience import Audience
from pta_documents.generation.common.result import GenerationResult
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.html.generator import HtmlDeckGenerator
from pta_documents.generation.html.options import HtmlDeckOptions
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of

if TYPE_CHECKING:
    from pta_documents.generation.pdf import PdfGenerator

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".svg"}
DOCX_SUFFIXES = ("-bericht", "-dokument")
PPTX_SUFFIXES = ("-praesentation", "-folien")
FORMAT_SWITCHES = ("--docx", "--pptx", "--pdf", "--html")
ALL_AUDIENCES = "alle"
AUDIENCE_VALUES = (*(a.value for a in Audience), ALL_AUDIENCES)


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


def generator_for(
    format: str,
) -> DocxGenerator | PptxGenerator | HtmlDeckGenerator | PdfGenerator:
    """The generator of ``format``; the PDF one is imported only now (extra ``pdf``)."""
    if format == "docx":
        return DocxGenerator()
    if format == "pptx":
        return PptxGenerator()
    if format == "html":
        return HtmlDeckGenerator()
    from pta_documents.generation.pdf import PdfGenerator

    return PdfGenerator()


def write(
    generator: DocxGenerator | PptxGenerator | HtmlDeckGenerator | PdfGenerator,
    document: MarkdownDocument,
    stream: BinaryIO,
    audience: Audience | None,
) -> GenerationResult:
    """``generator`` with its options for the version ``audience`` (None: ``fassung:``)."""
    if isinstance(generator, DocxGenerator):
        return generator.generate(document, stream, DocxOptions(audience=audience))
    if isinstance(generator, PptxGenerator):
        return generator.generate(document, stream, PptxOptions(audience=audience))
    if isinstance(generator, HtmlDeckGenerator):
        return generator.generate(document, stream, HtmlDeckOptions(audience=audience))
    from pta_documents.generation.pdf import PdfOptions

    return generator.generate(document, stream, PdfOptions(audience=audience))


def audiences_of(text: str, format: str, requested: str | None) -> list[Audience | None]:
    """The versions to write: the requested one, every differing one for ``alle``, else the
    one of the front matter (None: the generator reads ``fassung:`` itself)."""
    if requested is None:
        return [None]
    if requested != ALL_AUDIENCES:
        return [Audience(requested)]
    try:
        return list(audiences.versions(text, DocumentFormat(format)))
    except DocumentConversionError:
        return [None]  # the generator reports the mistake


def file_suffix(text: str, format: str, audience: Audience | None) -> str:
    """``-intern``/``-trainer`` for those versions, nothing for the customer's."""
    try:
        return audiences.of(text, DocumentFormat(format), audience).suffix
    except DocumentConversionError:
        return ""  # the generator reports the mistake


def print_notes(result: GenerationResult) -> None:
    for note in result.notes:
        print(f"  - {note}")


def generate(
    source: Path,
    forced: str | None,
    out: Path | None,
    strict: bool = False,
    audience: str | None = None,
) -> bool:
    """Generate one file in the versions ``audience`` asks for (``kunde``, ``intern``,
    ``trainer``, ``alle``; None: ``fassung:``); False on an error (or, with ``strict``, on
    notes)."""
    format = target_format(source, forced)
    if format is None:
        print(
            f"skipped {source}: name it …-bericht.md or …-praesentation.md, "
            "or pass --docx / --pptx / --pdf / --html"
        )
        return True
    document = MarkdownDocument(source.read_text(encoding="utf-8"), resources(source.parent))
    folder = out or source.parent
    folder.mkdir(parents=True, exist_ok=True)
    try:
        generator = generator_for(format)
    except ImportError as error:  # --pdf without the extra 'pdf'
        print(f"ERROR {source}: {error}", file=sys.stderr)
        return False
    ok = True
    for version in audiences_of(document.text, format, audience):
        suffix = file_suffix(document.text, format, version)
        target = folder / f"{source.stem}{suffix}.{format}"
        try:
            with target.open("wb") as stream:
                result = write(generator, document, stream, version)
        except DocumentConversionError as error:
            target.unlink(missing_ok=True)
            print(f"ERROR {source}: {error.reason}", file=sys.stderr)
            return False
        print(f"wrote {target}")
        print_notes(result)
        ok &= not (strict and result.notes)
    return ok


def main(argv: list[str]) -> int:
    forced: str | None = None
    out: Path | None = None
    strict = False
    audience: str | None = None
    paths: list[Path] = []
    args = iter(argv)
    for arg in args:
        if arg in FORMAT_SWITCHES:
            forced = arg[2:]
        elif arg == "--strict":
            strict = True
        elif arg == "--out":
            out = Path(next(args))
        elif arg == "--audience":
            audience = next(args, "").strip().lower()
            if audience not in AUDIENCE_VALUES:
                print(
                    f"--audience takes {', '.join(AUDIENCE_VALUES)}, not '{audience}'",
                    file=sys.stderr,
                )
                return 1
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
            ok &= generate(source, forced, out, strict, audience)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
