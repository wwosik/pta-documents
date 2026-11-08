"""The tool ``make_document`` (E08-S04; port of ``DocumentToolTests.cs`` of vt-tools-libs)."""

from __future__ import annotations

import io
import json
import re
from itertools import combinations
from pathlib import Path
from typing import Final

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from pta_documents.design.variants import SlidesVariant, WordVariant
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.authoring_guides import words
from pta_documents.generation.common.result import GenerationNote, GenerationResult
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.pdf import PdfGenerator, PdfOptions
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.tool import (
    ToolArgumentError,
    ToolOptions,
    ToolRun,
    combined_guide,
    describe,
    reply,
    run,
)
from pta_documents.tool.tool import file_name
from tests.conftest import REPO_ROOT

DOCX: Final = DocumentFormat.DOCX
PPTX: Final = DocumentFormat.PPTX
PDF: Final = DocumentFormat.PDF

ALL: Final = ToolOptions(docx=DocxOptions(), pptx=PptxOptions(), pdf=PdfOptions())

GUIDE_LIMIT: Final = 5000  # E08-S04 Warnung: the three guides together are ~4 600 words
"""The words of the guide for all three formats. The story aimed at 4 000; PowerPoint's guide
alone has about 3 200 and Word's 2 500, and what a report does differently from a deck does not
fit in 800 more (Warnung in the story)."""

REPORT: Final = """---
titel: Statusbericht
---
# Lage

Der Ausbau ist im Plan.
"""

DECK: Final = """# Kundenportal

## Der Pilot spart Zeit

- Anträge am selben Tag
"""


def options_for(*formats: DocumentFormat, **extra: str | None) -> ToolOptions:
    chosen = set(formats)
    return ToolOptions(
        docx=DocxOptions() if DOCX in chosen else None,
        pptx=PptxOptions() if PPTX in chosen else None,
        pdf=PdfOptions() if PDF in chosen else None,
        **extra,  # pyright: ignore[reportArgumentType]
    )


SELECTIONS: Final = [c for n in (1, 2, 3) for c in combinations((DOCX, PPTX, PDF), n)]


def headings(guide: str) -> list[str]:
    """The ``##`` headings of ``guide`` outside code blocks."""
    found: list[str] = []
    fence: str | None = None
    for line in guide.split("\n"):
        if fence is None and line.startswith("```"):
            fence = line[: len(line) - len(line.lstrip("`"))]
        elif fence is not None and line.strip() == fence:
            fence = None
        elif fence is None and line.startswith("## "):
            found.append(line[3:])
    return found


def generate(arguments: dict[str, object], options: ToolOptions = ALL) -> tuple[ToolRun, bytes]:
    output = io.BytesIO()
    made = run(json.dumps(arguments), output, options)
    return made, output.getvalue()


# ---------------------------------------------------------------------- options


def test_the_tool_needs_a_format() -> None:
    with pytest.raises(ValueError, match="at least one format"):
        ToolOptions()


@pytest.mark.parametrize("name", ["", "make document", "x" * 65, "dokument.erzeugen"])
def test_the_name_must_be_one_the_apis_take(name: str) -> None:
    with pytest.raises(ValueError, match="not valid"):
        ToolOptions(docx=DocxOptions(), name=name)


# ---------------------------------------------------------------------- describe


@pytest.mark.parametrize("formats", SELECTIONS, ids=lambda fs: "+".join(f.value for f in fs))
def test_the_schema_is_valid_and_names_only_the_formats_offered(
    formats: tuple[DocumentFormat, ...],
) -> None:
    description = describe(options_for(*formats))
    schema = description.parameters_schema
    Draft202012Validator.check_schema(schema)
    properties = schema["properties"]
    assert isinstance(properties, dict)
    assert list(properties) == ["markdown", "format", "vorlage", "dateiname"]  # pyright: ignore[reportUnknownArgumentType]
    assert properties["format"]["enum"] == [f.value for f in formats]
    templates = {
        DOCX: [v.value for v in WordVariant],
        PPTX: [v.value for v in SlidesVariant],
        PDF: [v.value for v in WordVariant],
    }
    expected = list(dict.fromkeys(t for f in formats for t in templates[f]))
    assert properties["vorlage"]["enum"] == expected
    assert schema["required"] == (["markdown"] if len(formats) == 1 else ["markdown", "format"])
    assert schema["additionalProperties"] is False
    assert len(description.description) < 1000
    for kind, format in (("Word", DOCX), ("PowerPoint", PPTX), ("PDF", PDF)):
        assert (kind in description.description) == (format in formats)


def test_the_schema_takes_a_call_and_rejects_others() -> None:
    validator = Draft202012Validator(describe(ALL).parameters_schema)
    validator.validate({"markdown": DECK, "format": "pptx", "vorlage": "schulung"})
    validator.validate({"markdown": REPORT, "format": "pdf", "dateiname": "bericht"})
    for wrong in (
        {"markdown": DECK},
        {"markdown": DECK, "format": "html"},
        {"markdown": DECK, "format": "pptx", "farbe": "rot"},
        {"markdown": DECK, "format": "pptx", "vorlage": "neutral"},
    ):
        with pytest.raises(ValidationError):
            validator.validate(wrong)


def test_the_name_is_the_options() -> None:
    assert describe(ALL).name == "make_document"
    assert describe(options_for(PPTX, name="folien")).name == "folien"


@pytest.mark.parametrize("format", [DOCX, PPTX, PDF])
def test_one_format_gets_its_generators_guide(format: DocumentFormat) -> None:
    options = options_for(format)
    own = {
        DOCX: lambda: DocxGenerator().authoring_guide(options.docx),
        PPTX: lambda: PptxGenerator().authoring_guide(options.pptx),
        PDF: lambda: PdfGenerator().authoring_guide(options.pdf),
    }[format]()
    assert describe(options).guide == own


@pytest.mark.parametrize("formats", SELECTIONS, ids=lambda fs: "+".join(f.value for f in fs))
def test_the_guide_says_every_section_once(formats: tuple[DocumentFormat, ...]) -> None:
    guide = describe(options_for(*formats)).guide
    found = headings(guide)
    assert len(found) == len(set(found)), found
    assert words(guide) < GUIDE_LIMIT
    own = {
        DOCX: DocxGenerator().authoring_guide(),
        PPTX: PptxGenerator().authoring_guide(),
        PDF: PdfGenerator().authoring_guide(),
    }
    named = {re.sub(r" \(nur [^)]*\)$", "", h) for h in found}
    for format in formats:
        if len(formats) > 1:
            assert set(headings(own[format])[1:]) <= named, format


def test_the_combined_guide_marks_what_only_some_formats_have() -> None:
    guide = describe(ALL).guide
    assert headings(guide)[0] == "Formate"
    assert "## Vorlagenlayouts (nur PowerPoint)" in guide
    assert "## Zeichen (nur PDF)" in guide
    assert "*Nur Word und PDF:*" in guide
    assert "| Markdown | In Word / Im PDF |" in guide
    # A front matter key that means different things says so in its row.
    row = next(line for line in guide.splitlines() if line.startswith("| `vorlage` |"))
    assert "*Word und PDF:* `hoch` (Standard)" in row
    assert "*PowerPoint:* `basis` (Standard)" in row


def test_formats_not_offered_are_missing_from_the_guide() -> None:
    documents = describe(options_for(DOCX, PDF)).guide
    assert "PowerPoint" not in "\n".join(headings(documents))
    assert "Nur PowerPoint" not in documents
    assert "`pptx`" not in documents
    assert "Vorlagenlayouts" not in documents
    no_pdf = describe(options_for(DOCX, PPTX)).guide
    assert "Nur PDF" not in no_pdf
    assert "nur PDF" not in no_pdf
    assert "`pdf`" not in no_pdf
    assert "## Zeichen" not in no_pdf


def test_the_host_notes_come_last() -> None:
    guide = describe(options_for(PPTX, host_notes="Links öffnen die Datei.")).guide
    assert guide.endswith("## In dieser Anwendung\n\nLinks öffnen die Datei.\n")
    own = describe(options_for(DOCX, PDF, host_notes="## Ablage\n\nIm Teams-Kanal.\n")).guide
    assert own.endswith("\n\n## Ablage\n\nIm Teams-Kanal.\n")
    assert combined_guide.HOST_HEADING not in own


def test_sections_ignore_headings_in_code_blocks() -> None:
    guide = "## Eins\n\nText\n\n````markdown\n## Folie\n````\n\n## Zwei\n\nMehr\n"
    found = combined_guide.sections(guide)
    assert list(found) == ["\0intro", "Zwei"]
    assert "## Folie" in found["\0intro"]


# ---------------------------------------------------------------------- run


@pytest.mark.parametrize(
    ("format", "markdown", "magic"),
    [(DOCX, REPORT, b"PK"), (PPTX, DECK, b"PK"), (PDF, REPORT, b"%PDF")],
)
def test_run_makes_each_format(format: DocumentFormat, markdown: str, magic: bytes) -> None:
    made, content = generate({"markdown": markdown, "format": format.value, "dateiname": "x"})
    assert content.startswith(magic)
    assert made.format is format
    assert made.file_name == f"x.{format.value}"
    assert (
        made.content_type
        == {
            DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            PPTX: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            PDF: "application/pdf",
        }[format]
    )
    assert made.result.notes == ()
    assert (made.result.slides is not None) == (format is PPTX)
    assert (made.result.pages is not None) == (format is PDF)


def test_one_format_needs_no_format_and_takes_parsed_arguments() -> None:
    output = io.BytesIO()
    made = run({"markdown": DECK, "vorlage": None, "dateiname": ""}, output, options_for(PPTX))
    assert made.format is PPTX
    assert made.file_name == "dokument.pptx"
    assert made.result.slides == 2


def test_the_template_is_a_default_the_front_matter_overrides() -> None:
    no_title = "# Lage\n\nText.\n"
    with pytest.raises(DocumentConversionError, match="needs a title"):
        generate({"markdown": no_title, "format": "docx"})
    made, _ = generate({"markdown": no_title, "format": "docx", "vorlage": "hoch-ohne-deckblatt"})
    assert made.result.notes == ()
    front = "---\nvorlage: hoch\n---\n" + no_title
    with pytest.raises(DocumentConversionError, match="needs a title"):
        generate({"markdown": front, "format": "pdf", "vorlage": "quer-ohne-deckblatt"})


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ("{markdown", "The arguments are not valid JSON: "),
        ("[1, 2]", "The arguments must be a JSON object."),
        ('{"markdown": "# A", "format": "pptx", "farbe": "rot"}', "Unknown parameter 'farbe'; "),
        ('{"markdown": 3, "format": "pptx"}', "The parameter 'markdown' must be a string."),
        ('{"markdown": "  ", "format": "pptx"}', "The parameter 'markdown' is missing or empty."),
        ('{"format": "pptx"}', "The parameter 'markdown' is missing or empty."),
        (
            '{"markdown": "# A"}',
            "The parameter 'format' is missing; expected 'docx', 'pptx' or 'pdf'.",
        ),
        (
            '{"markdown": "# A", "format": "html"}',
            "The parameter 'format' is 'html'; expected 'docx', 'pptx' or 'pdf'.",
        ),
        (
            '{"markdown": "# A", "format": "pptx", "vorlage": "hoch"}',
            "The parameter 'vorlage' is 'hoch'; for 'pptx' expected 'basis' or 'schulung'.",
        ),
    ],
)
def test_wrong_arguments_say_what_to_change(arguments: str, message: str) -> None:
    with pytest.raises(ToolArgumentError) as error:
        run(arguments, io.BytesIO(), ALL)
    assert str(error.value).startswith(message)
    assert reply(error.value) == json.dumps({"error": str(error.value)}, ensure_ascii=False)


def test_a_format_not_offered_is_a_wrong_argument() -> None:
    with pytest.raises(ToolArgumentError, match=r"is 'pdf'; expected 'docx' or 'pptx'\."):
        run('{"markdown": "# A", "format": "pdf"}', io.BytesIO(), options_for(DOCX, PPTX))


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        (None, "dokument"),
        ("", "dokument"),
        ("Statusbericht Mai", "Statusbericht Mai"),
        ("bericht.docx", "bericht"),
        ("../../etc/passwd", "etcpasswd"),
        ('a<b>c:d"e/f\\g|h?i*j', "abcdefghij"),
        (" ..versteckt. ", "versteckt"),
        ("zeile\nzwei\t", "zeilezwei"),
        ("???", "dokument"),
        ("ä" * 120, "ä" * 100),
    ],
)
def test_file_names_lose_what_file_systems_reject(name: str | None, expected: str) -> None:
    assert file_name(name, DOCX) == expected


# ---------------------------------------------------------------------- reply


def test_the_reply_after_a_run_has_one_shape() -> None:
    made = ToolRun(
        format=PPTX,
        file_name="folien.pptx",
        content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        result=GenerationResult(
            (
                GenerationNote("raw-html", None, "Raw HTML is left out."),
                GenerationNote("slide-split", 12, "The slide „Lage“ goes on."),
            ),
            slides=7,
        ),
    )
    assert reply(made, "https://host/folien.pptx") == (
        '{"file": "https://host/folien.pptx", "format": "pptx", "slides": 7, "pages": null, '
        '"notes": [{"code": "raw-html", "line": null, "message": "Raw HTML is left out."}, '
        '{"code": "slide-split", "line": 12, "message": "The slide „Lage“ goes on."}]}'
    )


def test_the_reply_after_a_real_run_names_pages() -> None:
    made, _ = generate({"markdown": REPORT, "format": "pdf"})
    answer = json.loads(reply(made, "bericht.pdf"))
    assert list(answer) == ["file", "format", "slides", "pages", "notes"]
    assert answer["format"] == "pdf"
    assert answer["slides"] is None
    assert answer["pages"] >= 1
    assert answer["notes"] == []


def test_the_reply_after_an_error_has_one_shape() -> None:
    error = DocumentConversionError(DOCX, "Line 3: Unknown container '::: karte'.")
    assert reply(error) == '{"error": "Line 3: Unknown container \'::: karte\'."}'
    assert reply(ValueError("Falsch")) == '{"error": "Falsch"}'


def test_a_mistake_in_the_markdown_is_the_models() -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate({"markdown": "# A\n\n::: karte\nText\n:::\n", "format": "pptx"})
    assert json.loads(reply(error.value)) == {"error": error.value.reason}


def test_other_errors_are_the_hosts() -> None:
    with pytest.raises(OSError, match="disk full"):
        reply(OSError("disk full"))


# ---------------------------------------------------------------------- package


def test_the_library_imports_no_ai_sdk() -> None:
    sdk = re.compile(
        r"^\s*(?:import|from)\s+(anthropic|openai|langchain\w*|google\.generativeai|"
        r"mistralai|cohere|ollama)\b",
        re.MULTILINE,
    )
    sources = (REPO_ROOT / "src" / "pta_documents").rglob("*.py")
    users = [p for p in sources if sdk.search(p.read_text(encoding="utf-8"))]
    assert users == []


def test_review_file(review_dir: Path) -> None:
    description = describe(ALL)
    text = (
        f"# Werkzeug `{description.name}`\n\n"
        f"## Beschreibung\n\n{description.description}\n\n"
        "## Parameter (JSON Schema)\n\n```json\n"
        + json.dumps(description.parameters_schema, ensure_ascii=False, indent=2)
        + f"\n```\n\n# Anleitung ({words(description.guide)} Wörter)\n\n"
        + description.guide
    )
    (review_dir / "make_document.md").write_text(text, encoding="utf-8")
