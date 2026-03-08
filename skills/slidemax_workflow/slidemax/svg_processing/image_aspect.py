"""Normalize SVG image frames to preserve source aspect ratios."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple
from xml.etree import ElementTree as ET

from .image_utils import get_image_dimensions


def calculate_fitted_dimensions(img_width: int, img_height: int, box_width: float, box_height: float, mode: str = "meet") -> Tuple[float, float, float, float]:
    """Calculate fitted image geometry for a target box."""

    img_ratio = img_width / img_height
    box_ratio = box_width / box_height

    if mode == "meet":
        if img_ratio > box_ratio:
            new_width = box_width
            new_height = box_width / img_ratio
        else:
            new_height = box_height
            new_width = box_height * img_ratio
    else:
        if img_ratio > box_ratio:
            new_height = box_height
            new_width = box_height * img_ratio
        else:
            new_width = box_width
            new_height = box_width / img_ratio

    offset_x = (box_width - new_width) / 2
    offset_y = (box_height - new_height) / 2
    return new_width, new_height, offset_x, offset_y


def fix_image_aspect_in_svg(svg_path: str | Path, dry_run: bool = False, verbose: bool = True) -> int:
    """Adjust SVG image frames to preserve their real aspect ratio."""

    svg_path = str(svg_path)
    svg_dir = os.path.dirname(os.path.abspath(svg_path))

    namespaces = {
        "": "http://www.w3.org/2000/svg",
        "xlink": "http://www.w3.org/1999/xlink",
        "svg": "http://www.w3.org/2000/svg",
        "sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
        "inkscape": "http://www.inkscape.org/namespaces/inkscape",
    }
    for prefix, uri in namespaces.items():
        if prefix:
            ET.register_namespace(prefix, uri)
        else:
            ET.register_namespace("", uri)

    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except ET.ParseError as exc:
        print(f"  [ERROR] Cannot parse SVG: {exc}")
        return 0

    fixed_count = 0
    for ns_prefix in ["", "{http://www.w3.org/2000/svg}"]:
        for image_elem in root.iter(f"{ns_prefix}image"):
            href = image_elem.get("{http://www.w3.org/1999/xlink}href")
            if href is None:
                href = image_elem.get("href")
            if href is None:
                continue

            try:
                x = float(image_elem.get("x", 0))
                y = float(image_elem.get("y", 0))
                width = float(image_elem.get("width", 0))
                height = float(image_elem.get("height", 0))
            except (ValueError, TypeError):
                continue

            if width <= 0 or height <= 0:
                continue

            par = image_elem.get("preserveAspectRatio", "xMidYMid meet")
            parts = par.split()
            align = parts[0] if parts else "xMidYMid"
            meet_or_slice = parts[1] if len(parts) > 1 else "meet"
            if align == "none":
                continue

            img_width, img_height = get_image_dimensions(href, svg_dir)
            if img_width is None or img_height is None:
                continue

            mode = "slice" if meet_or_slice == "slice" else "meet"
            new_width, new_height, offset_x, offset_y = calculate_fitted_dimensions(
                img_width,
                img_height,
                width,
                height,
                mode,
            )

            tolerance = 0.5
            if abs(new_width - width) < tolerance and abs(new_height - height) < tolerance:
                continue

            if verbose:
                img_name = os.path.basename(href.split("?")[0][:50] if not href.startswith("data:") else "[base64]")
                print(f"  [FIX] {img_name}")
                print(f"        Source: {img_width}x{img_height} (ratio: {img_width / img_height:.3f})")
                print(f"        Box: {width}x{height} @ ({x}, {y})")
                print(f"        New: {new_width:.1f}x{new_height:.1f} @ ({x + offset_x:.1f}, {y + offset_y:.1f})")

            if not dry_run:
                image_elem.set("x", f"{x + offset_x:.1f}")
                image_elem.set("y", f"{y + offset_y:.1f}")
                image_elem.set("width", f"{new_width:.1f}")
                image_elem.set("height", f"{new_height:.1f}")
                if "preserveAspectRatio" in image_elem.attrib:
                    del image_elem.attrib["preserveAspectRatio"]

            fixed_count += 1

    if not dry_run and fixed_count > 0:
        tree.write(svg_path, encoding="unicode", xml_declaration=True)

    return fixed_count
