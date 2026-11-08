"""The tool ``make_document`` for AI hosts (E08-S04; port of ``DocumentTool.cs`` of vt-tools-libs).

``describe`` gives the model the tool — name, description, parameters as JSON Schema and the
guide; ``run`` carries out a call; ``reply`` tells the model what happened, in one JSON shape for
every host. Nothing here depends on an AI SDK: the schema is a plain ``dict`` the Anthropic API
takes as ``input_schema`` and the OpenAI API as ``parameters``.
"""

from __future__ import annotations

import json
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, BinaryIO, Final, overload

from pta_documents.design.variants import SlidesVariant, WordVariant
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.result import GenerationResult
from pta_documents.markdown.document import DocumentResource, MarkdownDocument
from pta_documents.tool import combined_guide
from pta_documents.tool.options import ToolOptions

if TYPE_CHECKING:
    from pta_documents.generation.docx.options import DocxOptions
    from pta_documents.generation.pdf.options import PdfOptions
    from pta_documents.generation.pptx.options import PptxOptions

MARKDOWN: Final = "markdown"
FORMAT: Final = "format"
TEMPLATE: Final = "vorlage"
FILE_NAME: Final = "dateiname"
PARAMETERS: Final = (MARKDOWN, FORMAT, TEMPLATE, FILE_NAME)
"""The parameters of the tool; ``vorlage`` is the front matter key it stands for."""

DEFAULT_FILE_NAME: Final = "dokument"
FILE_NAME_LENGTH: Final = 100

CONTENT_TYPES: Final[Mapping[DocumentFormat, str]] = {
    DocumentFormat.DOCX: (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ),
    DocumentFormat.PPTX: (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ),
    DocumentFormat.PDF: "application/pdf",
}

KINDS: Final[Mapping[DocumentFormat, str]] = {
    DocumentFormat.DOCX: "ein Word-Dokument (`docx`)",
    DocumentFormat.PPTX: "eine PowerPoint-Präsentation (`pptx`)",
    DocumentFormat.PDF: "ein PDF (`pdf`)",
}

_INVALID_IN_FILE_NAMES: Final = frozenset('<>:"/\\|?*')


class ToolArgumentError(ValueError):
    """The arguments of a call are not what the schema describes; the message says, in English,
    what to change — for the model, like ``DocumentConversionError.reason``."""


@dataclass(frozen=True)
class ToolDescription:
    """What the host gives the model: the tool's ``name``, its ``description`` (one paragraph),
    its ``parameters_schema`` (JSON Schema, draft 2020-12, as a ``dict``) and the ``guide``, the
    Markdown for the system prompt."""

    name: str
    description: str
    parameters_schema: dict[str, object]
    guide: str


@dataclass(frozen=True)
class ToolRun:
    """What a call made: its ``format``, the ``file_name`` with extension, the ``content_type``
    of the file and the generator's ``result`` (notes, slides, pages)."""

    format: DocumentFormat
    file_name: str
    content_type: str
    result: GenerationResult


def describe(options: ToolOptions) -> ToolDescription:
    """The tool for ``options``: only the formats offered appear in the description, the
    schema and the guide."""
    formats = options.formats
    return ToolDescription(
        name=options.name,
        description=_description(formats),
        parameters_schema=schema(options),
        guide=combined_guide.write(_guides(options), options.host_notes),
    )


def schema(options: ToolOptions) -> dict[str, object]:
    """The parameters as JSON Schema: ``markdown`` (required), ``format`` (an enum of the
    formats offered; required when there are several), ``vorlage`` (an enum of the templates of
    the formats offered) and ``dateiname``; nothing else."""
    formats = options.formats
    templates = templates_of(options)
    properties: dict[str, object] = {
        MARKDOWN: {
            "type": "string",
            "description": "Das Dokument in Markdown, geschrieben wie in der Anleitung.",
        },
        FORMAT: {
            "type": "string",
            "enum": [f.value for f in formats],
            "description": (
                f"Immer `{formats[0].value}`."
                if len(formats) == 1
                else "Was entsteht: " + _joined([KINDS[f] for f in formats], "oder") + "."
            ),
        },
        TEMPLATE: {
            "type": "string",
            "enum": list(dict.fromkeys(t for names in templates.values() for t in names)),
            "description": _template_description(templates),
        },
        FILE_NAME: {
            "type": "string",
            "description": f"Der Dateiname ohne Endung; Standard `{DEFAULT_FILE_NAME}`.",
        },
    }
    return {
        "type": "object",
        "properties": properties,
        "required": [MARKDOWN] if len(formats) == 1 else [MARKDOWN, FORMAT],
        "additionalProperties": False,
    }


def templates_of(options: ToolOptions) -> dict[DocumentFormat, tuple[str, ...]]:
    """The values of ``vorlage`` for each format offered."""
    names = {
        DocumentFormat.DOCX: tuple(v.value for v in WordVariant),
        DocumentFormat.PPTX: tuple(v.value for v in SlidesVariant),
        DocumentFormat.PDF: tuple(v.value for v in WordVariant),
    }
    return {f: names[f] for f in options.formats}


def run(
    arguments: str | Mapping[str, object],
    output: BinaryIO,
    options: ToolOptions,
    resources: Sequence[DocumentResource] = (),
) -> ToolRun:
    """Carry out a call: read ``arguments`` (the call's JSON, as text — OpenAI — or already
    parsed — Anthropic), check them against the schema, write the file to ``output``.

    ``vorlage`` works as the front matter key of the same name and loses to it: the Markdown's
    own front matter wins. The images the Markdown references come from ``resources``.

    Raises ``ToolArgumentError`` (a ``ValueError``) for arguments the schema does not allow and
    ``DocumentConversionError`` for mistakes in the Markdown; both are the model's to fix
    (``reply``). Anything else is the host's.
    """
    formats = options.formats
    values = _read(arguments)
    markdown = values.get(MARKDOWN)
    if markdown is None or not markdown.strip():
        raise ToolArgumentError(f"The parameter '{MARKDOWN}' is missing or empty.")
    format = _format(values.get(FORMAT), formats)
    template = values.get(TEMPLATE)
    if template is not None:
        expected = templates_of(options)[format]
        if template not in expected:
            raise ToolArgumentError(
                f"The parameter '{TEMPLATE}' is '{template}'; for '{format.value}' expected "
                f"{_expected(expected)}."
            )
    document = MarkdownDocument(markdown, tuple(resources))
    result = _generate(format, document, output, options, template)
    return ToolRun(
        format=format,
        file_name=f"{file_name(values.get(FILE_NAME), format)}.{format.value}",
        content_type=CONTENT_TYPES[format],
        result=result,
    )


@overload
def reply(subject: ToolRun, link: str) -> str: ...
@overload
def reply(subject: BaseException) -> str: ...
def reply(subject: ToolRun | BaseException, link: str | None = None) -> str:
    """What to tell the model, as JSON.

    After a run (``reply(run, link)``): ``{"file": link, "format": "pptx", "slides": 12,
    "pages": null, "notes": [{"code": …, "line": 12, "message": …}]}`` — every key always
    there, ``slides`` only for a deck and ``pages`` only for a PDF not null, ``line`` null for a
    note without one.

    After an error (``reply(error)``): ``{"error": "…"}`` with the reason of a
    ``DocumentConversionError`` or the message of a ``ValueError`` (``ToolArgumentError``).
    Any other exception is a fault of the host, not of the call: it is raised again.
    """
    if isinstance(subject, ToolRun):
        if link is None:
            raise TypeError("reply(run, link) needs the link to the file.")
        result = subject.result
        return _json(
            {
                "file": link,
                "format": subject.format.value,
                "slides": result.slides,
                "pages": result.pages,
                "notes": [
                    {"code": n.code, "line": n.line, "message": n.message} for n in result.notes
                ],
            }
        )
    if isinstance(subject, DocumentConversionError):
        return _json({"error": subject.reason})
    if isinstance(subject, ValueError):
        return _json({"error": str(subject)})
    raise subject


def file_name(name: str | None, format: DocumentFormat) -> str:
    """``name`` without the characters file systems reject, without leading and trailing
    spaces and dots, without the extension of ``format`` and at most ``FILE_NAME_LENGTH``
    characters; ``DEFAULT_FILE_NAME`` when nothing is left."""
    text = name or ""
    suffix = f".{format.value}"
    if text.lower().endswith(suffix):
        text = text[: -len(suffix)]
    kept = "".join(
        c
        for c in text
        if c not in _INVALID_IN_FILE_NAMES and not unicodedata.category(c).startswith("C")
    )
    clean = kept.strip().strip(".").strip()[:FILE_NAME_LENGTH].strip()
    return clean or DEFAULT_FILE_NAME


# ---------------------------------------------------------------------- details


def _description(formats: Sequence[DocumentFormat]) -> str:
    kinds = _joined([KINDS[f] for f in formats], "oder")
    return (
        f"Erzeugt {kinds} im PTA-Design aus Markdown. Vorlage, Schriften, Farben und Logo setzt "
        "das Werkzeug; zu schreiben ist nur der Inhalt, so wie es die Anleitung beschreibt. Die "
        "Antwort nennt die Datei und Hinweise, was am Markdown zu verbessern ist; ein Fehler "
        "sagt, was vor dem nächsten Aufruf zu ändern ist."
    )


def _template_description(templates: Mapping[DocumentFormat, tuple[str, ...]]) -> str:
    by_names: dict[tuple[str, ...], list[str]] = {}
    for f, names in templates.items():
        by_names.setdefault(names, []).append(combined_guide.LABELS[f])
    parts = [
        f"{_joined(labels, 'und')} {_joined([f'`{t}`' for t in names], 'oder')}"
        for names, labels in by_names.items()
    ]
    return (
        "Die PTA-Vorlage: "
        + "; ".join(parts)
        + ". Weglassen für den Standard; `vorlage:` im Front Matter tut dasselbe und gewinnt."
    )


def _guides(options: ToolOptions) -> dict[DocumentFormat, str]:
    guides: dict[DocumentFormat, str] = {}
    if options.docx is not None:
        from pta_documents.generation.docx.generator import DocxGenerator

        guides[DocumentFormat.DOCX] = DocxGenerator().authoring_guide(options.docx)
    if options.pptx is not None:
        from pta_documents.generation.pptx.generator import PptxGenerator

        guides[DocumentFormat.PPTX] = PptxGenerator().authoring_guide(options.pptx)
    if options.pdf is not None:
        from pta_documents.generation.pdf import PdfGenerator

        guides[DocumentFormat.PDF] = PdfGenerator().authoring_guide(options.pdf)
    return guides


def _generate(
    format: DocumentFormat,
    document: MarkdownDocument,
    output: BinaryIO,
    options: ToolOptions,
    template: str | None,
) -> GenerationResult:
    """The generator of ``format`` with ``template`` as the default template: the generators
    apply the front matter on top of their options, so ``vorlage:`` in the Markdown wins."""
    if format is DocumentFormat.DOCX:
        from pta_documents.generation.docx.generator import DocxGenerator

        docx: DocxOptions = _offered(options.docx)
        if template is not None:
            docx = replace(docx, variant=WordVariant(template))
        return DocxGenerator().generate(document, output, docx)
    if format is DocumentFormat.PPTX:
        from pta_documents.generation.pptx.generator import PptxGenerator

        pptx: PptxOptions = _offered(options.pptx)
        if template is not None:
            pptx = replace(pptx, variant=SlidesVariant(template))
        return PptxGenerator().generate(document, output, pptx)
    from pta_documents.generation.pdf import PdfGenerator

    pdf: PdfOptions = _offered(options.pdf)
    if template is not None:
        pdf = replace(pdf, variant=WordVariant(template))
    return PdfGenerator().generate(document, output, pdf)


def _offered[T](value: T | None) -> T:
    if value is None:  # pragma: no cover - _format only returns formats offered
        raise AssertionError("The format is not offered.")
    return value


def _read(arguments: str | Mapping[str, object]) -> dict[str, str]:
    """The arguments as strings by parameter; a ``null`` or empty optional one is left out."""
    if isinstance(arguments, str):
        try:
            parsed: object = json.loads(arguments)
        except json.JSONDecodeError as error:
            raise ToolArgumentError(f"The arguments are not valid JSON: {error}.") from error
    else:
        parsed = arguments
    if not isinstance(parsed, Mapping):
        raise ToolArgumentError("The arguments must be a JSON object.")
    values: dict[str, str] = {}
    for name, value in parsed.items():
        key = str(name)
        if key not in PARAMETERS:
            raise ToolArgumentError(
                f"Unknown parameter '{key}'; the parameters are {_joined(PARAMETERS, 'and')}."
            )
        if value is None:
            continue
        if not isinstance(value, str):
            raise ToolArgumentError(f"The parameter '{key}' must be a string.")
        if key != MARKDOWN and not value.strip():
            continue
        values[key] = value if key == MARKDOWN else value.strip()
    return values


def _format(value: str | None, formats: Sequence[DocumentFormat]) -> DocumentFormat:
    names = [f.value for f in formats]
    if value is None:
        if len(formats) == 1:
            return formats[0]
        raise ToolArgumentError(
            f"The parameter '{FORMAT}' is missing; expected {_expected(names)}."
        )
    if value not in names:
        raise ToolArgumentError(
            f"The parameter '{FORMAT}' is '{value}'; expected {_expected(names)}."
        )
    return DocumentFormat(value)


def _expected(values: Sequence[str]) -> str:
    return _joined([f"'{v}'" for v in values], "or")


def _joined(values: Sequence[str], last: str) -> str:
    if len(values) <= 1:
        return "".join(values)
    return f"{', '.join(values[:-1])} {last} {values[-1]}"


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)
