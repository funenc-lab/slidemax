"""Crop image fills for a single SVG file."""

from __future__ import annotations

from pathlib import Path

from ..svg_processing.crop_images import process_svg_images


def run(svg_file: Path) -> int:
    """Crop slice-based images and return the processed count."""

    cropped_count, _ = process_svg_images(svg_file, dry_run=False, verbose=False)
    return cropped_count
