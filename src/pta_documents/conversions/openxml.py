"""Reading Office Open XML packages for the converters."""

from __future__ import annotations

import io
import posixpath
import zipfile
from collections.abc import Callable
from typing import BinaryIO, Final

from lxml import etree

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.markdown.document import MetadataKeys

CORE_PROPERTIES: Final = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DUBLIN_CORE: Final = "http://purl.org/dc/elements/1.1/"

_PARSER: Final = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)


def read_input(data: bytes | BinaryIO) -> bytes:
    return data if isinstance(data, bytes) else data.read()


class OpenXmlPackage:
    def __init__(self, data: bytes) -> None:
        self._zip = zipfile.ZipFile(io.BytesIO(data))

    def read_xml(self, part: str) -> etree._Element | None:
        content = self.read_bytes(part)
        return None if content is None else etree.fromstring(content, _PARSER)

    def read_bytes(self, part: str) -> bytes | None:
        try:
            return self._zip.read(part)
        except KeyError:
            return None

    def relationships(self, part: str) -> dict[str, str]:
        """Relationship id -> target part (resolved) or external URL."""
        folder, name = posixpath.split(part)
        rels = self.read_xml(posixpath.join(folder, "_rels", name + ".rels"))
        result: dict[str, str] = {}
        if rels is None:
            return result
        for rel in rels:
            rel_id, target = rel.get("Id"), rel.get("Target")
            if rel_id is None or target is None:
                continue
            if (rel.get("TargetMode") or "").lower() == "external":
                result[rel_id] = target
            else:
                result[rel_id] = resolve(folder, target)
        return result

    def add_core_properties(self, metadata: dict[str, str]) -> None:
        core = self.read_xml("docProps/core.xml")
        if core is None or core.tag != f"{{{CORE_PROPERTIES}}}coreProperties":
            return
        for key, tag in ((MetadataKeys.TITLE, "title"), (MetadataKeys.AUTHOR, "creator")):
            element = core.find(f"{{{DUBLIN_CORE}}}{tag}")
            if element is not None and (element.text or "").strip():
                metadata[key] = (element.text or "").strip()

    def close(self) -> None:
        self._zip.close()


def resolve(folder: str, target: str) -> str:
    if target.startswith("/"):
        return target[1:]
    parts = [p for p in folder.split("/") if p]
    for segment in target.split("/"):
        if segment == "..":
            if parts:
                parts.pop()
        elif segment not in (".", ""):
            parts.append(segment)
    return "/".join(parts)


def guard[T](format: DocumentFormat, convert: Callable[[], T]) -> T:
    """Turn the errors of a damaged package into ``DocumentConversionError``."""
    try:
        return convert()
    except (zipfile.BadZipFile, etree.XMLSyntaxError, OSError, EOFError) as error:
        raise DocumentConversionError(format, f"The package is damaged: {error}") from error
