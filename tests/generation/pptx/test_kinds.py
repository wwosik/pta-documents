"""E04-S04: the PTA slide kinds (agenda, interim conclusion, quote, contact) and the PTA chart
layouts."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from lxml import etree
from PIL import Image

from pta_documents import NoteCodes
from pta_documents.charts import ChartKind, ChartSeries, ChartSpec
from pta_documents.conversions.pptx import PptxConverter
from pta_documents.design import slides as design
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.renderers import (
    ChartGraphic,
    CodeBlockGraphic,
    CodeBlockRequest,
)
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import DocumentResource, MarkdownDocument
from tests.expected import assert_matches_expected
from tests.generation.pptx.conftest import generate, layout_names, open_pptx, texts

SAMPLES = Path(__file__).parent / "samples"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = {"a": A, "p": P}
LAY = design.LAYOUTS
PH = design.PLACEHOLDERS


def photo(width: int = 700, height: int = 890) -> DocumentResource:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (0, 111, 185)).save(buffer, "PNG")
    return DocumentResource("foto.png", "image/png", buffer.getvalue())


SAMPLE = (SAMPLES / "layouts-pta.md").read_text(encoding="utf-8")


def sample_deck() -> bytes:
    return generate(SAMPLE, resources=(photo(),))


def indices(slide: Any) -> set[int]:
    return {shape.placeholder_format.idx for shape in slide.placeholders}


def find(element: etree._Element, path: str) -> list[etree._Element]:
    result = etree.XPath(path, namespaces=NS)(element)
    assert isinstance(result, list)
    return [e for e in result if isinstance(e, etree._Element)]


def fails(markdown: str, *, resources: tuple[DocumentResource, ...] = ()) -> str:
    with pytest.raises(DocumentConversionError) as error:
        generate(markdown, resources=resources)
    return error.value.reason


# ---------------------------------------------------------------------- the sample


def test_the_sample_uses_the_pta_layouts(review_dir: Path) -> None:
    data = sample_deck()
    (review_dir / "layouts-pta.pptx").write_bytes(data)
    assert layout_names(data) == [
        LAY.title_image_02,
        LAY.agenda_short,
        LAY.chapter,
        LAY.interim_01,
        LAY.quote_01,
        LAY.chapter,
        LAY.agenda_long,
        LAY.contact_02,
        LAY.contact_text,
        LAY.closing,
    ]


def test_the_sample_generates_without_notes() -> None:
    document = MarkdownDocument(SAMPLE, (photo(),))
    assert PptxGenerator().generate(document, io.BytesIO()).notes == ()


def test_the_sample_round_trips_through_the_converter() -> None:
    markdown = PptxConverter().convert(sample_deck()).text
    assert_matches_expected(SAMPLES / "layouts-pta.roundtrip.expected.md", markdown)


def test_word_accepts_the_slide_kinds() -> None:
    document = MarkdownDocument(SAMPLE, (photo(),))
    result = DocxGenerator().generate(document, io.BytesIO())
    assert result.pages is None or result.pages >= 1


# ---------------------------------------------------------------------- agenda


def test_the_agenda_numbers_its_items_and_drops_unused_places() -> None:
    data = generate("# D\n\n## Agenda {.agenda}\n\n- Lage\n- **Ziel**\n")
    slide = open_pptx(data).slides[1]
    assert slide.slide_layout.name == LAY.agenda_short
    found = texts(slide)
    assert found[0] == "Agenda"
    assert (found[14], found[15], found[16], found[17]) == ("01", "Lage", "02", "Ziel")
    assert not indices(slide) & {18, 19, 20, 21}
    # The rule between the two items stays, those under the last item go.
    assert 30 in indices(slide)
    assert not indices(slide) & {31, 32}


def test_five_to_eight_items_take_the_long_agenda() -> None:
    items = "".join(f"- Punkt {n}\n" for n in range(1, 9))
    slide = open_pptx(generate(f"# D\n\n## Agenda {{.agenda}}\n\n{items}")).slides[1]
    assert slide.slide_layout.name == LAY.agenda_long
    assert texts(slide)[28] == "08" and texts(slide)[29] == "Punkt 8"
    assert set(PH.agenda_rules) <= indices(slide)


def test_an_agenda_without_a_list_lists_the_chapters() -> None:
    markdown = (
        "# Deck\n\n## Agenda {.agenda}\n\n# Lage\n\n"
        '# Ziel {layout="Trennfolie"}\n\n# Danke {.closing}\n'
    )
    slide = open_pptx(generate(markdown)).slides[1]
    found = texts(slide)
    assert (found[15], found[17]) == ("Lage", "Ziel")
    assert 18 not in found


def test_without_agenda_there_is_no_agenda_slide() -> None:
    data = generate("# D\n\n## Agenda\n\n- Lage\n- Ziel\n\n# Lage\n")
    assert LAY.agenda_short not in layout_names(data)
    assert LAY.agenda_long not in layout_names(data)


@pytest.mark.parametrize(
    ("markdown", "message"),
    [
        (
            "# D\n\n## A {.agenda}\n\n" + "".join(f"- P{n}\n" for n in range(9)),
            "Line 3: An agenda holds 8 items at most, this one 9. Split it into two agenda",
        ),
        (
            '# D\n\n## A {.agenda layout="Agenda (kurz)"}\n\n'
            + "".join(f"- P{n}\n" for n in range(5)),
            "The layout 'Agenda (kurz)' holds 4 items",
        ),
        ("# D\n\n## A {.agenda}\n\nText\n\n- P\n", "Line 5: An agenda {.agenda} holds one list"),
        ("# D\n\n## A {.agenda}\n\n- P\n  - Q\n", "Each agenda item is one line of text."),
        ("# D\n\n## A {.agenda}\n", "the deck has none"),
        ('# D\n\n## A {.agenda layout="Nur Titel"}\n', "Valid layouts: 'Agenda (kurz)'"),
    ],
)
def test_agenda_mistakes(markdown: str, message: str) -> None:
    assert message in fails(markdown)


# ---------------------------------------------------------------------- interim and quote


def test_the_interim_conclusion_is_its_heading() -> None:
    data = generate("# D\n\n## Es geht ohne Ausfall {.interim}\n")
    slide = open_pptx(data).slides[1]
    assert slide.slide_layout.name == LAY.interim_01
    assert texts(slide)[0] == "Es geht ohne Ausfall"


def test_layout_chooses_the_sister_layout() -> None:
    data = generate(
        '# D\n\n## A {.interim layout="Zwischenfazit 02"}\n\n## Q {.quote layout="Zitat 02"}\n'
    )
    assert layout_names(data)[1:] == [LAY.interim_02, LAY.quote_02]


def test_the_source_of_a_quote_is_a_second_paragraph_in_light_type() -> None:
    data = generate("# D\n\n## Wer misst, misst Mist {.quote}\n\n— Unbekannt\n")
    slide = open_pptx(data).slides[1]
    assert slide.slide_layout.name == LAY.quote_01
    title: Any = slide.shapes.title
    paragraphs = find(title._element, "p:txBody/a:p")
    assert len(paragraphs) == 2
    source = find(paragraphs[1], "a:r/a:rPr")[0]
    assert source.get("sz") == "2400" and source.get("i") == "0"
    assert find(source, "a:latin")[0].get("typeface") == design.BODY_FONT
    assert "".join(t.text or "" for t in paragraphs[1].iter(f"{{{A}}}t")) == "— Unbekannt"


@pytest.mark.parametrize(
    ("markdown", "message"),
    [
        ("# D\n\n## A {.interim}\n\nText\n", "Line 5: An interim conclusion {.interim} is its"),
        ("# D\n\n## Q {.quote}\n\nA\n\nB\n", "takes one paragraph under it at most"),
        ("# D\n\n## Q {.quote}\n\n- A\n", "takes one paragraph under it at most"),
        (
            '# D\n\n## A {.interim layout="Zitat 01"}\n',
            "The slide kind .interim goes on its own PTA layouts, not on 'Zitat 01'.",
        ),
        ("# D\n\n## A {.interim}\n\n::: panel\nx\n:::\n", "takes no slide-layout Markdown"),
    ],
)
def test_interim_and_quote_mistakes(markdown: str, message: str) -> None:
    assert message in fails(markdown)


@pytest.mark.parametrize("generator", [PptxGenerator(), DocxGenerator()], ids=["pptx", "docx"])
@pytest.mark.parametrize(
    ("markdown", "message"),
    [
        (
            "# D\n\n## Q {.quote .dark}\n",
            "The slide kind .quote in '{.quote .dark}' has the PTA layout's own design "
            "and takes no .dark.",
        ),
        ('# D\n\n## Q {.agenda kicker="K"}\n', "takes no kicker"),
        ("# D\n\n## Q {.agenda .quote}\n", "name the slide kinds .agenda and .quote"),
        ("# Agenda {.agenda}\n", "The heading attribute '.agenda' in '{.agenda}' goes on a '##'"),
        ("# D\n\n## Q {.agenda .agenda}\n", "name .agenda twice"),
    ],
)
def test_slide_kind_attribute_mistakes_in_every_format(
    generator: PptxGenerator | DocxGenerator, markdown: str, message: str
) -> None:
    with pytest.raises(DocumentConversionError) as error:
        generator.generate(MarkdownDocument(f"---\ntitel: T\n---\n{markdown}"), io.BytesIO())
    assert message in error.value.reason


# ---------------------------------------------------------------------- contact


CONTACTS = """# D

## Ansprechpartner {.contact}

### Erika Muster

![Erika](foto.png)
+49 621 1
erika@pta.de
Projektleiterin

### Max Muster

Berater
"""


def test_contacts_fill_the_places_of_their_persons() -> None:
    data = generate(CONTACTS, resources=(photo(),))
    slide = open_pptx(data).slides[1]
    assert slide.slide_layout.name == LAY.contact_02
    found = texts(slide)
    assert (found[14], found[35], found[36], found[38]) == (
        "Erika Muster",
        "Projektleiterin",
        "erika@pta.de",
        "+49 621 1",
    )
    assert (found[40], found[41]) == ("Max Muster", "Berater")
    # What Max lacks is left out: no photo place, no empty e-mail or phone.
    assert not indices(slide) & {39, 42, 43}
    pictures = find(slide._element, "//p:pic")
    assert len(pictures) == 1
    links = [r.target_ref for r in slide.part.rels.values() if r.is_external]
    assert links == ["mailto:erika@pta.de"]


def test_one_person_with_text_takes_contact_with_text() -> None:
    markdown = (
        "# D\n\n## Kontakt {.contact}\n\n### Erika\n\nBeraterin\nerika@pta.de\n\n"
        "Sie berät seit zehn Jahren.\n\n- Netze\n"
    )
    slide = open_pptx(generate(markdown)).slides[1]
    assert slide.slide_layout.name == LAY.contact_text
    assert texts(slide)[PH.contact_text] == "Sie berät seit zehn Jahren.\nNetze"
    assert PH.contacts[0][0] not in indices(slide)


@pytest.mark.parametrize("persons", [1, 3, 4, 5])
def test_n_persons_take_contact_0n(persons: int) -> None:
    people = "".join(f"### P{n}\n\nRolle\n\n" for n in range(persons))
    slide = open_pptx(generate(f"# D\n\n## K {{.contact}}\n\n{people}")).slides[1]
    assert slide.slide_layout.name == design.CONTACT_LAYOUTS[persons - 1]
    assert texts(slide)[PH.contacts[persons - 1][1]] == f"P{persons - 1}"


@pytest.mark.parametrize(
    ("markdown", "message"),
    [
        (
            "# D\n\n## K {.contact}\n\n" + "".join(f"### P{n}\n\n" for n in range(6)),
            "Line 3: A contact slide holds 5 persons at most, this one 6.",
        ),
        ("# D\n\n## K {.contact}\n\nText\n", "Line 5: A contact slide {.contact} holds a ###"),
        ("# D\n\n## K {.contact}\n", "holds a ### heading per person (one to 5)"),
        (
            "# D\n\n## K {.contact}\n\n### P\n\na@b.de\nc@d.de\n",
            "The person 'P' has two lines of the kind e-mail",
        ),
        (
            "# D\n\n## K {.contact}\n\n### P\n\nRolle\n\nText\n\n### Q\n\nRolle\n",
            "goes on a contact slide of one person ('Kontakt mit Text'); this one has 2.",
        ),
        (
            "# D\n\n## K {.contact}\n\n### P\n\nRolle\n\n| a |\n|---|\n| b |\n",
            "takes text beside the contact lines only",
        ),
        (
            '# D\n\n## K {.contact layout="Kontakt 01"}\n\n### P\n\n### Q\n',
            "The layout 'Kontakt 01' has no place for 2 persons; 'Kontakt 02' has.",
        ),
    ],
)
def test_contact_mistakes(markdown: str, message: str) -> None:
    assert message in fails(markdown)


def test_two_photos_of_one_person_are_a_mistake() -> None:
    markdown = "# D\n\n## K {.contact}\n\n### P\n\n![a](foto.png)\n![b](foto.png)\n"
    assert "one photo at most" in fails(markdown, resources=(photo(),))


# ---------------------------------------------------------------------- charts


@dataclass
class ChartRenderer:
    """Turns ``chart`` blocks into a chart whose title, unit and source are the block's lines."""

    authoring_guide: str | None = None

    def render(self, request: CodeBlockRequest) -> CodeBlockGraphic | None:
        if request.info.split()[0] != "chart":
            return None
        title, unit, source = ([*request.code.splitlines(), "", "", ""])[:3]
        spec = ChartSpec(
            ChartKind.BAR,
            ("Q1", "Q2"),
            (ChartSeries("Umsatz", (1.0, 2.0)), ChartSeries("Kosten", (0.5, None))),
            title=title or None,
            unit=unit or None,
            source=source or None,
        )
        return ChartGraphic(spec, object())


def chart_deck(body: str) -> bytes:
    output = io.BytesIO()
    options = PptxOptions(code_block_renderers=(ChartRenderer(),))
    PptxGenerator().generate(MarkdownDocument(f"# D\n\n{body}"), output, options)
    return output.getvalue()


CHART = "```chart\nUmsatz\nMio. EUR\nQuelle: PTA\n```\n"


def charts(slide: Any) -> list[Any]:
    return [shape for shape in slide.shapes if getattr(shape, "has_chart", False)]


def test_a_chart_fills_the_chart_placeholder(review_dir: Path) -> None:
    data = chart_deck(f"## Zahlen\n\n{CHART}")
    (review_dir / "chart-layouts.pptx").write_bytes(data)
    slide = open_pptx(data).slides[1]
    assert slide.slide_layout.name == LAY.chart
    found = texts(slide)
    assert (found[12], found[13], found[14]) == ("Umsatz", "Mio. EUR", "Quelle: PTA")
    (frame,) = charts(slide)
    assert frame.placeholder_format.idx == PH.chart
    chart = frame.chart
    assert not chart.has_title
    assert [s.name for s in chart.plots[0].series] == ["Umsatz", "Kosten"]
    assert chart.plots[0].series[1].values == (0.5, None)


def test_empty_chart_placeholders_are_left_out() -> None:
    slide = open_pptx(chart_deck("## Zahlen\n\n```chart\n```\n")).slides[1]
    assert not indices(slide) & {12, 13, 14}
    assert len(charts(slide)) == 1


@pytest.mark.parametrize(
    ("body", "layout"),
    [
        (f"## Z\n\nVorher\n\n{CHART}", LAY.text_and_chart),
        (f"## Z\n\n{CHART}\nNachher\n", LAY.chart_and_text),
        (f"## Z\n\n{CHART}\n{CHART}", LAY.two_charts),
        (f"## Z\n\n::: columns\n{CHART}\n---\n\n{CHART}:::\n", LAY.two_charts),
    ],
    ids=["text-first", "chart-first", "two", "columns"],
)
def test_chart_layouts(body: str, layout: str) -> None:
    slide = open_pptx(chart_deck(body)).slides[1]
    assert slide.slide_layout.name == layout
    if layout == LAY.two_charts:
        assert [c.placeholder_format.idx for c in charts(slide)] == [PH.chart, PH.second_chart[3]]
        assert texts(slide)[PH.second_chart[0]] == "Umsatz"
    else:
        assert texts(slide)[PH.chart_text] in ("Vorher", "Nachher")


def test_a_chart_beside_a_table_goes_on_a_slide_of_its_own() -> None:
    data = chart_deck(f"## Z\n\n{CHART}\n| a |\n|---|\n| b |\n")
    assert layout_names(data)[1:] == [LAY.chart, LAY.title_only]


def test_a_chart_on_a_flow_slide_is_a_mistake() -> None:
    with pytest.raises(DocumentConversionError) as error:
        chart_deck(f"## Z\n\n> [!NOTE]\n> x\n\n{CHART}")
    assert error.value.reason.startswith("Line 8: A chart goes on a slide of its own")


def test_a_named_chart_layout_takes_the_chart() -> None:
    data = chart_deck(f'## Z {{layout="Titel und Diagramm"}}\n\n{CHART}')
    slide = open_pptx(data).slides[1]
    assert slide.slide_layout.name == LAY.chart
    assert len(charts(slide)) == 1


def test_a_chart_needs_no_note() -> None:
    output = io.BytesIO()
    options = PptxOptions(code_block_renderers=(ChartRenderer(),))
    result = PptxGenerator().generate(MarkdownDocument(f"# D\n\n## Z\n\n{CHART}"), output, options)
    assert NoteCodes.CODE_NOT_DRAWN not in [n.code for n in result.notes]


def test_a_chart_without_renderer_stays_code() -> None:
    data = generate(f"# D\n\n## Z\n\n{CHART}")
    assert layout_names(data)[1] == LAY.title_only


def test_charts_in_word_follow_with_e06() -> None:
    from pta_documents.generation.docx.options import DocxOptions

    with pytest.raises(DocumentConversionError) as error:
        DocxGenerator().generate(
            MarkdownDocument(f"# D\n\n## Z\n\n{CHART}"),
            io.BytesIO(),
            DocxOptions(code_block_renderers=(ChartRenderer(),)),
        )
    assert error.value.format is DocumentFormat.DOCX
