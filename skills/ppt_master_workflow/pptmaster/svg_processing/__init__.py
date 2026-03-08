"""Reusable SVG processing helpers for PPT Master."""

from .crop_images import crop_image_to_size, get_crop_anchor, parse_preserve_aspect_ratio, process_directory as crop_images_directory, process_svg_images
from .embed_images import embed_images_in_svg
from .flatten_text import (
    compute_default_output_base,
    flatten_text_with_tspans,
    process_svg_file as flatten_text_file,
)
from .icons import DEFAULT_ICONS_DIR, generate_icon_group, parse_use_element, process_svg_file as embed_icons_file
from .image_aspect import calculate_fitted_dimensions, fix_image_aspect_in_svg
from .image_utils import format_file_size, get_image_dimensions, get_mime_type, require_pillow, resolve_svg_asset_path
from .rounded_rects import (
    find_svg_files,
    process_svg,
    process_svg_file as convert_rounded_rects_file,
    rect_to_rounded_path,
)

__all__ = [
    "format_file_size",
    "get_image_dimensions",
    "require_pillow",
    "resolve_svg_asset_path",
    "calculate_fitted_dimensions",
    "crop_image_to_size",
    "crop_images_directory",
    "fix_image_aspect_in_svg",
    "get_crop_anchor",
    "parse_preserve_aspect_ratio",
    "process_svg_images",
    "DEFAULT_ICONS_DIR",
    "embed_icons_file",
    "embed_images_in_svg",
    "generate_icon_group",
    "get_mime_type",
    "parse_use_element",
    "compute_default_output_base",
    "convert_rounded_rects_file",
    "find_svg_files",
    "flatten_text_file",
    "flatten_text_with_tspans",
    "process_svg",
    "rect_to_rounded_path",
]
