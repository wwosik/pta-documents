"""The tool ``make_document`` for AI hosts (E08-S04): the generators as one tool with a JSON
Schema, a guide and a fixed reply, without any AI SDK.

Usage::

    tool = ToolOptions(docx=DocxOptions(), pptx=PptxOptions())
    description = describe(tool)  # name, description, parameters_schema, guide
    try:
        made = run(arguments, output, tool)
        answer = reply(made, link)
    except (DocumentConversionError, ValueError) as error:
        answer = reply(error)
"""

from pta_documents.tool.options import DEFAULT_NAME, ToolOptions
from pta_documents.tool.tool import (
    ToolArgumentError,
    ToolDescription,
    ToolRun,
    describe,
    reply,
    run,
    schema,
)

__all__ = [
    "DEFAULT_NAME",
    "ToolArgumentError",
    "ToolDescription",
    "ToolOptions",
    "ToolRun",
    "describe",
    "reply",
    "run",
    "schema",
]
