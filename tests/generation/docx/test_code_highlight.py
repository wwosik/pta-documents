"""E17-S02 in Word: typography and coloured code blocks."""

from __future__ import annotations

import io

from lxml import etree

from pta_documents.conversions.docx import DocxConverter
from pta_documents.conversions.options import ConversionOptions
from pta_documents.design import colors
from pta_documents.generation.common.openxml import W, w
from pta_documents.generation.common.result import NoteCodes
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.docx.writer import PTA_NAMESPACE
from pta_documents.markdown import MarkdownDocument
from pta_documents.markdown.typography import NBSP
from tests.generation.docx.conftest import generate, parts

NS = {"w": W, "pta": PTA_NAMESPACE}
HEAD = "---\ntitel: Bericht\n{extra}---\n# Kapitel\n\n"
PYTHON = '```python\ndef answer():\n    return 42  # "so"\n```\n'


def document(markdown: str, extra: str = "") -> etree._Element:
    return etree.fromstring(
        parts(generate(HEAD.format(extra=extra) + markdown))["word/document.xml"]
    )


def code_runs(root: etree._Element) -> list[etree._Element]:
    result = root.xpath("//w:p[w:pPr/w:pStyle/@w:val='Code']/w:r[w:t]", namespaces=NS)
    assert isinstance(result, list)
    return [r for r in result if isinstance(r, etree._Element)]


def look(run: etree._Element) -> tuple[str, str | None, bool, bool]:
    r_pr = run.find(w("rPr"))
    color = r_pr.find(w("color")) if r_pr is not None else None
    return (
        "".join(t.text or "" for t in run.iter(w("t"))),
        color.get(w("val")) if color is not None else None,
        r_pr is not None and r_pr.find(w("b")) is not None,
        r_pr is not None and r_pr.find(w("i")) is not None,
    )


def body_texts(root: etree._Element) -> list[str]:
    return ["".join(t.text or "" for t in p.iter(w("t"))) for p in root.iter(w("p"))]


def test_text_is_typeset_and_code_stays_as_written() -> None:
    root = document('"Zitat" - z. B. 10 % und `"code"`\n\n```\n"x" - 10 %\n```\n')
    texts = body_texts(root)
    assert f'„Zitat“ – z.{NBSP}B. 10{NBSP}% und "code"' in texts
    assert '"x" - 10 %' in texts


def test_typography_can_be_turned_off() -> None:
    root = document('"Zitat" - z. B. 10 %\n', extra="typografie: nein\n")
    assert '"Zitat" - z. B. 10 %' in body_texts(root)


def test_a_python_block_is_in_the_pta_colours() -> None:
    looks = [look(r) for r in code_runs(document(PYTHON))]
    assert ("def ", colors.PTA_BLUE, True, False) in looks
    assert ("42  ", colors.TEXT_SLIDES, False, False) in looks
    assert ('# "so"', colors.GREY_DARK, False, True) in looks
    assert ("answer():", None, False, False) in looks


def test_without_language_in_one_colour_without_a_note() -> None:
    output = io.BytesIO()
    result = DocxGenerator().generate(
        MarkdownDocument(HEAD.format(extra="") + "```\ndef answer(): pass\n```\n"), output
    )
    assert result.notes == ()
    root = etree.fromstring(parts(output.getvalue())["word/document.xml"])
    assert [look(r) for r in code_runs(root)] == [("def answer(): pass", None, False, False)]


def test_an_unknown_language_is_noted() -> None:
    output = io.BytesIO()
    markdown = HEAD.format(extra="") + "```klingonisch\nx\n```\n"
    result = DocxGenerator().generate(MarkdownDocument(markdown), output)
    assert result.codes() == [NoteCodes.CODE_LANGUAGE_UNKNOWN]
    assert result.notes[0].line == 6


def test_highlighting_can_be_turned_off() -> None:
    root = document(PYTHON, extra="syntaxhervorhebung: nein\n")
    assert all(look(r)[1] is None for r in code_runs(root))


def test_the_language_is_kept_for_the_converter() -> None:
    data = generate(HEAD.format(extra="") + PYTHON)
    document_xml = parts(data)["word/document.xml"].decode()
    root = etree.fromstring(document_xml.encode())
    assert root.xpath("//pta:codeLanguage/@pta:val", namespaces=NS) == ["python"]
    assert "pta" in str(
        root.get("{http://schemas.openxmlformats.org/markup-compatibility/2006}Ignorable")
    )
    markdown = DocxConverter().convert(data).text
    assert '```python\ndef answer():\n    return 42  # "so"\n```' in markdown


def test_plain_quotes_bring_the_written_text_back() -> None:
    data = generate(HEAD.format(extra="") + '"Zitat" - z. B. 10 % und geht\'s...\n')
    typeset = DocxConverter().convert(data).text
    assert "„Zitat“ – z." in typeset
    plain = DocxConverter().convert(data, ConversionOptions(plain_quotes=True)).text
    assert '"Zitat" - z. B. 10 % und geht\'s...' in plain
