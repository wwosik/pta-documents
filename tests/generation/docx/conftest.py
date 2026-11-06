from __future__ import annotations

import io
import zipfile

import docx
from docx.document import Document
from docx.text.paragraph import Paragraph

from pta_documents.generation.common.openxml import W
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.markdown import DocumentResource, MarkdownDocument


def generate(
    markdown: str,
    options: DocxOptions | None = None,
    resources: tuple[DocumentResource, ...] = (),
) -> bytes:
    output = io.BytesIO()
    DocxGenerator().generate(MarkdownDocument(markdown, resources), output, options)
    return output.getvalue()


def open_docx(data: bytes) -> Document:
    return docx.Document(io.BytesIO(data))


def parts(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return {n: z.read(n) for n in z.namelist()}


def all_text(data: bytes) -> str:
    """The text of every XML part (body, headers, footers, properties)."""
    return "\n".join(
        content.decode("utf-8") for name, content in parts(data).items() if name.endswith(".xml")
    )


def style_name(paragraph: Paragraph) -> str:
    """The style name as stored in styles.xml (python-docx shows UI names like "Heading 1")."""
    style = paragraph.style
    if style is None:
        return ""
    name = style.element.find(f"{{{W}}}name")
    return str(name.get(f"{{{W}}}val")) if name is not None else ""
