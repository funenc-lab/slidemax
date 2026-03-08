"""Embed external raster images into SVG files as data URIs."""

from __future__ import annotations

import base64
import html
import re
from pathlib import Path
from typing import Tuple

from .image_utils import format_file_size, get_mime_type, resolve_svg_asset_path

HREF_PATTERN = re.compile(r'href="(?!data:)([^"]+\.(png|jpg|jpeg|gif|webp))"')


def embed_images_in_svg(svg_path: str | Path, dry_run: bool = False) -> Tuple[int, int]:
    """Embed external raster image references inside an SVG file."""

    svg_path = Path(svg_path)
    svg_dir = svg_path.resolve().parent
    content = svg_path.read_text(encoding="utf-8")
    original_size = len(content.encode("utf-8"))

    images_found = []
    images_embedded = 0

    def replace_with_base64(match: re.Match) -> str:
        nonlocal images_embedded
        img_path = match.group(1)
        img_path_decoded = html.unescape(img_path)
        full_path = resolve_svg_asset_path(svg_dir, img_path_decoded)

        if not full_path.exists():
            print(f"  [WARN] Image not found: {img_path}")
            images_found.append((img_path, "NOT FOUND", 0))
            return match.group(0)

        img_size = full_path.stat().st_size
        if dry_run:
            images_found.append((img_path, "WILL EMBED", img_size))
            return match.group(0)

        b64_data = base64.b64encode(full_path.read_bytes()).decode("utf-8")
        mime_type = get_mime_type(img_path)
        images_embedded += 1
        images_found.append((img_path, "EMBEDDED", img_size))
        return f'href="data:{mime_type};base64,{b64_data}"'

    new_content = HREF_PATTERN.sub(replace_with_base64, content)
    new_size = len(new_content.encode("utf-8"))

    if images_found:
        print(f"\n[FILE] {svg_path.name}")
        for img_path, status, size in images_found:
            size_str = format_file_size(size) if size > 0 else ""
            if status == "EMBEDDED":
                print(f"   [OK] {img_path} ({size_str})")
            elif status == "WILL EMBED":
                print(f"   [PREVIEW] {img_path} ({size_str}) [dry-run]")
            else:
                print(f"   [FAIL] {img_path} ({status})")
        print(f"   [SIZE] {format_file_size(original_size)} -> {format_file_size(new_size)}")

    if not dry_run and images_embedded > 0:
        svg_path.write_text(new_content, encoding="utf-8")

    return images_embedded, new_size
