"""Diagrams from code blocks (E06-S03): ``mermaid`` blocks drawn locally by mermaid-cli.

``MermaidRenderer`` needs Node.js and mermaid-cli (``./run.sh setup`` installs it repo-locally
when Node.js is there) and ``cssselect`` (extra ``diagrams``); without mermaid-cli the
generators leave the blocks as code with a ``code-not-drawn`` note.
"""

from pta_documents.diagrams.mermaid import (
    SUPPORTED,
    MermaidErrorMode,
    MermaidRenderer,
    find_command,
)

__all__ = ["SUPPORTED", "MermaidErrorMode", "MermaidRenderer", "find_command"]
