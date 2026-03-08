"""Fix image aspect ratio issues for a single SVG file."""

from __future__ import annotations

from pathlib import Path

from ..svg_processing.image_aspect import fix_image_aspect_in_svg


def run(svg_file: Path) -> int:
    """Normalize stretched image aspect ratios."""

    return fix_image_aspect_in_svg(svg_file, dry_run=False, verbose=False)
