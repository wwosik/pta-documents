import zipfile
from pathlib import Path

import pta_documents
from pta_documents import DocumentConversionError, DocumentFormat
from pta_documents.design import fonts, logos
from tests.conftest import REPO_ROOT


def test_version_is_set() -> None:
    assert pta_documents.__version__


def test_error_carries_format_and_reason() -> None:
    error = DocumentConversionError(DocumentFormat.DOCX, "broken")
    assert error.format is DocumentFormat.DOCX
    assert error.reason == "broken"
    assert str(error) == "docx: broken"


def test_the_wheel_carries_the_fonts_and_their_licences(tmp_path: Path) -> None:
    from hatchling.builders.wheel import WheelBuilder

    (wheel,) = WheelBuilder(str(REPO_ROOT)).build(directory=str(tmp_path), versions=["standard"])
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    prefix = "pta_documents/design/fonts/"
    for name in (*fonts.BUNDLED_FILES, *fonts.LICENCE_FILES, "__init__.py", "truetype.py"):
        assert prefix + name in names


def test_the_wheel_carries_the_logos(tmp_path: Path) -> None:
    from hatchling.builders.wheel import WheelBuilder

    (wheel,) = WheelBuilder(str(REPO_ROOT)).build(directory=str(tmp_path), versions=["standard"])
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    for logo in logos.Logo:
        for suffix in (".svg", ".png"):
            assert f"pta_documents/design/logos/{logo.stem}{suffix}" in names
