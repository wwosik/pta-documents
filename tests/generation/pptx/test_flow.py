"""E04-S03: flow slides in the PTA style (port of DocLibs ``SlideLayoutTests``), the PTA
conclusion and comment boxes, marks and status colours on every slide."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from lxml import etree

from pta_documents import NoteCodes
from pta_documents.conversions.pptx import PptxConverter
from pta_documents.design import colors
from pta_documents.design import slides as design
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.markdown import MarkdownDocument
from tests.conftest import SOURCE_TEMPLATES
from tests.expected import assert_matches_expected
from tests.generation.pptx.conftest import generate, layout_names

SAMPLES = Path(__file__).parent / "samples"
LAYOUTS = (Path(__file__).parents[1] / "common" / "samples" / "layouts.md").read_text(
    encoding="utf-8"
)
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = {"a": A, "p": P}
CM = 360_000


def slides(data: bytes) -> list[etree._Element]:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = sorted(
            (n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")),
            key=lambda n: int(n[len("ppt/slides/slide") : -4]),
        )
        return [etree.fromstring(z.read(n)) for n in names]


def find(root: etree._Element, path: str) -> list[etree._Element]:
    result = root.xpath(path, namespaces=NS)
    assert isinstance(result, list)
    return [e for e in result if isinstance(e, etree._Element)]


def text(element: etree._Element) -> str:
    return "".join(t.text or "" for t in element.iter(f"{{{A}}}t"))


def shapes(root: etree._Element) -> list[etree._Element]:
    """The shapes the generator drew (no placeholders), in drawing order."""
    return find(root, "//p:spTree/p:sp[not(p:nvSpPr/p:nvPr/p:ph)]")


def boxes(root: etree._Element) -> list[etree._Element]:
    """Drawn shapes without text: cards, panels, alert areas and bars, code areas."""
    return [s for s in shapes(root) if find(s, "p:spPr/a:prstGeom") and not text(s)]


def geometry(shape: etree._Element) -> tuple[int, int, int, int]:
    off = find(shape, "p:spPr/a:xfrm/a:off")[0]
    ext = find(shape, "p:spPr/a:xfrm/a:ext")[0]
    return int(off.get("x", 0)), int(off.get("y", 0)), int(ext.get("cx", 0)), int(ext.get("cy", 0))


def fill(shape: etree._Element) -> str | None:
    found = find(shape, "p:spPr/a:solidFill/a:srgbClr")
    return found[0].get("val") if found else None


def run_properties(root: etree._Element, words: str) -> etree._Element:
    for run in find(root, "//a:r"):
        if text(run) == words:
            return find(run, "a:rPr")[0]
    raise AssertionError(f"no run {words!r}")


def run_color(r_pr: etree._Element) -> str | None:
    found = find(r_pr, "a:solidFill/a:srgbClr")
    return found[0].get("val") if found else None


def shape_with(root: etree._Element, words: str) -> etree._Element:
    return next(s for s in find(root, "//p:sp") if text(s) == words)


def layouts_deck() -> bytes:
    return generate(LAYOUTS)


# ---------------------------------------------------------------------- the sample


def test_the_sample_is_on_title_only_and_its_shapes_lie_on_the_grid(review_dir: Path) -> None:
    data = layouts_deck()
    (review_dir / "layouts.pptx").write_bytes(data)
    assert layout_names(data) == [
        "Titelfolie mit Bild 02",
        *["Nur Titel"] * 6,
        "Titel und Text (zweispaltig)",
        "Nur Titel",
        "Nur Titel",
    ]
    area = design.CONTENT_AREA
    guides = {design.cm(start) for start, _ in design.COLUMN_GUIDES} | {
        x for x, _ in design.grid(3)
    }
    for number, root in enumerate(slides(data)[1:], start=2):
        for shape in [*shapes(root), *find(root, "//p:graphicFrame")]:
            if find(shape, "p:xfrm"):
                off, ext = find(shape, "p:xfrm/a:off")[0], find(shape, "p:xfrm/a:ext")[0]
                x, y = int(off.get("x", 0)), int(off.get("y", 0))
                w, h = int(ext.get("cx", 0)), int(ext.get("cy", 0))
            else:
                x, y, w, h = geometry(shape)
            if y < area.top:  # the kicker, above the title
                assert y == design.FLOW.kicker_top, number
                continue
            assert area.left <= x and x + w <= area.right + 1, (number, text(shape))
            assert area.top <= y and y + h <= area.bottom + 1, (number, text(shape))
        found = boxes(root)
        areas = [geometry(b) for b in found if fill(b) is not None]
        for card in found:
            x, y, _, _ = geometry(card)
            inside = any(ax < x and ay < y < ay + ah for ax, ay, _, ah in areas)
            if fill(card) is None and not inside:  # a card on the slide: it starts on a guide
                assert x in guides, number


def test_the_sample_round_trips_through_the_converter() -> None:
    markdown = PptxConverter().convert(layouts_deck()).text
    assert_matches_expected(SAMPLES / "layouts.roundtrip.expected.md", markdown)


def test_the_sample_generates_without_notes() -> None:
    result = PptxGenerator().generate(MarkdownDocument(LAYOUTS), io.BytesIO())
    assert result.notes == ()


def test_all_colours_come_from_the_colour_module_and_signals_only_mean_status() -> None:
    palette = {
        value
        for name, value in vars(colors).items()
        if name.isupper() and isinstance(value, str) and len(value) == 6
    }
    signals = set(colors.SIGNALS)
    for root in slides(layouts_deck())[1:]:
        for colour in find(root, "//a:srgbClr"):
            value = colour.get("val")
            assert value in palette, value
            if value in signals:
                # A signal colour is the colour of a status run: coloured words or a label dot.
                parents = [e.tag for e in colour.iterancestors()]
                assert parents[1] == f"{{{A}}}rPr", value


def test_run_properties_keep_the_schema_order() -> None:
    order = ["ln", "noFill", "solidFill", "gradFill", "effectLst", "highlight", "latin", "ea"]
    order += ["cs", "sym", "hlinkClick"]
    for root in slides(layouts_deck()):
        for r_pr in find(root, "//a:rPr"):
            names = [etree.QName(child).localname for child in r_pr]
            assert names == sorted(names, key=order.index), names


# ---------------------------------------------------------------------- which slides flow


def test_sections_without_layouts_stay_text_and_table_slides() -> None:
    data = generate(
        "## Text\n\n- a\n\n## Table\n\n| a |\n| - |\n| `x` |\n\n## Code\n\nRun `a` now.\n"
    )
    assert layout_names(data) == ["Titel und Text", "Nur Titel", "Titel und Text"]
    cell = find(slides(data)[1], "//a:tc")[-1]
    assert find(cell, ".//a:latin")[0].get("typeface") == "Consolas"
    assert "●" not in text(cell)


def test_a_code_list_outside_a_container_stays_a_list() -> None:
    root = slides(generate('## T {kicker="K"}\n\n- `--force` overwrites\n'))[0]
    assert all(not find(s, "p:spPr/a:ln/a:solidFill") for s in shapes(root))
    assert "--force overwrites" in [text(p) for p in find(root, "//a:p")]


def test_a_named_layout_takes_no_flow_content_but_title_only_does() -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate('## T {layout="Titel und Text"}\n\n> [!NOTE]\n> x\n')
    assert "goes on the layout 'Nur Titel' only" in error.value.reason
    assert "(line 1)" in error.value.reason
    data = generate('## T {layout="Nur Titel"}\n\n> [!NOTE]\n> x\n')
    assert layout_names(data) == ["Nur Titel"]
    assert len(boxes(slides(data)[0])) == 2


def test_two_equal_columns_of_text_take_the_two_column_layout() -> None:
    columns = "::: columns{}\nLinks\n\n---\n\nRechts\n:::\n"
    assert layout_names(generate("## T\n\n" + columns.format(""))) == [
        "Titel und Text (zweispaltig)"
    ]
    assert layout_names(generate("## T\n\n" + columns.format(" 1:2"))) == ["Nur Titel"]
    assert layout_names(generate("## T {.dark}\n\n" + columns.format(""))) == ["Nur Titel"]
    root = slides(generate("## T\n\n" + columns.format(" 1:2")))[0]
    left, right = (geometry(s) for s in shapes(root))
    assert left[0] == design.CONTENT_AREA.left
    assert right[0] + right[2] == design.CONTENT_AREA.right


# ---------------------------------------------------------------------- kicker and dark slides


def test_the_kicker_sits_above_the_title() -> None:
    root = slides(generate('## Titel {kicker="Warum"}\n\nText\n'))[0]
    kicker = shape_with(root, "Warum")
    x, y, _, _ = geometry(kicker)
    assert (x, y) == (design.cm(1.33), design.cm(1.60))
    r_pr = run_properties(root, "Warum")
    assert (r_pr.get("sz"), r_pr.get("b"), r_pr.get("cap")) == ("1200", "1", "all")
    assert run_color(r_pr) == colors.DARK_BLUE
    title = find(root, "//p:sp[p:nvSpPr/p:nvPr/p:ph/@type='title']")[0]
    assert text(title) == "Titel"


def test_a_dark_slide_has_the_title_slide_background_and_white_text() -> None:
    root = slides(generate('## Dunkel {.dark kicker="K"}\n\nText\n'))[0]
    background = find(root, "p:cSld/p:bg/p:bgPr/a:gradFill")
    assert background, "the gradient of 'Titelfolie ohne Bild'"
    for words in ("Dunkel", "Text", "K"):
        assert run_color(run_properties(root, words)) == colors.WHITE


# ---------------------------------------------------------------------- containers


def test_cards_are_outlined_rectangles_on_the_grid_with_their_figure_first() -> None:
    root = slides(
        generate("## T\n\n::: cards\n### One\n**26**\n\nfirst\n\n### Two\nsecond\n:::\n")
    )[0]
    cards = boxes(root)
    assert len(cards) == 2
    for card in cards:
        assert find(card, "p:spPr/a:prstGeom")[0].get("prst") == "rect"
        assert find(card, "p:spPr/a:noFill")
        line = find(card, "p:spPr/a:ln")[0]
        assert line.get("w") == "9525"
        assert find(line, "a:solidFill/a:srgbClr")[0].get("val") == colors.GREY_LIGHT
    one, two = geometry(cards[0]), geometry(cards[1])
    assert (one[0], one[2]) == (design.cm(1.33), design.cm(15.10))
    assert (two[0], two[2]) == (design.cm(17.43), design.cm(15.10))
    assert one[1] == two[1] and one[3] == two[3]
    figure = run_properties(root, "26")
    assert (figure.get("sz"), figure.get("b"), run_color(figure)) == ("3200", "1", colors.PTA_BLUE)
    title = run_properties(root, "One")
    assert (title.get("sz"), run_color(title)) == ("1800", colors.PTA_BLUE)
    assert run_properties(root, "first").get("sz") == "1400"
    order = [text(s) for s in shapes(root) if text(s)]
    assert order == ["26", "One", "first", "Two", "second"]


def test_four_cards_take_the_four_columns_and_a_fifth_a_new_row() -> None:
    cards = "".join(f"### {n}\n{n}\n\n" for n in "abcde")
    root = slides(generate(f"## T\n\n::: cards\n{cards}:::\n"))[0]
    found = [geometry(b) for b in boxes(root)]
    assert [x for x, _, _, _ in found[:4]] == [design.cm(s) for s, _ in design.COLUMN_GUIDES]
    assert {w for _, _, w, _ in found[:4]} == {design.cm(7.00)}
    assert found[4][1] > found[0][1] and found[4][0] == design.cm(1.33)


def test_cards_and_rows_take_the_list_form() -> None:
    root = slides(
        generate(
            "## T\n\n::: cards\n- **One** – first\n- **Two:** second\n:::\n\n"
            "::: rows\n- **Term** – description\n- **Other** - more\n:::\n"
        )
    )[0]
    order = [text(s) for s in shapes(root) if text(s)]
    assert order == ["One", "first", "Two", "second", "Term", "description", "Other", "more"]
    rules = find(root, "//p:cxnSp")
    assert len(rules) == 3  # above each row and below the last
    colours = [find(r, ".//a:srgbClr")[0].get("val") for r in rules]
    assert colours == [colors.GREY_LIGHT, colors.GREY_LIGHT, colors.TEXT_SLIDES]
    assert run_color(run_properties(root, "Term")) == colors.PTA_BLUE


def test_panels_are_light_grey_and_dark_panels_dark_blue_with_white_text() -> None:
    root = slides(generate("## T\n\n::: panel\nHell\n:::\n\n::: panel dark\nDunkel\n:::\n"))[0]
    assert [fill(b) for b in boxes(root)] == [colors.GREY_LIGHT, colors.DARK_BLUE]
    assert run_color(run_properties(root, "Dunkel")) == colors.WHITE
    assert run_color(run_properties(root, "Hell")) is None  # the theme's 404040


def test_alerts_have_a_bar_in_pta_blue_or_yellow_and_upright_text() -> None:
    root = slides(generate("## T\n\n> [!NOTE]\n> Note\n\n> [!WARNING]\n> Careful\n"))[0]
    found = boxes(root)
    assert [fill(b) for b in found] == [
        colors.GREY_LIGHT,
        colors.PTA_BLUE,
        colors.GREY_LIGHT,
        colors.YELLOW,
    ]
    assert geometry(found[1])[2] == design.cm(0.15)
    assert run_properties(root, "Note").get("i") is None


def test_tags_are_chips_and_labelled_tags_put_the_label_beside_the_text() -> None:
    root = slides(generate("## T\n\n`a` `b` `c`\n\n::: panel\n- `x` first\n- `yy` second\n:::\n"))[
        0
    ]
    chips = [s for s in shapes(root) if find(s, "p:spPr/a:ln/a:solidFill")]
    assert [text(c) for c in chips] == ["a", "b", "c", "x", "yy"]
    for chip in chips:
        assert find(chip, ".//a:latin")[0].get("typeface") == "Consolas"
        line = find(chip, "p:spPr/a:ln")[0]
        assert find(line, ".//a:srgbClr")[0].get("val") == colors.PTA_BLUE
    assert run_properties(root, "x").get("b") == "1"
    assert run_properties(root, "a").get("sz") == "1200"
    first = shape_with(root, "first")
    assert geometry(first)[0] > geometry(chips[3])[0] + geometry(chips[3])[2]


def test_code_on_a_flow_slide_sits_on_a_grey_area_with_more_line_spacing() -> None:
    root = slides(generate('## T {kicker="K"}\n\n```\na = 1\nb = 2\n```\n'))[0]
    assert [fill(b) for b in boxes(root)] == [colors.GREY_LIGHT]
    lines = [p for p in find(root, "//a:p") if text(p) in ("a = 1", "b = 2")]
    assert len(lines) == 2
    for line in lines:
        assert find(line, "a:pPr/a:lnSpc/a:spcPct")[0].get("val") == "130000"
        assert find(line, ".//a:latin")[0].get("typeface") == "Consolas"


def test_a_flow_slide_stacks_several_tables() -> None:
    root = slides(generate('## T {kicker="K"}\n\n| a |\n| - |\n| 1 |\n\n| b |\n| - |\n| 2 |\n'))[0]
    tables = find(root, "//p:graphicFrame")
    assert len(tables) == 2
    first, second = (int(find(t, "p:xfrm/a:off")[0].get("y", 0)) for t in tables)
    assert second > first


def test_the_statement_is_large_bold_and_pta_blue() -> None:
    root = slides(generate("## T\n\n::: statement\nBig claim.\n\nSmall print.\n:::\n"))[0]
    big = run_properties(root, "Big claim.")
    assert (big.get("sz"), big.get("b"), run_color(big)) == ("2400", "1", colors.PTA_BLUE)
    assert run_properties(root, "Small print.").get("sz") == "1800"


# ---------------------------------------------------------------------- marks and status


def test_marked_rows_are_yellow_and_status_labels_get_a_dot_in_their_colour() -> None:
    data = generate(
        "---\nstatus.success: Fertig\nstatus.danger: Spät; Blockiert\n---\n\n"
        '## T {kicker="K"}\n\n| a | b |\n| - | - |\n| ==x== | `Fertig` |\n| y | `Spät` |\n'
        "| z | `Später` |\n\nSome ==marked== text and [late]{.danger} work.\n"
    )
    root = slides(data)[0]
    rows = find(root, "//a:tr")

    def cell_fill(row: int, column: int) -> str | None:
        found = find(find(rows[row], "a:tc")[column], "a:tcPr/a:solidFill/a:srgbClr")
        return found[0].get("val") if found else None

    assert cell_fill(1, 0) == colors.YELLOW and cell_fill(1, 1) == colors.YELLOW
    assert cell_fill(2, 0) is None
    dots = [run_properties_of(r) for r in find(root, "//a:r") if text(r) == "● "]
    assert [run_color(d) for d in dots] == [
        colors.SIGNAL_GREEN,
        colors.SIGNAL_RED,
        colors.GREY_MID,
    ]
    assert all(d.get("b") is None for d in dots)
    label = run_properties(root, "Fertig")
    assert run_color(label) == colors.TEXT_SLIDES and label.get("b") is None
    marked = run_properties(root, "marked")
    assert marked.get("b") == "1"
    assert find(marked, "a:highlight/a:srgbClr")[0].get("val") == colors.YELLOW
    late = run_properties(root, "late")
    assert (late.get("b"), run_color(late)) == ("1", colors.SIGNAL_RED)


def run_properties_of(run: etree._Element) -> etree._Element:
    return find(run, "a:rPr")[0]


def test_marks_and_coloured_words_also_on_text_and_table_slides() -> None:
    data = generate(
        "## Text\n\nA ==mark== and [done]{.success}.\n\n## Table\n\n| a |\n| - |\n| ==x== |\n"
    )
    text_slide, table_slide = slides(data)
    assert find(run_properties(text_slide, "mark"), "a:highlight")
    assert run_color(run_properties(text_slide, "done")) == colors.SIGNAL_GREEN
    cell = find(table_slide, "//a:tr")[1]
    assert find(cell, "a:tc/a:tcPr/a:solidFill/a:srgbClr")[0].get("val") == colors.YELLOW


# ---------------------------------------------------------------------- conclusion box


def template_conclusion() -> etree._Element:
    with zipfile.ZipFile(SOURCE_TEMPLATES / "PTA-Powerpoint-Vorlagensammlung.pptx") as z:
        root = etree.fromstring(z.read("ppt/slides/slide43.xml"))
    return next(s for s in find(root, "//p:sp") if text(s).startswith("Platzhalter für eine F"))


def test_the_conclusion_box_has_the_measures_of_the_template() -> None:
    root = slides(generate("## T\n\nText\n\n::: conclusion\nDas Fazit.\n:::\n"))[0]
    box = shape_with(root, "Das Fazit.")
    model = template_conclusion()
    for ours, theirs in zip(geometry(box), geometry(model), strict=True):
        assert abs(ours - theirs) <= CM // 100  # within 0.1 mm
    assert fill(box) == colors.DARK_BLUE
    body_pr = find(box, "p:txBody/a:bodyPr")[0]
    model_pr = find(model, "p:txBody/a:bodyPr")[0]
    for inset in ("lIns", "rIns", "tIns", "bIns"):
        assert body_pr.get(inset) == model_pr.get(inset), inset
    r_pr = run_properties(root, "Das Fazit.")
    assert (r_pr.get("sz"), r_pr.get("b"), run_color(r_pr)) == ("1800", "1", colors.WHITE)
    above = shape_with(root, "Text")
    assert geometry(above)[1] < geometry(box)[1]


def test_a_long_conclusion_shrinks_and_a_too_long_one_is_refused() -> None:
    words = " ".join(["Fazit"] * 36)
    root = slides(generate(f"## T\n\n::: conclusion\n{words}\n:::\n"))[0]
    assert run_properties(root, words).get("sz") in ("1600", "1400")
    with pytest.raises(DocumentConversionError) as error:
        generate("## T\n\n::: conclusion\n" + " ".join(["Fazit"] * 80) + "\n:::\n")
    assert "takes 2 lines at most" in error.value.reason


@pytest.mark.parametrize(
    ("markdown", "message"),
    [
        (
            "## T\n\n::: conclusion\nA\n:::\n\n::: conclusion\nB\n:::\n",
            "Line 7: A slide holds one '::: conclusion' at most.",
        ),
        (
            ":::: panel\n::: conclusion\nA\n:::\n::::\n",
            "goes on the slide itself, not inside another container",
        ),
        ("## T\n\n::: conclusion\n| a |\n| - |\n| 1 |\n:::\n", "holds text only"),
        ("## T\n\n::: comment\nA\n:::\n", "Line 3: A '::: comment' comments on the block"),
        (
            "## T\n\n::: cards\nText first\n\n### Card\n:::\n",
            "Line 4: In '::: cards', each card starts with a ### heading",
        ),
        ("## T\n\n::: cards\n:::\n", "A '::: cards' holds no cards."),
        ("## T\n\n::: rows\n- plain item\n:::\n", "starts with **bold** text, its title."),
        ("## T\n\n::: rows\nText\n:::\n", "holds one list of '- **Term** – description'"),
        ("## T\n\n::: rows\n- **a** b\n\n  ```\n  x\n  ```\n:::\n", "hold text only"),
        ("## T\n\n::: statement\n- a\n:::\n", "starts with a paragraph, its statement."),
        ("## T\n\n::: columns\nA\n:::\n", "Line 3: A '::: columns' holds two or three"),
        ("## T\n\n::: columns 1:2:3\nA\n\n---\n\nB\n:::\n", "gives 3 widths for 2 columns"),
    ],
)
def test_structural_mistakes_raise_with_their_line(markdown: str, message: str) -> None:
    if not markdown.startswith("## "):
        markdown = "## T\n\n" + markdown
    with pytest.raises(DocumentConversionError) as error:
        generate(markdown)
    assert message in error.value.reason


# ---------------------------------------------------------------------- comment box


def test_the_comment_box_is_a_speech_bubble_on_the_block_before_it() -> None:
    root = slides(generate("## T\n\nEin Satz.\n\n::: comment\nWichtig\n:::\n"))[0]
    bubble = shape_with(root, "Wichtig")
    assert find(bubble, "p:spPr/a:prstGeom")[0].get("prst") == "wedgeRectCallout"
    assert fill(bubble) == colors.WHITE
    line = find(bubble, "p:spPr/a:ln")[0]
    assert line.get("w") == "19050"
    stops = [s.get("val") for s in find(line, "a:gradFill/a:gsLst/a:gs/a:srgbClr")]
    assert stops == [colors.LIGHT_BLUE, colors.PTA_BLUE]
    r_pr = run_properties(root, "Wichtig")
    assert (r_pr.get("sz"), r_pr.get("b"), run_color(r_pr)) == ("1400", "1", colors.PTA_BLUE)
    body_pr = find(bubble, "p:txBody/a:bodyPr")[0]
    assert (body_pr.get("lIns"), body_pr.get("tIns")) == (str(design.cm(0.30)), "72000")
    x, y, w, _ = geometry(bubble)
    area = design.CONTENT_AREA
    assert x + w == area.right and w <= area.width // 2
    assert y == geometry(shape_with(root, "Ein Satz."))[1]
    adjust = {g.get("name"): g.get("fmla") for g in find(bubble, ".//a:gd")}
    assert adjust["adj1"] == "val -60000"
    assert int(str(adjust["adj2"]).split()[1]) > 50000  # the point below the bubble


# ---------------------------------------------------------------------- fitting


def test_a_long_flow_slide_shrinks_then_continues_with_its_kicker() -> None:
    rows = "".join(
        f"- **Begriff {n}** – eine Beschreibung, die etwas Platz braucht\n" for n in range(13)
    )
    small = PptxGenerator().generate(
        MarkdownDocument(f'## T {{kicker="K"}}\n\n::: rows\n{rows}:::\n'), io.BytesIO()
    )
    assert small.notes == ()
    shrunk = slides(generate(f'## T {{kicker="K"}}\n\n::: rows\n{rows}:::\n'))[0]
    assert (
        int(run_properties(shrunk, "eine Beschreibung, die etwas Platz braucht").get("sz", 0))
        < 1800
    )

    many = "".join(
        f"- **Begriff {n}** – eine Beschreibung, die etwas Platz braucht\n" for n in range(30)
    )
    markdown = f'## T {{kicker="K"}}\n\n::: rows\n{many}:::\n\n::: conclusion\nDas Fazit.\n:::\n'
    output = io.BytesIO()
    result = PptxGenerator().generate(MarkdownDocument(markdown), output)
    assert [n.code for n in result.notes] == [NoteCodes.SLIDE_SPLIT]
    parts = slides(output.getvalue())
    assert len(parts) >= 2
    titles = [text(find(r, "//p:sp[p:nvSpPr/p:nvPr/p:ph/@type='title']")[0]) for r in parts]
    assert titles[0] == "T" and all(t == "T (Forts.)" for t in titles[1:])
    assert all(any(text(s) == "K" for s in shapes(r)) for r in parts)
    with_conclusion = [any(text(s) == "Das Fazit." for s in shapes(r)) for r in parts]
    assert with_conclusion == [False] * (len(parts) - 1) + [True]
    bottom = design.CONCLUSION.area.top
    for root in parts:
        for line in find(root, "//p:cxnSp"):
            assert int(find(line, "p:spPr/a:xfrm/a:off")[0].get("y", 0)) < bottom
