"""Markdown to PDF/A-2b in the PTA design (extra ``pdf``: reportlab, pikepdf).

Importing this package without the extra raises an ``ImportError`` that names it.
"""

from __future__ import annotations

from typing import Final

EXTRA_MISSING: Final = (
    "The PDF generator needs the optional extra 'pdf' (reportlab, pikepdf): "
    "pip install -e '.[pdf]'."
)

try:
    import pikepdf  # noqa: F401  # pyright: ignore[reportUnusedImport]
    import reportlab  # noqa: F401  # pyright: ignore[reportUnusedImport]
except ImportError as error:  # pragma: no cover - the test environment has the extra
    raise ImportError(EXTRA_MISSING) from error

from pta_documents.generation.pdf.generator import PdfGenerator  # noqa: E402
from pta_documents.generation.pdf.options import PdfOptions  # noqa: E402

__all__ = ["EXTRA_MISSING", "PdfGenerator", "PdfOptions"]
