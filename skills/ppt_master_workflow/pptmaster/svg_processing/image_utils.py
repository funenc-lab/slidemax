"""Shared image helpers for SVG processing modules."""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path
from typing import Optional, Tuple

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    Image = None
    HAS_PIL = False

DATA_URI_RE = re.compile(r"data:image/(\w+);base64,(.+)")


def require_pillow() -> None:
    """Ensure Pillow is available for image editing operations."""

    if not HAS_PIL:
        raise RuntimeError("Pillow is required. Run: pip install Pillow")


def get_mime_type(filename: str) -> str:
    """Return the MIME type inferred from a filename."""

    ext = filename.lower().split(".")[-1]
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
        "svg": "image/svg+xml",
    }
    return mime_map.get(ext, "application/octet-stream")


def format_file_size(size_bytes: int) -> str:
    """Format bytes into a human-readable size string."""

    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def resolve_svg_asset_path(svg_dir: str | Path, href: str) -> Path:
    """Resolve an SVG asset href into an absolute local filesystem path."""

    svg_dir = Path(svg_dir)
    href_path = Path(href)
    if href_path.is_absolute():
        return href_path
    return (svg_dir / href).resolve()


def get_image_dimensions_pil(image_path: str | Path) -> Tuple[Optional[int], Optional[int]]:
    """Read image dimensions with Pillow."""

    try:
        with Image.open(image_path) as img:
            return img.width, img.height
    except Exception as exc:
        print(f"  [WARN] Cannot read image with Pillow: {exc}")
        return None, None


def get_image_dimensions_basic(image_path: str | Path) -> Tuple[Optional[int], Optional[int]]:
    """Read PNG or JPEG dimensions without Pillow."""

    try:
        with open(image_path, "rb") as file_obj:
            data = file_obj.read(64)

        if data[:8] == b"\x89PNG\r\n\x1a\n":
            width = int.from_bytes(data[16:20], "big")
            height = int.from_bytes(data[20:24], "big")
            return width, height

        if data[:2] == b"\xff\xd8":
            with open(image_path, "rb") as file_obj:
                file_obj.seek(2)
                while True:
                    marker = file_obj.read(2)
                    if not marker or len(marker) < 2 or marker[0] != 0xFF:
                        break
                    code = marker[1]
                    if code in (0xC0, 0xC2):
                        file_obj.read(3)
                        height = int.from_bytes(file_obj.read(2), "big")
                        width = int.from_bytes(file_obj.read(2), "big")
                        return width, height
                    if code in (0xD9,):
                        break
                    if code in (0xD8,) or 0xD0 <= code <= 0xD7:
                        continue
                    length = int.from_bytes(file_obj.read(2), "big")
                    file_obj.seek(length - 2, 1)

        return None, None
    except Exception as exc:
        print(f"  [WARN] Cannot read image dimensions: {exc}")
        return None, None


def get_image_dimensions_from_base64(data_uri: str) -> Tuple[Optional[int], Optional[int]]:
    """Read image dimensions from a Base64 data URI."""

    import io

    try:
        match = DATA_URI_RE.match(data_uri)
        if not match:
            return None, None
        img_bytes = base64.b64decode(match.group(2))
        if HAS_PIL:
            with Image.open(io.BytesIO(img_bytes)) as img:
                return img.width, img.height
        if img_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            width = int.from_bytes(img_bytes[16:20], "big")
            height = int.from_bytes(img_bytes[20:24], "big")
            return width, height
        return None, None
    except Exception as exc:
        print(f"  [WARN] Cannot parse base64 image: {exc}")
        return None, None


def get_image_dimensions(href: str, svg_dir: str | Path) -> Tuple[Optional[int], Optional[int]]:
    """Read image dimensions for an SVG href target."""

    if href.startswith("data:"):
        return get_image_dimensions_from_base64(href)

    full_path = resolve_svg_asset_path(svg_dir, href)
    if not full_path.exists():
        print(f"  [WARN] Image not found: {href}")
        return None, None

    if HAS_PIL:
        return get_image_dimensions_pil(full_path)
    return get_image_dimensions_basic(full_path)
