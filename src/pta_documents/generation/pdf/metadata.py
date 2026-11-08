"""What a PDF says about itself: title, author, language and creation time."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Final

from pta_documents.design.variants import Language

PRODUCER: Final = "PTA Documents"
"""``/Producer`` and ``pdf:Producer``; also ``/Creator`` and ``xmp:CreatorTool``."""

LANGUAGE_TAGS: Final = {Language.DE: "de-DE", Language.EN: "en"}
"""``/Lang`` of the catalog and ``dc:language`` per document language."""


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


@dataclass(frozen=True)
class PdfInfo:
    """The document information of a PDF: reportlab writes it (``layout.render``), the PDF/A
    pass writes it again with the XMP (``pdfa.to_pdfa``)."""

    title: str | None = None
    author: str | None = None
    subject: str | None = None
    language: Language = Language.DE
    created: dt.datetime = field(default_factory=_now)
    """Creation and modification time; naive values count as UTC. The generator sets it from
    ``PdfOptions.created``."""

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
