"""Sanitize a single SVG file for SlideMax compatibility."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from ..svg_processing.sanitize import sanitize_tree


def run(svg_file: Path) -> int:
    """Remove editor metadata and normalize common compatibility issues."""

    tree = ET.parse(str(svg_file))
    changes = sanitize_tree(tree)
    if changes > 0:
        if hasattr(ET, "indent"):
            ET.indent(tree, space="  ")
        tree.write(str(svg_file), encoding="unicode", xml_declaration=False)
    return changes
