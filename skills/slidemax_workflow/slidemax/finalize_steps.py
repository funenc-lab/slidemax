"""Step registry for the SlideMax finalize pipeline."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, Tuple

from .finalizers import (
    crop_images,
    embed_icons,
    embed_images,
    fix_aspect,
    fix_rounded,
    flatten_text,
    sanitize,
)

STEP_CHOICES: Tuple[str, ...] = (
    "sanitize",
    "embed-icons",
    "crop-images",
    "fix-aspect",
    "embed-images",
    "flatten-text",
    "fix-rounded",
)


@dataclass(frozen=True)
class FinalizeContext:
    """Resolved filesystem context for the finalize pipeline."""

    project_dir: Path
    svg_output: Path
    svg_final: Path
    icons_dir: Path


@dataclass(frozen=True)
class FinalizeStepDefinition:
    """Metadata and handler for a finalize step."""

    name: str
    title: str
    success_suffix: str
    empty_message: str
    runner: Callable[[FinalizeContext, Iterable[Path]], int]


def copy_svg_output(svg_output: Path, svg_final: Path) -> None:
    """Create a fresh working copy of the SVG tree in ``svg_final``."""

    if svg_final.exists():
        shutil.rmtree(svg_final)
    shutil.copytree(svg_output, svg_final)


def build_step_registry() -> Dict[str, FinalizeStepDefinition]:
    """Build the ordered finalize step registry."""

    return {
        "sanitize": FinalizeStepDefinition(
            name="sanitize",
            title="Sanitizing SVG compatibility",
            success_suffix="files sanitized",
            empty_message="No sanitization changes needed",
            runner=lambda context, files: sum(sanitize(svg_file) for svg_file in files),
        ),
        "embed-icons": FinalizeStepDefinition(
            name="embed-icons",
            title="Embedding icons",
            success_suffix="icons embedded",
            empty_message="No icon placeholders found",
            runner=lambda context, files: sum(embed_icons(svg_file, context.icons_dir) for svg_file in files),
        ),
        "crop-images": FinalizeStepDefinition(
            name="crop-images",
            title="Cropping images",
            success_suffix="images cropped",
            empty_message="No slice-based images found",
            runner=lambda context, files: sum(crop_images(svg_file) for svg_file in files),
        ),
        "fix-aspect": FinalizeStepDefinition(
            name="fix-aspect",
            title="Fixing image aspect ratios",
            success_suffix="images fixed",
            empty_message="No images found",
            runner=lambda context, files: sum(fix_aspect(svg_file) for svg_file in files),
        ),
        "embed-images": FinalizeStepDefinition(
            name="embed-images",
            title="Embedding images",
            success_suffix="images embedded",
            empty_message="No external images found",
            runner=lambda context, files: sum(embed_images(svg_file) for svg_file in files),
        ),
        "flatten-text": FinalizeStepDefinition(
            name="flatten-text",
            title="Flattening text",
            success_suffix="files flattened",
            empty_message="No text flattening needed",
            runner=lambda context, files: sum(flatten_text(svg_file) for svg_file in files),
        ),
        "fix-rounded": FinalizeStepDefinition(
            name="fix-rounded",
            title="Converting rounded rects",
            success_suffix="rounded rects converted",
            empty_message="No rounded rects found",
            runner=lambda context, files: sum(fix_rounded(svg_file) for svg_file in files),
        ),
    }


__all__ = [
    "STEP_CHOICES",
    "FinalizeContext",
    "FinalizeStepDefinition",
    "build_step_registry",
    "copy_svg_output",
]
