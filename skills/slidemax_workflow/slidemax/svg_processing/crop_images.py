"""Crop SVG image references based on preserveAspectRatio settings."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import unquote
from xml.etree import ElementTree as ET

from .image_utils import Image, require_pillow


def parse_preserve_aspect_ratio(attr: str) -> Tuple[str, str]:
    """Parse the preserveAspectRatio SVG attribute."""

    if not attr:
        return ("xMidYMid", "meet")

    parts = attr.strip().split()
    align = parts[0] if parts else "xMidYMid"
    meet_or_slice = parts[1] if len(parts) > 1 else "meet"
    return (align, meet_or_slice)


def get_crop_anchor(align: str) -> Tuple[float, float]:
    """Resolve crop anchor fractions from an SVG alignment token."""

    x_map = {"xMin": 0.0, "xMid": 0.5, "xMax": 1.0}
    y_map = {"YMin": 0.0, "YMid": 0.5, "YMax": 1.0}

    x_anchor = 0.5
    y_anchor = 0.5

    for key, value in x_map.items():
        if key in align:
            x_anchor = value
            break

    for key, value in y_map.items():
        if key in align:
            y_anchor = value
            break

    return (x_anchor, y_anchor)


def crop_image_to_size(img: "Image.Image", target_width: int, target_height: int, x_anchor: float = 0.5, y_anchor: float = 0.5) -> "Image.Image":
    """Crop an image to the target ratio without rescaling."""

    img_width, img_height = img.size
    target_ratio = target_width / target_height
    img_ratio = img_width / img_height

    if img_ratio > target_ratio:
        crop_height = img_height
        crop_width = int(img_height * target_ratio)
    else:
        crop_width = img_width
        crop_height = int(img_width / target_ratio)

    extra_width = img_width - crop_width
    extra_height = img_height - crop_height

    left = int(extra_width * x_anchor)
    top = int(extra_height * y_anchor)
    right = left + crop_width
    bottom = top + crop_height
    return img.crop((left, top, right, bottom))


def process_svg_images(
    svg_file: str | Path,
    output_dir: Optional[str | Path] = None,
    dry_run: bool = False,
    verbose: bool = True,
) -> Tuple[int, int]:
    """Crop slice-mode SVG images and rewrite their href references."""

    require_pillow()

    svg_path = Path(svg_file)
    svg_dir = svg_path.parent

    if output_dir is None:
        project_dir = svg_dir.parent
        output_dir = project_dir / "images" / "cropped"
    else:
        output_dir = Path(output_dir)

    try:
        ET.register_namespace("", "http://www.w3.org/2000/svg")
        ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
        tree = ET.parse(str(svg_path))
        root = tree.getroot()
    except Exception as exc:
        if verbose:
            print(f"  [ERROR] Failed to parse SVG: {exc}")
        return (0, 1)

    processed_count = 0
    error_count = 0
    modified = False

    for image in root.iter("{http://www.w3.org/2000/svg}image"):
        href = image.get("{http://www.w3.org/1999/xlink}href") or image.get("href")
        if not href or href.startswith("data:"):
            continue

        align, mode = parse_preserve_aspect_ratio(image.get("preserveAspectRatio", ""))
        if mode != "slice":
            continue

        try:
            target_width = int(float(image.get("width", 0)))
            target_height = int(float(image.get("height", 0)))
        except (ValueError, TypeError):
            continue

        if target_width <= 0 or target_height <= 0:
            continue

        href_decoded = unquote(href)
        img_path = (svg_dir / href_decoded).resolve()
        if not img_path.exists():
            if verbose:
                print(f"    [SKIP] Image not found: {href}")
            continue

        x_anchor, y_anchor = get_crop_anchor(align)
        if dry_run:
            if verbose:
                print(
                    f"    [DRY] {img_path.name} -> {target_width}x{target_height} "
                    f"(align: {align}, anchor: {x_anchor},{y_anchor})"
                )
            processed_count += 1
            continue

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            img = Image.open(img_path)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            cropped = crop_image_to_size(img, target_width, target_height, x_anchor, y_anchor)
            output_filename = img_path.name
            output_path = Path(output_dir) / output_filename

            if img_path.suffix.lower() == ".png":
                cropped.save(output_path, "PNG", optimize=True)
            else:
                cropped.save(output_path, "JPEG", quality=90, optimize=True)

            if verbose:
                print(f"    [OK] {img_path.name}: {img.size} -> {target_width}x{target_height} ({align})")

            new_href = f"../images/cropped/{output_filename}"
            if image.get("{http://www.w3.org/1999/xlink}href"):
                image.set("{http://www.w3.org/1999/xlink}href", new_href)
            else:
                image.set("href", new_href)
            if "preserveAspectRatio" in image.attrib:
                del image.attrib["preserveAspectRatio"]

            modified = True
            processed_count += 1
        except Exception as exc:
            if verbose:
                print(f"    [ERROR] {img_path.name}: {exc}")
            error_count += 1

    if modified and not dry_run:
        tree.write(str(svg_path), encoding="unicode", xml_declaration=False)

    return (processed_count, error_count)


def process_directory(directory: str | Path, dry_run: bool = False, verbose: bool = True) -> Tuple[int, int]:
    """Process all SVG files in a directory."""

    directory = Path(directory)
    total_processed = 0
    total_errors = 0

    for svg_file in directory.glob("*.svg"):
        if verbose:
            print(f"  Processing: {svg_file.name}")
        processed, errors = process_svg_images(svg_file, dry_run=dry_run, verbose=verbose)
        total_processed += processed
        total_errors += errors

    return (total_processed, total_errors)
