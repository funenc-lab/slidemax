# SlideMax Command Reference

[中文](./README_CN.md) | English

This directory contains the canonical command entry points for the SlideMax workflow.

## Current Rules

- Use `skills/slidemax_workflow/commands/` as the canonical command surface.
- Use `skills/slidemax_workflow/slidemax/` as the shared Python core.
- When command behavior changes, update command bridges and shared core first, then reconcile the docs.

## Operational Command Quickstart

### End-to-End Command Path

```text
Start a PPT workflow task
  -> Normalize source
     -> PDF: `pdf_to_md.py`
     -> URL: `web_to_md.py` or `web_to_md.cjs`
     -> Screenshot/image document: OCR skill `.agent/skills/ocr_image_to_markdown/SKILL.md`
     -> Markdown/Text: use directly
  -> Create project: `project_manager.py init`
  -> Produce strategy and role outputs
  -> Acquire images when needed
     -> AI image: `image_generate.py`
     -> Provider smoke test: `smoke_test_image_provider.py`
     -> Stock image: `download_stock_image.py` / `register_stock_image.py`
  -> Finalize SVG: `finalize_svg.py`
  -> Export PPTX: `svg_to_pptx.py -s final`
  -> Validate project: `project_manager.py validate` or `batch_validate.py`
```

### Command Decision Flow

```text
What is the immediate task?
|
+-- Convert source material ----------------> `pdf_to_md.py` / `web_to_md.py` / `web_to_md.cjs`
+-- Transcribe screenshots / image docs ---> OCR skill `.agent/skills/ocr_image_to_markdown/SKILL.md`
+-- Create or inspect a project -----------> `project_manager.py init|validate|info`
+-- Generate or verify images -------------> `image_generate.py` / `smoke_test_image_provider.py`
+-- Register stock assets -----------------> `download_stock_image.py` / `register_stock_image.py`
+-- Fix or finalize SVG -------------------> `finalize_svg.py`
+-- Export PPTX ---------------------------> `svg_to_pptx.py -s final`
+-- Diagnose quality ----------------------> `svg_quality_checker.py` / `batch_validate.py` / `error_helper.py`
```

## Reliable Default Commands

```bash
# 1. Create a project
python3 skills/slidemax_workflow/commands/project_manager.py init my_project --format ppt169

# 2. Smoke test an image provider before relying on it
python3 skills/slidemax_workflow/commands/smoke_test_image_provider.py --provider gemini --output workspace/my_project/images

# 3. Finalize generated SVG
python3 skills/slidemax_workflow/commands/finalize_svg.py workspace/my_project_ppt169_YYYYMMDD

# 4. Export finalized SVG to PPTX
python3 skills/slidemax_workflow/commands/svg_to_pptx.py workspace/my_project_ppt169_YYYYMMDD -s final

# 5. Validate the project before completion claims
python3 skills/slidemax_workflow/commands/project_manager.py validate workspace/my_project_ppt169_YYYYMMDD
```

## Command Groups

### Source Conversion

- `pdf_to_md.py` - Convert PDF documents to Markdown
- `web_to_md.py` - Convert standard web pages to Markdown
- `web_to_md.cjs` - Convert harder web targets such as WeChat pages

### Project Management

- `project_manager.py` - Create, inspect, and validate projects
- `project_utils.py` - Project utility bridge and helpers
- `generate_examples_index.py` - Regenerate the examples index

### Image and Media

- `analyze_images.py` - Analyze local image assets and generate a CSV inventory
- `image_generate.py` - Provider-neutral image generation entry
- `nano_banana_gen.py` - Legacy Gemini-compatible image generation wrapper
- `smoke_test_image_provider.py` - Validate live image provider configuration
- `register_stock_image.py` - Register an existing stock asset into `images/stock/manifest.json`
- `download_stock_image.py` - Download and register a stock asset into `images/stock/manifest.json`
- `gemini_watermark_remover.py` - Remove Gemini star watermark assets
- `doubao_i2v_task.py` - ARK image-to-video task CLI

### SVG Finalization and Helpers

- `finalize_svg.py` - Canonical SVG finalization entry
- `embed_icons.py` - Replace icon placeholders with local SVG icons
- `crop_images.py` - Crop slice-mode image references into prepared assets
- `fix_image_aspect.py` - Adjust image frames to preserve aspect ratio
- `embed_images.py` - Inline raster image assets into SVG files
- `flatten_tspan.py` - Flatten `tspan`-based text nodes
- `svg_rect_to_path.py` - Convert rounded rectangles into plain path geometry
- `svg_position_calculator.py` - Validate and calculate chart-safe SVG layout positions

### Export and Validation

- `svg_to_pptx.py` - Export SVG slides to PPTX
- `pptx_animations.py` - PPTX transition and animation compatibility helpers
- `svg_quality_checker.py` - Validate SVG compliance and detect compatibility issues
- `batch_validate.py` - Batch validation entry
- `error_helper.py` - Human-readable error explanations and fix hints
- `config.py` - Inspect shared configuration and canvas definitions
- `total_md_split.py` - Split speaker notes into per-slide note files

## Reliability Rules

- Prefer canonical commands in this directory over ad-hoc scripts.
- Prefer `finalize_svg.py` over manually chaining finalizer internals unless debugging a specific stage.
- Prefer `svg_to_pptx.py -s final` for delivery builds.
- Prefer provider smoke tests before relying on a live image setup.
- Prefer project-local asset paths over remote links in slide content.
- Prefer generated indexes and manifests to be refreshed by commands instead of manual edits.

## Related Resources

- [Workflow Rules](../AGENTS.md)
- [Workflow Index](../workflows/README.md)
- [Documentation Index](../docs/README.md)
- [Role Definitions](../roles/README.md)
- [Chart Templates](../templates/charts/README.md)
