# Documentation Index

[中文](./README_CN.md) | English

This directory stores supporting documentation for `skills/slidemax_workflow/`, including workflow guidance, design rules, image handling rules, export behavior, and operator manuals.

## Current Rules

- **Only workflow source of truth**: `skills/slidemax_workflow/`
- **Full rules handbook**: [`../AGENTS.md`](../AGENTS.md)
- **Workflow entry document**: [`../workflows/generate-ppt.md`](../workflows/generate-ppt.md)
- **Command entry directory**: [`../commands/`](../commands/)
- **Shared Python core**: [`../slidemax/`](../slidemax/)

## 📖 Document List

### Workflow and Operations

- [workflow_tutorial.md](./workflow_tutorial.md) - Workflow tutorial and walkthroughs
- [ppt_workflow_operator_manual.md](./ppt_workflow_operator_manual.md) - Operator manual and execution checklists
- [quick_reference.md](./quick_reference.md) - Common commands and parameter cheat sheet

### Design and Canvas

- [canvas_formats.md](./canvas_formats.md) - Canvas format specifications
- [design_guidelines.md](./design_guidelines.md) - Design rules and visual guidance
- [image_layout_spec.md](./image_layout_spec.md) - Image layout strategy and page-level image usage rules
- [svg_image_embedding.md](./svg_image_embedding.md) - SVG image embedding guide

### Images and Media Capabilities

- [image_stock_sources.md](./image_stock_sources.md) - Commercial stock source and manifest rules
- [image_generation_providers.md](./image_generation_providers.md) - Image provider registry and environment variables
- [image_generation_setup.md](./image_generation_setup.md) - Image generation setup and command examples
- [ai_setup_prompts.md](./ai_setup_prompts.md) - AI-ready prompts for env setup and verification
- [ark_video_generation.md](./ark_video_generation.md) - ARK image-to-video setup and examples

### Architecture and Maintenance

- [architecture/repository_structure.md](./architecture/repository_structure.md) - Current repository structure and source-of-truth boundaries
- [plans/2026-03-07-repo-structure-reorg.md](./plans/2026-03-07-repo-structure-reorg.md) - Repository reorganization plan and rationale

## 🔗 Related Resources

- [Role Definitions](../roles/README.md)
- [Workflow Index](../workflows/README.md)
- [Chart Templates](../templates/charts/README.md)
- [Icon Library](../templates/icons/README.md)
- [Commands Reference](../commands/README.md)
- [OCR Image to Markdown skill](../../../.agent/skills/ocr_image_to_markdown/SKILL.md) - Skill entry for screenshot or scanned-image source material

## Maintenance Rules

- Update canonical documents first instead of copying instructions into parallel files.
- When workflow rules change, update `../AGENTS.md` and `../workflows/generate-ppt.md` first.
- When command behavior and documentation diverge, reconcile against the current state of `../commands/` and `../slidemax/`, then backfill the docs.
- Refresh generated example statistics through canonical commands instead of manually editing generated files.
