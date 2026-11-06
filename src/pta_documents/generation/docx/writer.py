"""Writes the Markdown body into the document, block by block, in PTA styles."""

from __future__ import annotations

from docx.document import Document
from markdown_it.token import Token

from pta_documents.design import word
from pta_documents.design.variants import GeneratedTexts
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.markdown.document import MarkdownDocument
from pta_documents.markdown.front_matter import FrontMatter
from pta_documents.markdown.parser import parse


class BodyWriter:
    def __init__(
        self,
        document: Document,
        source: MarkdownDocument,
        front: FrontMatter,
        options: DocxOptions,
        texts: GeneratedTexts,
    ) -> None:
        self.document = document
        self.source = source
        self.front = front
        self.options = options
        self.texts = texts

    def write(self) -> None:
        tokens = parse(self.front.body)
        i = 0
        while i < len(tokens):
            i = self.block(tokens, i)

    def block(self, tokens: list[Token], i: int) -> int:
        token = tokens[i]
        if token.type == "heading_open":
            level = int(token.tag[1])
            text = tokens[i + 1].content
            styles = word.STYLES
            style = styles.headings[level - 1] if level <= 3 else styles.sub_heading
            self.document.add_paragraph(text, style=style)
            return i + 3
        if token.type == "paragraph_open":
            self.document.add_paragraph(tokens[i + 1].content, style=word.STYLES.normal)
            return i + 3
        return i + 1
