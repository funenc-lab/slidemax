"""Embed icon placeholders into a single SVG file."""

from __future__ import annotations

from pathlib import Path

from ..svg_processing.icons import process_svg_file


def run(svg_file: Path, icons_dir: Path) -> int:
    """Replace icon placeholders with embedded SVG fragments."""

    return process_svg_file(svg_file, icons_dir=icons_dir, dry_run=False, verbose=False)
