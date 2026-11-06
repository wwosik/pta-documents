"""A Markdown document with the binary resources (images) it references."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final
from urllib.parse import unquote


@dataclass(frozen=True)
class DocumentResource:
    """A file the Markdown references by ``path``, e.g. ``images/figure-1.png``."""

    path: str
    content_type: str
    content: bytes


def _no_metadata() -> Mapping[str, str]:
    return MappingProxyType({})


@dataclass(frozen=True)
class MarkdownDocument:
    """Markdown text, its resources and metadata (``MetadataKeys``).

    Converters produce it; generators consume it. Images never come from the file system, only
    from ``resources``.
    """

    text: str
    resources: Sequence[DocumentResource] = ()
    metadata: Mapping[str, str] = field(default_factory=_no_metadata)

    def find_resource(self, reference: str) -> DocumentResource | None:
        """The resource a Markdown link points to; ``./``, ``\\`` and %-escapes do not matter."""
        wanted = _normalize(reference)
        return next((r for r in self.resources if _normalize(r.path) == wanted), None)


def _normalize(path: str) -> str:
    normalized = unquote(path.strip()).replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


class MetadataKeys:
    """Keys of ``MarkdownDocument.metadata``."""

    TITLE: Final = "title"
    AUTHOR: Final = "author"
    PAGE_COUNT: Final = "pageCount"
    SLIDE_COUNT: Final = "slideCount"
    SKIPPED_IMAGES: Final = "skippedImages"


CONTENT_TYPES: Final = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".jpe": "image/jpeg",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".emf": "image/x-emf",
    ".wmf": "image/x-wmf",
}


def content_type_of(file_name: str) -> str:
    """The MIME type of an image file name; ``application/octet-stream`` if unknown."""
    dot = file_name.rfind(".")
    extension = file_name[dot:].lower() if dot >= 0 else ""
    return CONTENT_TYPES.get(extension, "application/octet-stream")
