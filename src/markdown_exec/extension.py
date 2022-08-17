"""This module contains a Markdown extension allowing to integrate generated headings into the ToC."""

from __future__ import annotations
import re
from collections import ChainMap
from typing import Any, MutableSequence, Tuple
from warnings import warn
from xml.etree.ElementTree import Element
from markupsafe import Markup

import yaml
from jinja2.exceptions import TemplateNotFound
from markdown import Markdown
from markdown.blockparser import BlockParser
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from mkdocs_autorefs.plugin import AutorefsPlugin

from mkdocstrings.handlers.base import BaseHandler, CollectionError, CollectorItem, Handlers
from mkdocstrings.loggers import get_logger

try:
    from mkdocs.exceptions import PluginError  # New in MkDocs 1.2
except ImportError:
    PluginError = SystemExit  # noqa: WPS440


log = get_logger(__name__)


class InsertHeadings(Treeprocessor):
    """Our headings insertor."""

    name = "markdown_exec_insert_headings"

    def __init__(self, md: Markdown):
        """Initialize the object.

        Arguments:
            md: A `markdown.Markdown` instance.
        """
        super().__init__(md)
        self.headings: dict[Markup, list[Element]] = {}

    def run(self, root: Element):  # noqa: D102 (ignore missing docstring)
        if not self.headings:
            return

        for el in root.iter():
            if el.text in self.md.stash:
                div = Element("div", {"class": "markdown-exec"})
                div.extend(self.headings[self.md.stash[el.text]])
                el.append(div)


class RemoveHeadings(Treeprocessor):
    """Our headings remover."""

    name = "markdown_exec_remove_headings"

    def run(self, root: Element):
        carry_text = ""
        for el in reversed(root):  # Reversed mainly for the ability to mutate during iteration.
            if el.tag == "div" and el.get("class") == "markdown-exec":
                # Delete the duplicated headings along with their container, but keep the text (i.e. the actual HTML).
                carry_text = (el.text or "") + carry_text
                root.remove(el)
            elif carry_text:
                el.tail = (el.tail or "") + carry_text
                carry_text = ""
        if carry_text:
            root.text = (root.text or "") + carry_text


class MarkdownExecExtension(Extension):
    """Our Markdown extension."""

    def extendMarkdown(self, md: Markdown) -> None:  # noqa: N802 (casing: parent method's name)
        """Register the extension.

        Add instances of our tree processors to handle headings.

        Arguments:
            md: A `markdown.Markdown` instance.
        """
        md.treeprocessors.register(
            InsertHeadings(md),
            InsertHeadings.name,
            priority=3,  # Right before toc
        )
        md.treeprocessors.register(
            RemoveHeadings(md),
            RemoveHeadings.name,
            priority=4,  # Right after toc.
        )
