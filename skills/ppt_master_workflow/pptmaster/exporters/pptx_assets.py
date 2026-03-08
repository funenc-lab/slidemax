"""Asset and canvas helpers for PPTX export."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config import CANVAS_FORMATS

PNG_RENDERER = None
cairosvg = None
svg2rlg = None
renderPM = None

try:
    import cairosvg as _cairosvg

    cairosvg = _cairosvg
    PNG_RENDERER = "cairosvg"
except ImportError:
    try:
        from svglib.svglib import svg2rlg as _svg2rlg
        from reportlab.graphics import renderPM as _renderPM

        svg2rlg = _svg2rlg
        renderPM = _renderPM
        PNG_RENDERER = "svglib"
    except ImportError:
        pass

EMU_PER_INCH = 914400
EMU_PER_PIXEL = EMU_PER_INCH / 96


def get_png_renderer_info() -> tuple:
    """Return renderer availability details."""

    if PNG_RENDERER == "cairosvg":
        return ("cairosvg", "(full gradients/filters)", None)
    if PNG_RENDERER == "svglib":
        return (
            "svglib",
            "(some gradients may degrade)",
            "Install cairosvg for better rendering: pip install cairosvg",
        )
    return (
        None,
        "(not installed)",
        "Install cairosvg or svglib/reportlab for compatibility mode",
    )


def get_slide_dimensions(
    canvas_format: str,
    custom_pixels: Optional[Tuple[int, int]] = None,
) -> Tuple[int, int]:
    """Return slide dimensions in EMU."""

    width_px, height_px = get_pixel_dimensions(canvas_format, custom_pixels)
    return int(width_px * EMU_PER_PIXEL), int(height_px * EMU_PER_PIXEL)


def get_pixel_dimensions(
    canvas_format: str,
    custom_pixels: Optional[Tuple[int, int]] = None,
) -> Tuple[int, int]:
    """Return slide dimensions in pixels."""

    if custom_pixels:
        return custom_pixels

    if canvas_format not in CANVAS_FORMATS:
        canvas_format = "ppt169"

    dimensions = CANVAS_FORMATS[canvas_format]["dimensions"]
    match = re.match(r"(\d+)[×x](\d+)", dimensions)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 1280, 720


def get_viewbox_dimensions(svg_path: Path) -> Optional[Tuple[int, int]]:
    """Extract viewBox width/height from an SVG file."""

    try:
        content = svg_path.read_text(encoding="utf-8")[:2000]
        match = re.search(r'viewBox="([^"]+)"', content)
        if not match:
            return None

        parts = re.split(r"[\s,]+", match.group(1).strip())
        if len(parts) < 4:
            return None

        width = float(parts[2])
        height = float(parts[3])
        if width <= 0 or height <= 0:
            return None
        return int(round(width)), int(round(height))
    except Exception:
        return None


def detect_format_from_svg(svg_path: Path) -> Optional[str]:
    """Detect canvas format from SVG viewBox."""

    try:
        content = svg_path.read_text(encoding="utf-8")[:2000]
        match = re.search(r'viewBox="([^"]+)"', content)
        if match:
            viewbox = match.group(1)
            for fmt_key, fmt_info in CANVAS_FORMATS.items():
                if fmt_info["viewbox"] == viewbox:
                    return fmt_key
    except Exception:
        pass
    return None


def convert_svg_to_png(
    svg_path: Path,
    png_path: Path,
    width: int = None,
    height: int = None,
) -> bool:
    """Render an SVG file to a PNG fallback image."""

    if PNG_RENDERER is None:
        return False

    try:
        if PNG_RENDERER == "cairosvg" and cairosvg is not None:
            cairosvg.svg2png(
                url=str(svg_path),
                write_to=str(png_path),
                output_width=width,
                output_height=height,
            )
            return True

        if PNG_RENDERER == "svglib" and svg2rlg is not None and renderPM is not None:
            drawing = svg2rlg(str(svg_path))
            if drawing is None:
                print(f"  Warning: unable to parse SVG ({svg_path.name})")
                return False
            renderPM.drawToFile(
                drawing,
                str(png_path),
                fmt="PNG",
                configPIL={"quality": 95},
            )
            return True
    except Exception as exc:
        print(f"  Warning: SVG to PNG failed ({svg_path.name}): {exc}")
        return False

    return False


def find_svg_files(project_path: Path, source: str = "output") -> Tuple[List[Path], str]:
    """Locate SVG files inside a project."""

    dir_map = {
        "output": "svg_output",
        "final": "svg_final",
    }
    dir_name = dir_map.get(source, source)
    svg_dir = project_path / dir_name

    if not svg_dir.exists():
        print(f"  Warning: {dir_name} not found, falling back to svg_output")
        dir_name = "svg_output"
        svg_dir = project_path / dir_name

    if not svg_dir.exists():
        if project_path.is_dir():
            svg_dir = project_path
            dir_name = project_path.name
        else:
            return [], ""

    return sorted(svg_dir.glob("*.svg")), dir_name


def find_notes_files(project_path: Path, svg_files: List[Path] = None) -> Dict[str, str]:
    """Locate note files and map them to SVG stems."""

    notes_dir = project_path / "notes"
    notes: Dict[str, str] = {}
    if not notes_dir.exists():
        return notes

    svg_stems_mapping = {}
    svg_index_mapping = {}
    if svg_files:
        for index, svg_path in enumerate(svg_files, 1):
            svg_stems_mapping[svg_path.stem] = index
            svg_index_mapping[index] = svg_path.stem

    for notes_file in notes_dir.glob("*.md"):
        try:
            content = notes_file.read_text(encoding="utf-8").strip()
            if not content:
                continue
            stem = notes_file.stem

            match = re.search(r"slide[_]?(\d+)", stem)
            if match:
                mapped_stem = svg_index_mapping.get(int(match.group(1)))
                if mapped_stem:
                    notes[mapped_stem] = content

            if stem in svg_stems_mapping:
                notes[stem] = content
        except Exception:
            pass

    return notes
