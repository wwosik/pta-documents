"""What a PDF says about itself: title, author, language and creation time."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Final

from pta_documents.design.variants import Language

PRODUCER: Final = "PTA Documents"
"""``/Producer`` and ``pdf:Producer``; also ``/Creator`` and ``xmp:CreatorTool``."""

LANGUAGE_TAGS: Final = {Language.DE: "de-DE", Language.EN: "en"}
"""``/Lang`` of the catalog and ``dc:language`` per document language."""


@dataclass(frozen=True)
class PdfInfo:
    title: str | None
    author: str | None
    subject: str | None
    language: Language
    created: dt.datetime
    """Creation and modification time; naive values count as UTC."""

    @property
    def language_tag(self) -> str:
        return LANGUAGE_TAGS[self.language]

    @property
    def created_utc(self) -> dt.datetime:
        """``created`` in UTC, whole seconds."""
        created = self.created
        if created.tzinfo is None:
            created = created.replace(tzinfo=dt.UTC)
        return created.astimezone(dt.UTC).replace(microsecond=0)
