"""Embed icon placeholders into SVG files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from ..config import TEMPLATES_DIR

DEFAULT_ICONS_DIR = TEMPLATES_DIR / "icons"
ICON_BASE_SIZE = 16
USE_PATTERN = re.compile(r'<use\s+[^>]*data-icon="[^"]*"[^>]*/>')
PATH_PATTERN = re.compile(r'<path\s+([^>]*)/>', re.DOTALL)


def extract_paths_from_icon(icon_path: Path) -> List[str]:
    """Extract SVG path nodes from an icon file."""

    if not icon_path.exists():
        return []

    content = icon_path.read_text(encoding="utf-8")
    matches = PATH_PATTERN.findall(content)
    paths = []
    for attrs in matches:
        attrs_clean = re.sub(r'\s*fill="[^"]*"', "", attrs)
        paths.append(f'<path {attrs_clean.strip()}/>')
    return paths


def parse_use_element(use_match: str) -> Dict[str, float | str]:
    """Parse the supported attributes from an icon placeholder."""

    attrs: Dict[str, float | str] = {}

    icon_match = re.search(r'data-icon="([^"]+)"', use_match)
    if icon_match:
        attrs["icon"] = icon_match.group(1)

    for attr in ["x", "y", "width", "height"]:
        match = re.search(rf'{attr}="([^"]+)"', use_match)
        if match:
            attrs[attr] = float(match.group(1))

    fill_match = re.search(r'fill="([^"]+)"', use_match)
    if fill_match:
        attrs["fill"] = fill_match.group(1)

    return attrs


def generate_icon_group(attrs: Dict[str, float | str], paths: List[str]) -> str:
    """Build the replacement SVG group for one icon placeholder."""

    x = attrs.get("x", 0)
    y = attrs.get("y", 0)
    width = attrs.get("width", ICON_BASE_SIZE)
    fill = attrs.get("fill", "#000000")
    icon_name = attrs.get("icon", "unknown")
    scale = float(width) / ICON_BASE_SIZE

    if scale == 1:
        transform = f"translate({x}, {y})"
    else:
        transform = f"translate({x}, {y}) scale({scale})"

    paths_str = "\n    ".join(paths)
    return (
        f'<!-- icon: {icon_name} -->\n'
        f'  <g transform="{transform}" fill="{fill}">\n'
        f'    {paths_str}\n'
        f'  </g>'
    )


def process_svg_file(
    svg_path: Path,
    icons_dir: Path = DEFAULT_ICONS_DIR,
    dry_run: bool = False,
    verbose: bool = False,
) -> int:
    """Replace icon placeholders in one SVG file."""

    if not svg_path.exists():
        print(f"[ERROR] File not found: {svg_path}")
        return 0

    content = svg_path.read_text(encoding="utf-8")
    matches = list(USE_PATTERN.finditer(content))

    if not matches:
        if verbose:
            print(f"[SKIP] No icon placeholders: {svg_path}")
        return 0

    replaced_count = 0
    new_content = content

    for match in reversed(matches):
        use_str = match.group(0)
        attrs = parse_use_element(use_str)
        icon_name = attrs.get("icon")
        if not icon_name:
            continue

        icon_path = icons_dir / f"{icon_name}.svg"
        paths = extract_paths_from_icon(icon_path)
        if not paths:
            print(f"[WARN] Icon not found: {icon_name} (in {svg_path.name})")
            continue

        replacement = generate_icon_group(attrs, paths)
        if verbose or dry_run:
            print(
                f"  [*] {icon_name}: x={attrs.get('x', 0)}, y={attrs.get('y', 0)}, "
                f"size={attrs.get('width', 16)}, fill={attrs.get('fill', '#000000')}"
            )

        new_content = new_content[:match.start()] + replacement + new_content[match.end():]
        replaced_count += 1

    if not dry_run and replaced_count > 0:
        svg_path.write_text(new_content, encoding="utf-8")

    status = "[PREVIEW]" if dry_run else "[OK]"
    print(f"{status} {svg_path.name} ({replaced_count} icons)")
    return replaced_count
