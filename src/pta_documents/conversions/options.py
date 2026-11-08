"""Options of the converters to Markdown and the collector of extracted images."""

from __future__ import annotations

import hashlib
import posixpath
from dataclasses import dataclass, field

from pta_documents.markdown.document import DocumentResource, content_type_of


@dataclass(frozen=True)
class ConversionOptions:
    resource_path_prefix: str = "images/"
    """Prefix of the paths of extracted images, e.g. ``images/image1.png``."""
    include_images: bool = True
    """Extract images as resources and reference them; without, images are left out."""
    file_name: str | None = None
    """The original file name, for format detection by extension."""
    notes: bool = True
    """PPTX: the speaker notes of each slide after it, as ``::: notes`` … ``:::``; without,
    only the slides' content."""
    plain_quotes: bool = False
    """Typographic characters back to straight ones outside code — „“ → ", ‚‘’ → ', – → -,
    … → ..., non-breaking spaces → spaces — so that Markdown the generators typeset
    (``typografie: ja``) comes back as it was written (E17-S02)."""


@dataclass
class ResourceCollector:
    """Collects extracted images: identical content is stored once, names stay unique."""

    prefix: str
    resources: list[DocumentResource] = field(default_factory=lambda: list[DocumentResource]())
    _paths_by_hash: dict[str, str] = field(default_factory=lambda: dict[str, str]())
    _paths: set[str] = field(default_factory=lambda: set[str]())

    def add(self, file_name: str, content: bytes) -> str:
        digest = hashlib.sha256(content).hexdigest()
        if digest in self._paths_by_hash:
            return self._paths_by_hash[digest]
        path = self.prefix + file_name
        stem, extension = posixpath.splitext(file_name)
        n = 2
        while path.lower() in self._paths:
            path = f"{self.prefix}{stem}-{n}{extension}"
            n += 1
        self._paths.add(path.lower())
        self._paths_by_hash[digest] = path
        self.resources.append(DocumentResource(path, content_type_of(file_name), content))
        return path
