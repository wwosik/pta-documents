"""The Markdown document model shared by converters and generators.

Public modules besides the names below: ``text``, the helpers for writing Markdown safely
(``escape``, ``escape_line_start``, ``code``, ``destination``, ``cell``, ``table``, ``compact``,
``normalize``), imported as ``from pta_documents.markdown import text as md``.
"""

from pta_documents.markdown.document import (
    DocumentResource,
    MarkdownDocument,
    MetadataKeys,
    content_type_of,
)
from pta_documents.markdown.front_matter import FrontMatter, Keys

__all__ = [
    "DocumentResource",
    "FrontMatter",
    "Keys",
    "MarkdownDocument",
    "MetadataKeys",
    "content_type_of",
]
