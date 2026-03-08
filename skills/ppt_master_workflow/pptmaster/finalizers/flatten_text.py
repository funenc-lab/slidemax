"""Flatten text tspans inside a single SVG file."""

from __future__ import annotations

from pathlib import Path

from ..svg_processing.flatten_text import flatten_text_with_tspans
from xml.etree import ElementTree as ET


def run(svg_file: Path) -> int:
    """Flatten tspan structures and return 1 when a file changed."""

    tree = ET.parse(str(svg_file))
    changed = flatten_text_with_tspans(tree)
    if changed:
        tree.write(str(svg_file), encoding="unicode", xml_declaration=False)
        return 1
    return 0
