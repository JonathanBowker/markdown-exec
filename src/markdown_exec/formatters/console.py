"""Formatter for executing shell console code."""

from __future__ import annotations

import textwrap
from typing import Any
from uuid import uuid4

from markdown.core import Markdown

from markdown_exec.formatters.sh import _run_sh  # noqa: WPS450
from markdown_exec.rendering import add_source, markdown


def _format_console(  # noqa: WPS231
    code: str,
    md: Markdown,
    html: bool,
    source: str,
    tabs: tuple[str, str],
    **options: Any,
) -> str:
    markdown.setup(md)

    sh_lines = []
    for line in code.split("\n"):
        if line.startswith("$ "):
            sh_lines.append(line[2:])
    sh_code = "\n".join(sh_lines)

    extra = options.get("extra", {})
    output = _run_sh(sh_code, **extra)
    stash = {}
    if html:
        placeholder = str(uuid4())
        stash[placeholder] = output
        output = placeholder
    if source:
        source_code = textwrap.indent(sh_code, "$ ")
        output = add_source(source=source_code, location=source, output=output, language="console", tabs=tabs, **extra)
    return markdown.convert(output, stash=stash)
