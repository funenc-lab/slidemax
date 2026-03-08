"""Convert rounded rectangles to paths for a single SVG file."""

from __future__ import annotations

from pathlib import Path

from ..svg_processing.rounded_rects import process_svg


def run(svg_file: Path) -> int:
    """Convert rounded rectangles into path elements."""

    content = svg_file.read_text(encoding="utf-8")
    processed, count = process_svg(content, verbose=False)
    if count > 0:
        svg_file.write_text(processed, encoding="utf-8")
    return count
