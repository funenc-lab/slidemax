"""Shared Python namespace for PPT Master tooling.

This package provides a stable import boundary for reusable tool modules.
Legacy top-level scripts remain available, while new integrations should prefer
imports from ``pptmaster.*``.
"""

__all__ = [
    "batch_validation",
    "config",
    "command_bridge",
    "error_helper",
    "export_setup",
    "examples_index",
    "finalize",
    "flatten_text_cli",
    "finalize_steps",
    "finalizers",
    "pdf_markdown",
    "image_analysis",
    "image_generation",
    "image_rotation",
    "notes_splitter",
    "stock_sources",
    "video_generation",
    "video_generation_cli",
    "web_markdown",
    "pptx_animations",
    "pptx_export",
    "exporters",
    "project_management",
    "project_utils",
    "rounded_rect_cli",
    "svg_processing",
    "svg_rules",
    "svg_quality",
    "svg_position_cli",
    "svg_asset_cli",
    "svg_positioning",
    "watermark_removal",
]
