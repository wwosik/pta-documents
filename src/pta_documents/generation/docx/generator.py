"""Markdown to DOCX on the PTA Word templates."""

from __future__ import annotations

import copy
import datetime as dt
import io
from collections.abc import Iterator
from dataclasses import dataclass, replace
from typing import BinaryIO, Final

import docx
from docx.document import Document
from docx.opc.part import Part
from lxml import etree

from pta_documents.design import templates, word
from pta_documents.design.variants import TEXTS, GeneratedTexts, Language, WordVariant
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.openxml import (
    field_paragraph_runs,
    paragraph_text,
    remove,
    replace_in_paragraph,
    set_update_fields,
    w,
)
from pta_documents.generation.common.result import GenerationResult, Notes
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.docx.writer import BodyWriter, declare_own_namespace
from pta_documents.markdown.document import MarkdownDocument, MetadataKeys
from pta_documents.markdown.front_matter import FrontMatter, Keys

FORMAT: Final = DocumentFormat.DOCX
VALID_KEYS: Final = (
    Keys.TEMPLATE,
    Keys.TITLE,
    Keys.SUBTITLE,
    Keys.AUTHOR,
    Keys.LOCATION,
    Keys.DATE,
    Keys.COMPANY,
    Keys.LANGUAGE,
    Keys.TYPOGRAPHY,
    Keys.HIGHLIGHT,
    Keys.CHECK,
    Keys.TOC,
)
TEMPLATE_COMPANY: Final = "PTA IT-Beratung"
HEADER_CONTENT_TYPE: Final = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"
)
FOOTER_CONTENT_TYPE: Final = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"
)


@dataclass(frozen=True)
class DocumentInfo:
    """What the front matter (or the metadata) says about the document."""

    title: str | None
    subtitle: str | None
    author: str | None
    location: str | None
    date: dt.date | None


class DocxGenerator:
    def generate(
        self,
        document: MarkdownDocument,
        output: BinaryIO,
        options: DocxOptions | None = None,
    ) -> GenerationResult:
        """Write ``document`` as a DOCX to ``output``.

        Returns the notes on what had to be worked around (HTML left out, …), see
        ``GenerationResult``; ``pages`` stays None, as Word counts pages only when it lays the
        document out. Raises ``DocumentConversionError`` for mistakes in the Markdown or its
        front matter.
        """
        notes = Notes()
        front = FrontMatter.read(document.text, FORMAT)
        front.check_keys(VALID_KEYS, allow_status=True)
        front.status_labels()  # raises for an unknown category or a label in two
        options = apply_front_matter(front, options or DocxOptions())
        info = DocumentInfo(
            title=front.get(Keys.TITLE) or document.metadata.get(MetadataKeys.TITLE),
            subtitle=front.get(Keys.SUBTITLE),
            author=front.get(Keys.AUTHOR) or document.metadata.get(MetadataKeys.AUTHOR),
            location=front.get(Keys.LOCATION),
            date=options.date,
        )
        texts = TEXTS[options.language]
        if options.variant.has_cover and not info.title:
            raise DocumentConversionError(
                FORMAT,
                f"The template '{options.variant.value}' has a cover page and needs a title: "
                f"add '{Keys.TITLE}: …' to the front matter.",
            )

        result = docx.Document(io.BytesIO(templates.word_template(options.variant)))
        borrow_styles(result)
        if options.variant.has_cover:
            write_cover(result, info)
        if options.toc:
            write_toc(result, texts)
        BodyWriter(result, document, front, options, texts, notes).write()
        declare_own_namespace(result)
        fill_headers_and_footers(result, info, options, texts)
        set_properties(result, info)
        if options.toc:
            set_update_fields(result.settings.element)
        result.save(output)
        return GenerationResult(notes.to_tuple())


def apply_front_matter(front: FrontMatter, options: DocxOptions) -> DocxOptions:
    if (value := front.get(Keys.TEMPLATE)) is not None:
        options = replace(options, variant=WordVariant.parse(value))
    if (value := front.get(Keys.LANGUAGE)) is not None:
        options = replace(options, language=Language.parse(value, FORMAT))
    if (value := front.boolean(Keys.TYPOGRAPHY)) is not None:
        options = replace(options, typography=value)
    if (value := front.boolean(Keys.HIGHLIGHT)) is not None:
        options = replace(options, highlight=value)
    if (value := front.date()) is not None:
        options = replace(options, date=value)
    if (value := front.get(Keys.COMPANY)) is not None:
        options = replace(options, company=value)
    if (value := front.boolean(Keys.TOC)) is not None:
        options = replace(options, toc=value)
    return options


def format_date(date: dt.date) -> str:
    return date.strftime("%d.%m.%Y")


def borrow_styles(document: Document) -> None:
    """Copy styles missing from the template (landscape ones) from the portrait template."""
    styles = document.styles.element
    names = {s.get(w("val")) for s in styles.iterfind(f"{w('style')}/{w('name')}")}
    missing = [n for n in word.BORROWED_STYLES if n not in names]
    if not missing:
        return
    portrait = docx.Document(io.BytesIO(templates.word_template(WordVariant.PORTRAIT)))
    for style in portrait.styles.element.iterfind(w("style")):
        name = style.find(w("name"))
        if name is not None and name.get(w("val")) in missing:
            styles.append(copy.deepcopy(style))


def page_break(document: Document) -> None:
    paragraph = document.add_paragraph()
    etree.SubElement(etree.SubElement(paragraph._p, w("r")), w("br")).set(w("type"), "page")


def write_cover(document: Document, info: DocumentInfo) -> None:
    s = word.STYLES
    assert info.title is not None
    document.add_paragraph(info.title, style=s.title)
    if info.subtitle:
        document.add_paragraph(info.subtitle, style=s.subtitle)
    byline = ", ".join(
        part
        for part in (info.author, info.location, format_date(info.date) if info.date else None)
        if part
    )
    if byline:
        document.add_paragraph(byline, style=s.author)
    page_break(document)


def write_toc(document: Document, texts: GeneratedTexts) -> None:
    document.add_paragraph(texts.contents, style=word.STYLES.sub_heading)
    paragraph = document.add_paragraph(style=word.STYLES.toc[0])
    for run in field_paragraph_runs(word.TOC_FIELD):
        paragraph._p.append(run)
    page_break(document)


def header_and_footer_parts(document: Document) -> Iterator[Part]:
    package = document.part.package
    assert package is not None
    for part in package.iter_parts():
        if part.content_type in (HEADER_CONTENT_TYPE, FOOTER_CONTENT_TYPE):
            yield part


def fill_headers_and_footers(
    document: Document, info: DocumentInfo, options: DocxOptions, texts: GeneratedTexts
) -> None:
    date = format_date(options.date or dt.date.today())
    for part in header_and_footer_parts(document):
        root: etree._Element = part.element  # type: ignore[attr-defined]
        for paragraph in list(root.iter(w("p"))):
            content = paragraph_text(paragraph)
            instructions = "".join(i.text or "" for i in paragraph.iter(w("instrText")))
            if word.SUBTITLE_PLACEHOLDER in content or "STYLEREF  Untertitel" in instructions:
                if info.subtitle:
                    replace_in_paragraph(paragraph, word.SUBTITLE_PLACEHOLDER, info.subtitle)
                else:
                    # A STYLEREF to a missing style shows an error text in Word.
                    remove(paragraph)
                continue
            replace_in_paragraph(paragraph, word.TITLE_PLACEHOLDER, info.title or "")
            replace_in_paragraph(paragraph, word.DATE_PLACEHOLDER, date)
            if options.language is not Language.DE:
                replace_in_paragraph(paragraph, word.AS_OF_LABEL, texts.as_of + ":")
                replace_in_paragraph(paragraph, word.PAGE_LABEL + " ", texts.page + " ")
            if options.company:
                replace_in_paragraph(paragraph, TEMPLATE_COMPANY, options.company)


def set_properties(document: Document, info: DocumentInfo) -> None:
    properties = document.core_properties
    now = dt.datetime.now(dt.UTC).replace(microsecond=0)
    properties.title = info.title or ""
    properties.subject = info.subtitle or ""
    properties.author = info.author or ""
    properties.last_modified_by = info.author or ""
    properties.created = now
    properties.modified = now
    properties.revision = 1
