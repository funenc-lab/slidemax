"""Embed external image assets into a single SVG file."""

from __future__ import annotations

from pathlib import Path

from ..svg_processing.embed_images import embed_images_in_svg


def run(svg_file: Path) -> int:
    """Convert external image references into embedded data URIs."""

    embedded_count, _ = embed_images_in_svg(svg_file, dry_run=False)
    return embedded_count
