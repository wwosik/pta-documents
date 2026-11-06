"""Access to the embedded PTA templates (package data, prepared by ``run.sh prepare-templates``)."""

from __future__ import annotations

from importlib import resources

from pta_documents.design.variants import Language, SlidesVariant, WordVariant


def read(name: str) -> bytes:
    """The bytes of an embedded template file."""
    return (resources.files("pta_documents.design") / "templates" / name).read_bytes()


def word_template(variant: WordVariant) -> bytes:
    return read(variant.package_file)


def slides_template(variant: SlidesVariant, language: Language) -> bytes:
    return read(variant.package_file(language))


ENGLISH_LOGO = "slides-logo-en.png"
"""The English PTA logo of the English title slide; the layouts only carry the German one."""
