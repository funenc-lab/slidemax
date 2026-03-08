"""Shared Python namespace for SlideMax tooling.

This package provides a stable import boundary for reusable tool modules.
Legacy top-level scripts remain available, while new integrations should prefer
imports from ``slidemax.*``.
"""

__all__ = [
    "batch_validation",
    "asset_policy",
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
    "image_source_metadata",
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
    "watermark_detection",
]
