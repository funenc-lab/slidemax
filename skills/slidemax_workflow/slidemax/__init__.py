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
    "web_markdown",
    "pptx_animations",
    "pptx_export",
    "exporters",
    "project_management",
    "project_state",
    "project_utils",
    "subcommands",
    "svg_processing",
    "svg_rules",
    "svg_quality",
    "svg_positioning",
    "watermark_removal",
    "watermark_detection",
]
