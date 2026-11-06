"""Prepare the embedded PTA templates from source-templates/.

Strips SharePoint metadata, trash parts, sample slides and sample text and person names, and
writes the result to src/pta_documents/design/templates/ deterministically: running it again
without a template change produces identical bytes.

usage: ./run.sh prepare-templates [--check]
  --check  only compare; exit 1 if the embedded templates are out of date
"""

from __future__ import annotations

import io
import posixpath
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from pta_documents.design.variants import SLIDES_SOURCES, WordVariant

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "source-templates"
TARGET = REPO / "src" / "pta_documents" / "design" / "templates"

CT = "http://schemas.openxmlformats.org/package/2006/content-types"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
EP = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
REL_TYPES = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"

ZIP_DATE = (2000, 1, 1, 0, 0, 0)
DROPPED_REL_TYPES = {
    REL_TYPES + "customXml",
    REL_TYPES + "custom-properties",
    "http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail",
    REL_TYPES + "commentAuthors",
    REL_TYPES + "slide",
    REL_TYPES + "attachedTemplate",
}

CORE = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/'
    'core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title></dc:title>'
    "<dc:creator></dc:creator><cp:lastModifiedBy></cp:lastModifiedBy><cp:revision>1</cp:revision>"
    '<dcterms:created xsi:type="dcterms:W3CDTF">2000-01-01T00:00:00Z</dcterms:created>'
    '<dcterms:modified xsi:type="dcterms:W3CDTF">2000-01-01T00:00:00Z</dcterms:modified>'
    "</cp:coreProperties>"
)


def app_xml(application: str, company: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<Properties xmlns="{EP}" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        f"<Application>{application}</Application><DocSecurity>0</DocSecurity>"
        f"<Company>{company}</Company></Properties>"
    )


@dataclass
class Package:
    """An OPC package in memory: part name (without leading slash) -> bytes."""

    parts: dict[str, bytes]
    order: list[str] = field(default_factory=lambda: list[str]())

    @classmethod
    def read(cls, path: Path) -> Package:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            return cls({n: z.read(n) for n in names}, names)

    def xml(self, name: str) -> etree._Element:
        return etree.fromstring(self.parts[name])

    def put_xml(self, name: str, root: etree._Element) -> None:
        self.parts[name] = etree.tostring(
            root, xml_declaration=True, encoding="UTF-8", standalone=True
        )

    def remove(self, name: str) -> None:
        self.parts.pop(name, None)
        self.parts.pop(rels_name(name), None)

    def write(self) -> bytes:
        buffer = io.BytesIO()
        names = [n for n in self.order if n in self.parts]
        names += sorted(n for n in self.parts if n not in names)
        # [Content_Types].xml first, as Office writes it.
        names.sort(key=lambda n: n != "[Content_Types].xml")
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
            for name in names:
                info = zipfile.ZipInfo(name, ZIP_DATE)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, self.parts[name])
        return buffer.getvalue()


def rels_name(part: str) -> str:
    directory, file = posixpath.split(part)
    return posixpath.join(directory, "_rels", file + ".rels")


def rel_target(source: str, target: str) -> str:
    if target.startswith("/"):
        return target[1:]
    base = posixpath.dirname(source)
    return posixpath.normpath(posixpath.join(base, target))


def owner_of_rels(name: str) -> str:
    directory, file = posixpath.split(name)
    return posixpath.join(posixpath.dirname(directory), file[: -len(".rels")])


def drop_relationships(package: Package) -> None:
    """Remove relationships of dropped types from every .rels part."""
    for name in [n for n in package.parts if n.endswith(".rels")]:
        root = package.xml(name)
        changed = False
        for rel in list(root):
            if rel.get("Type") in DROPPED_REL_TYPES:
                root.remove(rel)
                changed = True
        if changed:
            package.put_xml(name, root)


def collect_garbage(package: Package) -> None:
    """Delete every part no relationship reaches from the package root."""
    reachable: set[str] = set()
    pending = [""]
    while pending:
        part = pending.pop()
        rels = "_rels/.rels" if part == "" else rels_name(part)
        if rels not in package.parts:
            continue
        for rel in package.xml(rels):
            if rel.get("TargetMode") == "External":
                continue
            target = rel_target(part if part else "x", str(rel.get("Target")))
            if part == "":
                target = str(rel.get("Target")).lstrip("/")
            if target not in reachable and target in package.parts:
                reachable.add(target)
                pending.append(target)
    for name in list(package.parts):
        if name == "[Content_Types].xml" or name == "_rels/.rels":
            continue
        if name.endswith(".rels"):
            if owner_of_rels(name) not in reachable:
                del package.parts[name]
            continue
        if name not in reachable:
            del package.parts[name]
    fix_content_types(package)


def fix_content_types(package: Package, main: tuple[str, str] | None = None) -> None:
    root = package.xml("[Content_Types].xml")
    for override in list(root.iterfind(f"{{{CT}}}Override")):
        part = str(override.get("PartName")).lstrip("/")
        if part not in package.parts:
            root.remove(override)
        elif main and part == main[0]:
            override.set("ContentType", main[1])
    extensions = {posixpath.splitext(n)[1][1:].lower() for n in package.parts}
    for default in list(root.iterfind(f"{{{CT}}}Default")):
        if str(default.get("Extension")).lower() not in extensions:
            root.remove(default)
    package.put_xml("[Content_Types].xml", root)


def prepare_word(source: Path) -> bytes:
    package = Package.read(source)
    drop_relationships(package)
    document = package.xml("word/document.xml")
    body = document.find(f"{{{W}}}body")
    assert body is not None
    for child in list(body):
        if child.tag != f"{{{W}}}sectPr":
            body.remove(child)
    package.put_xml("word/document.xml", document)
    package.parts["docProps/core.xml"] = CORE.encode()
    package.parts["docProps/app.xml"] = app_xml("Microsoft Office Word", "PTA GmbH").encode()
    collect_garbage(package)
    fix_content_types(
        package,
        (
            "word/document.xml",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
        ),
    )
    return package.write()


def prepare_slides(source: Path) -> tuple[bytes, list[tuple[str, bytes]]]:
    """Returns the template and the pictures placed on its sample slides (by part name)."""
    package = Package.read(source)
    pictures = slide_pictures(package)
    drop_relationships(package)
    presentation = package.xml("ppt/presentation.xml")
    for tag in ("sldIdLst", "custShowLst"):
        element = presentation.find(f"{{{P}}}{tag}")
        if element is not None:
            presentation.remove(element)
    ext_list = presentation.find(f"{{{P}}}extLst")
    if ext_list is not None:
        for ext in list(ext_list):
            # Sections list slide ids that no longer exist.
            if any(etree.QName(c).localname == "sectionLst" for c in ext):
                ext_list.remove(ext)
        if len(ext_list) == 0:
            presentation.remove(ext_list)
    package.put_xml("ppt/presentation.xml", presentation)
    package.parts["docProps/core.xml"] = CORE.encode()
    package.parts["docProps/app.xml"] = app_xml(
        "Microsoft Office PowerPoint", "PTA Unternehmensberatung"
    ).encode()
    collect_garbage(package)
    fix_content_types(
        package,
        (
            "ppt/presentation.xml",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml",
        ),
    )
    return package.write(), pictures


def slide_pictures(package: Package) -> list[tuple[str, bytes]]:
    """Pictures placed directly on the slides (not inherited from layouts)."""
    result: list[tuple[str, bytes]] = []
    for name in sorted(
        n for n in package.parts if n.startswith("ppt/slides/slide") and n.endswith(".xml")
    ):
        rels = rels_name(name)
        if rels not in package.parts:
            continue
        targets = {
            str(rel.get("Id")): rel_target(name, str(rel.get("Target")))
            for rel in package.xml(rels)
        }
        for blip in package.xml(name).iterfind(f".//{{{P}}}pic//{{{A}}}blip"):
            target = targets.get(str(blip.get(f"{{{R}}}embed")))
            if target and target in package.parts:
                result.append((target, package.parts[target]))
    return result


def build() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for variant in WordVariant:
        files[variant.package_file] = prepare_word(SOURCE / variant.source_file)
    for package_file, source in SLIDES_SOURCES.items():
        data, pictures = prepare_slides(SOURCE / source)
        files[package_file] = data
        if package_file == "slides-basis-en.pptx":
            # The English logo is only on the sample title slide; keep it for the generator.
            ((_, logo),) = [p for p in pictures if p[0].endswith(".png")]
            files["slides-logo-en.png"] = logo
    return files


def main(argv: list[str]) -> int:
    check = "--check" in argv
    files = build()
    stale = [
        name
        for name, data in files.items()
        if not (TARGET / name).exists() or (TARGET / name).read_bytes() != data
    ]
    extra = (
        sorted(p.name for p in TARGET.glob("*") if p.is_file() and p.name not in files)
        if TARGET.exists()
        else []
    )
    if check:
        for name in stale + extra:
            print(f"out of date: {name}")
        return 1 if stale or extra else 0
    TARGET.mkdir(parents=True, exist_ok=True)
    for name in stale:
        (TARGET / name).write_bytes(files[name])
        print(f"wrote {name} ({len(files[name]) // 1024} KB)")
    for name in extra:
        (TARGET / name).unlink()
        print(f"removed {name}")
    if not stale and not extra:
        print("templates are up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
