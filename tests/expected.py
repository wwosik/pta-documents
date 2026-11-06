"""Snapshot comparison with ``*.expected.md`` files (renew with PTA_DOCUMENTS_UPDATE_EXPECTED=1)."""

from __future__ import annotations

import os
import re
from pathlib import Path

from pta_documents.markdown import MarkdownDocument

UPDATE_VARIABLE = "PTA_DOCUMENTS_UPDATE_EXPECTED"


def assert_matches_expected(expected: Path, actual: str) -> None:
    if os.environ.get(UPDATE_VARIABLE) == "1":
        expected.write_text(actual, encoding="utf-8", newline="\n")
        return
    assert expected.exists(), f"{expected.name} is missing; run with {UPDATE_VARIABLE}=1"
    assert actual == expected.read_text(encoding="utf-8").replace("\r\n", "\n")


_IMAGE = re.compile(r"!\[[^\]]*\]\(<?([^)>]+)>?\)")


def assert_resources_match_references(document: MarkdownDocument) -> None:
    referenced = sorted(set(_IMAGE.findall(document.text)))
    assert referenced == sorted(r.path for r in document.resources)
