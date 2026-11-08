"""E16-S01: versions of one document for the customer, PTA and the trainer, in every format."""

from __future__ import annotations

import datetime as dt
import importlib.util
import io
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

from pta_documents.conversions.docx import DocxConverter
from pta_documents.conversions.pptx import PptxConverter
from pta_documents.design.variants import TEXTS, Language, Marking, WordVariant
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import audience
from pta_documents.generation.common.audience import Audience
from pta_documents.generation.common.check import CheckOptions, DeckStats, ReportStats, check
from pta_documents.generation.common.result import GenerationResult, NoteCodes
from pta_documents.generation.docx.generator import DocxGenerator, apply_front_matter
from pta_documents.generation.docx.generator import apply_audience as docx_audience
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.html.generator import HtmlDeckGenerator
from pta_documents.generation.html.options import HtmlDeckOptions
from pta_documents.generation.pdf import PdfGenerator, PdfOptions
from pta_documents.generation.pptx import sticker
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.generation.pptx.generator import apply_audience as pptx_audience
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import MarkdownDocument
from pta_documents.markdown.front_matter import FrontMatter
from pta_documents.markdown.parser import parse
from tests.expected import assert_matches_expected
from tests.generation.docx.conftest import all_text, open_docx
from tests.generation.pdf.support import body_texts
from tests.generation.pptx.conftest import open_pptx

REPO: Final = Path(__file__).resolve().parents[3]
SAMPLES: Final = Path(__file__).parent / "samples"
DECK: Final = (SAMPLES / "fassungen.md").read_text(encoding="utf-8")
A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
CREATED: Final = dt.datetime(2026, 11, 8, 12, 0, tzinfo=dt.UTC)

PUBLIC: Final = "Öffentlicher Text"
MARKED: Final = "Interner Hinweis zum Preis"
CONTAINED: Final = "Interne Liste"
EXERCISE: Final = "Rechne zwei plus zwei"
SOLUTION: Final = "Die Lösung ist vier"
SLIDE: Final = "Geheime Folie"
SLIDE_NOTES: Final = "Notiz der geheimen Folie"
CHAPTER: Final = "Internes Kapitel"
IN_CHAPTER: Final = "Text im internen Kapitel"
INTERNAL_TEXTS: Final = (MARKED, CONTAINED, SLIDE, SLIDE_NOTES, CHAPTER, IN_CHAPTER)

Generate = Callable[[str, Audience | None], tuple[GenerationResult, str]]


def docx_text(markdown: str, chosen: Audience | None) -> tuple[GenerationResult, str]:
    output = io.BytesIO()
    options = DocxOptions(variant=WordVariant.PORTRAIT_NO_COVER, audience=chosen)
    result = DocxGenerator().generate(MarkdownDocument(markdown), output, options)
    return result, "\n".join(p.text for p in open_docx(output.getvalue()).paragraphs)


def pptx_text(markdown: str, chosen: Audience | None) -> tuple[GenerationResult, str]:
    output = io.BytesIO()
    options = PptxOptions(audience=chosen, code_block_renderers=())
    result = PptxGenerator().generate(MarkdownDocument(markdown), output, options)
    return result, PptxConverter().convert(output.getvalue()).text


def pdf_text(markdown: str, chosen: Audience | None) -> tuple[GenerationResult, str]:
    output = io.BytesIO()
    options = PdfOptions(
        variant=WordVariant.PORTRAIT_NO_COVER, system_fonts=False, created=CREATED, audience=chosen
    )
    result = PdfGenerator().generate(MarkdownDocument(markdown), output, options)
    return result, "\n".join(body_texts(output.getvalue())).replace("\n", " ")


def html_text(markdown: str, chosen: Audience | None) -> tuple[GenerationResult, str]:
    output = io.BytesIO()
    options = HtmlDeckOptions(audience=chosen, code_block_renderers=())
    result = HtmlDeckGenerator().generate(MarkdownDocument(markdown), output, options)
    return result, output.getvalue().decode("utf-8")


FORMATS = pytest.mark.parametrize(
    "generate",
    [docx_text, pptx_text, pdf_text, html_text],
    ids=["docx", "pptx", "pdf", "html"],
)


# ---------------------------------------------------------------------- what each version shows


@FORMATS
@pytest.mark.parametrize("chosen", list(Audience), ids=lambda a: a.value)
def test_every_syntax_in_every_version(generate: Generate, chosen: Audience) -> None:
    _, text = generate(DECK, chosen)
    assert PUBLIC in text and EXERCISE in text
    for internal in (MARKED, CONTAINED, SLIDE, CHAPTER, IN_CHAPTER):
        assert (internal in text) is chosen.shows_internal, internal
    assert (SOLUTION in text) is chosen.shows_solutions


@FORMATS
def test_the_customer_version_is_the_default(generate: Generate) -> None:
    assert generate(DECK, None) == generate(DECK, Audience.KUNDE)


def test_the_customer_pdf_is_byte_for_byte_the_default() -> None:
    def pdf(options: PdfOptions) -> bytes:
        output = io.BytesIO()
        PdfGenerator().generate(MarkdownDocument(DECK), output, options)
        return output.getvalue()

    base = PdfOptions(variant=WordVariant.PORTRAIT_NO_COVER, system_fonts=False, created=CREATED)
    assert pdf(base) == pdf(replace(base, audience=Audience.KUNDE))


def test_an_internal_slide_goes_with_its_notes() -> None:
    output = io.BytesIO()
    options = PptxOptions(audience=Audience.KUNDE, code_block_renderers=())
    PptxGenerator().generate(MarkdownDocument(DECK), output, options)
    notes = [
        slide.notes_slide.notes_text_frame.text
        for slide in open_pptx(output.getvalue()).slides
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None
    ]
    assert not any(SLIDE_NOTES in n for n in notes)
    _, trainer = pptx_text(DECK, Audience.TRAINER)
    assert SLIDE_NOTES in trainer


def test_chapter_numbers_count_without_the_internal_chapters() -> None:
    def numbers(chosen: Audience) -> list[str]:
        _, text = pptx_text(DECK, chosen)
        return [line for line in text.split("\n") if line in ("01", "02", "03")]

    assert numbers(Audience.KUNDE) == ["01", "02"]
    assert numbers(Audience.INTERN) == ["01", "02", "03"]


def test_slides_are_left_out_not_emptied() -> None:
    kunde, _ = pptx_text(DECK, Audience.KUNDE)
    trainer, _ = pptx_text(DECK, Audience.TRAINER)
    assert kunde.slides is not None and trainer.slides is not None
    # The internal slide, the internal chapter's slide and its content slide.
    assert trainer.slides - kunde.slides == 3


# ---------------------------------------------------------------------- the note


@FORMATS
def test_one_note_with_the_numbers(generate: Generate) -> None:
    kunde, _ = generate(DECK, Audience.KUNDE)
    intern, _ = generate(DECK, Audience.INTERN)
    trainer, _ = generate(DECK, Audience.TRAINER)
    assert kunde.codes().count(NoteCodes.AUDIENCE_OMITTED) == 1
    omitted = next(n for n in kunde.notes if n.code == NoteCodes.AUDIENCE_OMITTED)
    assert omitted.message.startswith(
        "4 internal blocks and 1 solution were left out for the audience 'kunde'"
    )
    assert omitted.line is None
    message = next(n.message for n in intern.notes if n.code == NoteCodes.AUDIENCE_OMITTED)
    assert message.startswith("1 solution was left out for the audience 'intern'")
    assert NoteCodes.AUDIENCE_OMITTED not in trainer.codes()


def test_no_note_without_anything_to_leave_out() -> None:
    result, _ = pptx_text("# Deck\n\n## Folie\n\nText\n", Audience.KUNDE)
    assert result.notes == ()


def test_the_message_names_what_shows_the_blocks() -> None:
    assert audience.omitted_message(1, 0, Audience.KUNDE) == (
        "1 internal block was left out for the audience 'kunde'; '--audience intern' (or "
        "'fassung: intern') shows them."
    )
    assert audience.omitted_message(12, 3, Audience.KUNDE).startswith(
        "12 internal blocks and 3 solutions were left out for the audience 'kunde'; "
        "'--audience trainer'"
    )


# ---------------------------------------------------------------------- front matter, marking


def test_the_front_matter_chooses_and_the_option_wins() -> None:
    markdown = "---\nfassung: trainer\n---\n" + DECK
    _, text = docx_text(markdown, None)
    assert SOLUTION in text
    _, text = docx_text(markdown, Audience.KUNDE)
    assert SOLUTION not in text and MARKED not in text


@pytest.mark.parametrize("generate", [docx_text, pptx_text, pdf_text, html_text])
def test_an_unknown_version_names_the_valid_ones(generate: Generate) -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate("---\nfassung: alle\n---\n# T\n", None)
    assert "The front matter key 'fassung' has the value 'alle'" in error.value.reason
    assert "'kunde' or 'intern' or 'trainer'" in error.value.reason


@pytest.mark.parametrize(
    ("front", "chosen", "expected"),
    [
        ("", None, Marking.NONE),
        ("", Audience.INTERN, Marking.INTERNAL),
        ("fassung: trainer", None, Marking.INTERNAL),
        ("fassung: trainer\nkennzeichnung: vertraulich", None, Marking.CONFIDENTIAL),
        ("fassung: trainer\nkennzeichnung: kein", None, Marking.NONE),
    ],
)
def test_internal_versions_are_marked_internal(
    front: str, chosen: Audience | None, expected: Marking
) -> None:
    markdown = f"---\n{front}\n---\n# T\n" if front else "# T\n"
    matter = FrontMatter.read(markdown, DocumentFormat.DOCX)
    options = docx_audience(matter, apply_front_matter(matter, DocxOptions(audience=chosen)))
    assert options.marking is expected
    slides = pptx_audience(matter, PptxOptions(audience=chosen, marking=_pptx_marking(front)))
    assert sticker.resolve(slides.variant, slides.marking) is expected


def _pptx_marking(front: str) -> Marking | None:
    for line in front.split("\n"):
        if line.startswith("kennzeichnung:"):
            return Marking(line.partition(":")[2].strip())
    return None


def test_the_marking_lands_in_word_and_on_the_master() -> None:
    texts = TEXTS[Language.DE]
    output = io.BytesIO()
    options = DocxOptions(variant=WordVariant.PORTRAIT_NO_COVER, audience=Audience.TRAINER)
    DocxGenerator().generate(MarkdownDocument(DECK), output, options)
    assert texts.marking(Marking.INTERNAL) in all_text(output.getvalue())
    output = io.BytesIO()
    options = DocxOptions(variant=WordVariant.PORTRAIT_NO_COVER)
    DocxGenerator().generate(MarkdownDocument(DECK), output, options)
    assert texts.marking(Marking.INTERNAL) not in all_text(output.getvalue())
    output = io.BytesIO()
    PptxGenerator().generate(MarkdownDocument(DECK), output, PptxOptions(audience=Audience.INTERN))
    master = open_pptx(output.getvalue()).slide_masters[0].shapes._spTree
    found = sticker.find(master)
    assert found is not None
    shown = "".join(t.text or "" for t in found.iter(f"{{{A}}}t"))
    assert texts.marking(Marking.INTERNAL) in shown


# ---------------------------------------------------------------------- mistakes


MISTAKES: Final = [
    (
        "# T\n\nText\n\n::: solution\nVier\n:::\n",
        "Line 5: A '::: solution' needs a '::: exercise' right before it (or around it).",
    ),
    (
        "# T\n\n::: exercise\nA\n:::\n\nText\n\n::: solution\nB\n:::\n",
        "Line 9: A '::: solution' needs a '::: exercise'",
    ),
    (
        "# T\n\n::: internal\n## Folie\n:::\n",
        "Line 4: A '##' heading cannot stand in a '::: internal'",
    ),
    (
        "# T\n\n## Folie\n\n{.build}\n::: internal\n- a\n:::\n",
        "Line 5: The block marker '{.build}' cannot mark a '::: internal'",
    ),
    (
        "# T\n\n{.internal}\n## Folie\n",
        "Line 3: '{.internal}' before a '#' or '##' heading: write it at the end of the heading",
    ),
    ("# T\n\n> ## Zitat {.internal}\n", "Line 3: '{.internal}' goes on a '#' or '##' heading"),
    ("# T\n\n{.internal=ja}\nText\n", "The block marker '{.internal}' takes no value"),
]


@pytest.mark.parametrize("generate", [docx_text, pptx_text, pdf_text])
@pytest.mark.parametrize(("markdown", "message"), MISTAKES)
def test_mistakes_raise_in_every_version(generate: Generate, markdown: str, message: str) -> None:
    for chosen in Audience:
        with pytest.raises(DocumentConversionError) as error:
            generate(markdown, chosen)
        assert message in error.value.reason


def test_a_solution_may_follow_or_stand_in_its_exercise() -> None:
    nested = "# T\n\n:::: exercise\nA\n\n::: solution\nB\n:::\n::::\n"
    following = "# T\n\n::: exercise\nA\n:::\n\n::: solution\nB\n:::\n"
    for markdown in (nested, following):
        _, text = docx_text(markdown, Audience.TRAINER)
        assert "A" in text and "B" in text
        _, text = docx_text(markdown, Audience.INTERN)
        assert "B" not in text.split("\n")


def test_the_title_slide_of_a_deck_is_never_internal() -> None:
    markdown = "# Titel {.internal}\n\n## Folie\n\nText\n"
    with pytest.raises(DocumentConversionError) as error:
        pptx_text(markdown, Audience.TRAINER)
    assert "Line 1: The first '#' heading is the title slide" in error.value.reason
    # In Word the first '#' is a chapter like any other.
    _, text = docx_text(markdown, Audience.KUNDE)
    assert "Titel" not in text and "Text" not in text


def test_internal_notes_and_containers_inside_others() -> None:
    markdown = (
        "# T\n\n## Folie\n\n:::: panel\nKarte sichtbar\n\n::: internal\nIntern\n"
        ":::\n::::\n\n{.internal}\n::: notes\nInterne Notiz\n:::\n"
    )
    _, kunde = pptx_text(markdown, Audience.KUNDE)
    _, intern = pptx_text(markdown, Audience.INTERN)
    assert "Karte" in kunde and "Intern" not in kunde and "Interne Notiz" not in kunde
    assert "Intern" in intern and "Interne Notiz" in intern


# ---------------------------------------------------------------------- filtering itself


def test_unwrapped_blocks_move_up_a_level() -> None:
    tokens = parse("::: exercise\n- a\n:::\n")
    kept = audience.filter_tokens(tokens, Audience.KUNDE)
    assert [t.type for t in kept][:2] == ["bullet_list_open", "list_item_open"]
    assert kept[0].level == 0 and kept[1].level == 1


def test_versions_are_those_that_differ() -> None:
    docx = DocumentFormat.DOCX
    assert audience.versions("# T\n\nText\n", docx) == (Audience.KUNDE,)
    only_solutions = "# T\n\n::: exercise\nA\n:::\n\n::: solution\nB\n:::\n"
    assert audience.versions(only_solutions, docx) == (Audience.KUNDE, Audience.TRAINER)
    only_internal = "# T\n\n::: internal\nA\n:::\n"
    assert audience.versions(only_internal, docx) == (Audience.KUNDE, Audience.INTERN)
    assert audience.versions(DECK, docx) == tuple(Audience)


def test_the_suffixes() -> None:
    assert [a.suffix for a in Audience] == ["", "-intern", "-trainer"]


# ---------------------------------------------------------------------- check and round trips


def test_check_counts_each_version() -> None:
    document = MarkdownDocument(DECK)
    kunde = check(document, DocumentFormat.PPTX, CheckOptions(audience=Audience.KUNDE))
    trainer = check(document, DocumentFormat.PPTX, CheckOptions(audience=Audience.TRAINER))
    assert isinstance(kunde.stats, DeckStats) and isinstance(trainer.stats, DeckStats)
    assert kunde.stats.slides < trainer.stats.slides
    assert NoteCodes.AUDIENCE_OMITTED in kunde.codes()
    document = MarkdownDocument("---\ntitel: Schulung\n---\n" + DECK)
    report = check(document, DocumentFormat.DOCX, CheckOptions(audience=Audience.KUNDE))
    full = check(document, DocumentFormat.DOCX, CheckOptions(audience=Audience.TRAINER))
    assert isinstance(report.stats, ReportStats) and isinstance(full.stats, ReportStats)
    assert report.stats.words < full.stats.words


@pytest.mark.parametrize("chosen", list(Audience), ids=lambda a: a.value)
def test_the_round_trip_of_each_version(chosen: Audience) -> None:
    output = io.BytesIO()
    options = PptxOptions(audience=chosen, code_block_renderers=())
    PptxGenerator().generate(MarkdownDocument(DECK), output, options)
    deck = PptxConverter().convert(output.getvalue()).text
    assert_matches_expected(SAMPLES / f"fassungen-{chosen.value}.roundtrip.expected.md", deck)
    output = io.BytesIO()
    word = DocxOptions(variant=WordVariant.PORTRAIT_NO_COVER, audience=chosen)
    DocxGenerator().generate(MarkdownDocument(DECK), output, word)
    report = DocxConverter().convert(output.getvalue()).text
    assert_matches_expected(
        SAMPLES / f"fassungen-{chosen.value}-bericht.roundtrip.expected.md", report
    )


# ---------------------------------------------------------------------- ./run.sh generate


def load_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "generate_tool", REPO / "tools" / "generate" / "generate.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_tool_names_each_version(tmp_path: Path) -> None:
    tool = load_tool()
    source = tmp_path / "kurs-praesentation.md"
    source.write_text(DECK, encoding="utf-8")
    assert tool.main([str(source), "--audience", "alle", "--out", str(tmp_path / "out")]) == 0
    written = sorted(p.name for p in (tmp_path / "out").iterdir())
    assert written == [
        "kurs-praesentation-intern.pptx",
        "kurs-praesentation-trainer.pptx",
        "kurs-praesentation.pptx",
    ]
    source.write_text("---\nfassung: intern\ntitel: Kurs\n---\n" + DECK, encoding="utf-8")
    assert tool.main([str(source), "--docx", "--out", str(tmp_path / "front")]) == 0
    assert [p.name for p in (tmp_path / "front").iterdir()] == ["kurs-praesentation-intern.docx"]
    assert tool.main([str(source), "--audience", "jeder"]) == 1
