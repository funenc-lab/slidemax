# SlideMax Command Reference

[中文](./command_reference_cn.md) | English

This document describes the SlideMax command surface and points to the canonical runtime scripts.

## Current Rules

- Use `skills/slidemax_workflow/scripts/slidemax.py` as the canonical command tool.
- Use `skills/slidemax_workflow/slidemax/` as the shared Python core and command registry.
- Use `skills/slidemax_workflow/references/docs/command_reference*.md` as the command documentation.
- Keep `skills/slidemax_workflow/scripts/web_to_md.cjs` as the standalone Node fallback implementation.
- When command behavior changes, update the unified tool and shared core first, then reconcile the docs.

## Operational Command Quickstart

### End-to-End Command Path

```text
Start a PPT workflow task
  -> Normalize source
     -> PDF: `pdf_to_md`
     -> URL: `web_to_md` or `web_to_md_cjs`
     -> Screenshot/image document: OCR skill `.agent/skills/ocr_image_to_markdown/SKILL.md`
     -> Markdown/Text: use directly
  -> Create project: `project_manager init`
  -> Inspect workflow stage progression when needed: `project_manager audit`
  -> Produce strategy and role outputs
  -> Acquire images when needed
     -> User-supplied image analysis: `analyze_images`
     -> AI image: `image_generate`
     -> Provider smoke test: `smoke_test_image_provider`
     -> Stock image: `download_stock_image` / `register_stock_image`
     -> Provenance and risk audit: `register_image_source` / `audit_image_asset`
  -> Split notes explicitly: `total_md_split`
  -> Finalize SVG: `finalize_svg`
  -> Export PPTX: `svg_to_pptx -s final`
  -> Validate delivery: `project_manager validate` or `batch_validate`
```

### Command Decision Flow

```text
What is the immediate task?
|
+-- Convert source material ----------------> `pdf_to_md` / `web_to_md` / `web_to_md_cjs`
+-- Transcribe screenshots / image docs ---> OCR skill `.agent/skills/ocr_image_to_markdown/SKILL.md`
+-- Create or inspect a project -----------> `project_manager init|validate|info|audit|doctor`
+-- Analyze user image assets -------------> `analyze_images`
+-- Generate or verify images -------------> `image_generate` / `smoke_test_image_provider`
+-- Fix image orientation -----------------> `rotate_images`
+-- Register stock assets -----------------> `download_stock_image` / `register_stock_image`
+-- Record asset provenance ---------------> `register_image_source` / `audit_image_asset`
+-- Split notes before delivery -----------> `total_md_split`
+-- Fix or finalize SVG -------------------> `finalize_svg`
+-- Export PPTX ---------------------------> `svg_to_pptx -s final`
+-- Diagnose quality ----------------------> `svg_quality_checker` / `batch_validate` / `error_helper`
+-- Install export environment -----------> `setup_export_env`
```

## Reliable Default Commands

```bash
# 1. Create a project
python3 skills/slidemax_workflow/scripts/slidemax.py project_manager init my_project --format ppt169

# 2. Assume the created project path is workspace/my_project_ppt169_YYYYMMDD

# 3. Smoke test an image provider before relying on it
python3 skills/slidemax_workflow/scripts/slidemax.py smoke_test_image_provider --provider gemini --output workspace/my_project_ppt169_YYYYMMDD/images

# 4. Split notes explicitly before delivery
python3 skills/slidemax_workflow/scripts/slidemax.py total_md_split workspace/my_project_ppt169_YYYYMMDD

# 5. Finalize generated SVG
python3 skills/slidemax_workflow/scripts/slidemax.py finalize_svg workspace/my_project_ppt169_YYYYMMDD

# 6. Export finalized SVG to PPTX
python3 skills/slidemax_workflow/scripts/slidemax.py svg_to_pptx workspace/my_project_ppt169_YYYYMMDD -s final

# 7. Validate the project before completion claims
python3 skills/slidemax_workflow/scripts/slidemax.py project_manager validate workspace/my_project_ppt169_YYYYMMDD
```

## Command Groups

### Source Conversion

- `pdf_to_md` - Convert PDF documents to Markdown
- `web_to_md` - Convert standard web pages to Markdown
- `web_to_md_cjs` - Standalone Node fallback for harder web targets such as WeChat pages

### Project Management

- `project_manager` - Create projects, run preflight checks, and validate final delivery outputs
- `project_utils` - Project utility bridge and helpers
- `generate_examples_index` - Regenerate the examples index

### Image and Media

- `analyze_images` - Analyze local image assets and generate a CSV inventory
- `image_generate` - Provider-neutral image generation entry
- `nano_banana_gen` - Legacy Gemini-compatible image generation wrapper
- `smoke_test_image_provider` - Validate live image provider configuration
- `register_image_source` - Write or update provenance sidecars for local image assets
- `register_stock_image` - Register an existing stock asset into `images/stock/manifest.json`
- `download_stock_image` - Download and register a stock asset into `images/stock/manifest.json`
- `rotate_images` - Rotate local image assets and apply recorded fixes
- `audit_image_asset` - Audit watermark and provenance risk before delivery
- `gemini_watermark_remover` - Remove Gemini star watermark assets
- `doubao_i2v_task` - ARK image-to-video task CLI

### SVG Finalization and Helpers

- `finalize_svg` - Canonical SVG finalization entry
- `embed_icons` - Replace icon placeholders with local SVG icons
- `crop_images` - Crop slice-mode image references into prepared assets
- `fix_image_aspect` - Adjust image frames to preserve aspect ratio
- `embed_images` - Inline raster image assets into SVG files
- `flatten_tspan` - Flatten `tspan`-based text nodes
- `svg_rect_to_path` - Convert rounded rectangles into plain path geometry
- `svg_position_calculator` - Validate and calculate chart-safe SVG layout positions

### Export and Validation

- `svg_to_pptx` - Export SVG slides to PPTX
- `svg_quality_checker` - Validate SVG compliance and detect compatibility issues
- `batch_validate` - Batch validation entry
- `error_helper` - Human-readable error explanations and fix hints
- `config` - Inspect shared configuration and canvas definitions
- `total_md_split` - Split speaker notes into per-slide note files

## Reliability Rules

- Prefer the unified command tool over ad-hoc scripts.
- Prefer the explicit delivery path `total_md_split -> finalize_svg -> svg_to_pptx -s final -> project_manager validate` for release work.
- Use `project_manager audit` between draft and delivery stages to detect blocking stage gaps early.
- Prefer `finalize_svg` over manually chaining finalizer internals unless debugging a specific stage.
- Prefer `svg_to_pptx -s final` for delivery builds.
- `svg_to_pptx` auto-splits `notes/total.md` when per-slide notes are missing, but treat that as a fallback rather than the primary delivery path.
- Treat `project_manager doctor` as the permissive preflight path and `project_manager validate` as the strict delivery gate.
- Treat `project_manager audit` as the stage-consistency check for in-progress projects.
- `project_manager validate` should only be treated as passing when finalized SVG, note coverage, and an exported `.pptx` are present.
- Prefer provider smoke tests before relying on a live image setup.
- Prefer project-local asset paths over remote links in slide content.
- Prefer generated indexes and manifests to be refreshed by commands instead of manual edits.

## Related Resources

- [Workflow Rules](../../AGENTS.md)
- [Workflow Index](../../workflows/README.md)
- [Image Prompt Guidance](./image_prompt_guidance.md)
- [Role Definitions](../../roles/AGENTS.md)
- [Chart Templates](../../templates/charts/README.md)
