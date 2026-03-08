---
name: slidemax-workflow
description: Use when generating PPT, XHS, story, or related canvas outputs with this repository, or when maintaining workflow-facing assets under skills/slidemax_workflow that depend on the repository-specific stage order, role handoffs, command surface, and project structure rules.
---

# SlideMax Workflow

## Overview

This skill is the canonical entry point for the SlideMax workflow in this repository.

Use it when the task depends on the repository-specific execution order, role protocol, command entry points, project layout, or workflow-facing assets under `skills/slidemax_workflow/`.

This skill is not a full replacement for the workflow rules. It tells you how to enter the workflow correctly, which files to read next, which commands are authoritative, and which checks prevent avoidable failures.

## When to Use

- Generate PPT, XHS, story, or related outputs from Markdown, PDF, URL, or mixed source material.
- Run or explain the `Strategist -> Image_Generator -> Executor -> Finalize -> Export` process.
- Modify workflow-facing roles, commands, docs, examples, templates, or shared workflow services under `skills/slidemax_workflow/`.
- Audit workflow completeness, tool reliability, repository boundaries, or role handoff quality.
- Debug why a PPT task failed, stalled, skipped a stage, or exported incorrectly.

## When Not to Use

- The task is unrelated to the SlideMax workflow.
- The task is only a generic Python, frontend, infrastructure, or shell issue with no repository-specific workflow context.
- A narrower skill can solve the task without using this repository's workflow rules, role model, or command surface.

## Quick Activation Flow

```text
Need to work on a PPT task in this repository?
|
+-- Is the task source material? -------------------------------+
|   |
|   +-- PDF -> run `commands/pdf_to_md.py` first               |
|   +-- URL -> run `commands/web_to_md.py` or `.cjs` first     |
|   +-- Screenshot/image document -> use OCR skill first       |
|   |      `.agent/skills/ocr_image_to_markdown/SKILL.md`      |
|   +-- Markdown/text -> continue                              |
|                                                              |
+-- Is there already a project folder? ------------------------+
|   |
|   +-- No -> run `commands/project_manager.py init`           |
|   +-- Yes -> inspect project structure                       |
|                                                              |
+-- Is a template required? -----------------------------------+
|   |
|   +-- Yes -> copy template files into `templates/` and       |
|   |         image assets into `images/` before Strategist    |
|   +-- No -> continue                                         |
|                                                              |
+-- Read `AGENTS.md` -> enter stage execution order -----------+
    |
    +-- Stage 0: mandatory preflight
    +-- Stage 1-3: source prep, project init, template decision
    +-- Stage 4: Strategist
    +-- Stage 5: Image_Generator if AI or stock images are needed
    +-- Stage 6: Executor
    +-- Stage 7: finalize SVG and export PPTX
    +-- Stage 8: optional visual optimization
```

## Core Concepts

- `skills/slidemax_workflow/` is the only workflow source of truth.
- `AGENTS.md` is the main workflow manual.
- `workflows/generate-ppt.md` is a redirect entry, not a second workflow definition.
- `commands/` is the only canonical CLI surface.
- `slidemax/` contains reusable Python services; command scripts should stay thin.
- `workspace/` stores runtime projects and generated artifacts, not canonical workflow assets.
- `references/` is supporting navigation material, not the source of truth.

## Mandatory Read Order

Read in this order before executing or modifying a workflow task:

1. `skills/slidemax_workflow/AGENTS.md`
2. `skills/slidemax_workflow/workflows/generate-ppt.md` only to confirm the redirect behavior
3. The required role file in `skills/slidemax_workflow/roles/`
4. The relevant command documentation in `skills/slidemax_workflow/commands/README.md` when running or changing tooling
5. The shared service implementation in `skills/slidemax_workflow/slidemax/` when the task is not command-only

## Stage Execution Map

| Stage | Trigger | Mandatory Read | Primary Output | Canonical Commands |
|------|---------|----------------|----------------|--------------------|
| Stage 0 | Any PPT workflow task | `AGENTS.md` | Preflight confirmation | None |
| Stage 1 | Source is PDF, URL, or image-based document | `AGENTS.md` | Markdown source | `pdf_to_md.py`, `web_to_md.py`, `web_to_md.cjs`, OCR skill |
| Stage 2 | New project required | `AGENTS.md` | Project folder | `project_manager.py init` |
| Stage 3 | Template-based workflow | `AGENTS.md` | Template files in project | Copy assets before Strategist |
| Stage 4 | Every PPT project | `roles/Strategist.md` | Project design-outline markdown file | `analyze_images.py` when user images exist |
| Stage 5 | AI or stock images needed | `roles/Image_Generator.md` | `images/`, `images/stock/`, `images/image_prompts.md` | `image_generate.py`, `download_stock_image.py`, `register_stock_image.py`, `smoke_test_image_provider.py` |
| Stage 6 | Slide production | Matching Executor role | `svg_output/`, `notes/total.md` | Role-driven generation |
| Stage 7 | SVG output exists | `AGENTS.md`, `commands/README.md` | `svg_final/`, `.pptx` | `finalize_svg.py`, `svg_to_pptx.py` |
| Stage 8 | User requests polish | `roles/Optimizer_CRAP.md` | Improved SVG/PPTX | Re-run finalize and export |

## Reliability Rules

These rules exist to reduce failure rates during PPT generation and workflow maintenance.

1. Never skip Stage 0 preflight.
2. Never enter a role stage before reading that role's file.
3. If the source is PDF or URL, convert it immediately before doing strategy work.
4. Create the project folder before writing workflow outputs.
5. If templates are used, copy template files into the project before Strategist starts.
6. Keep all generated or downloaded image assets on project-local paths.
7. When stock images are used, normalize them into `images/stock/` and register provenance before Executor references them.
8. Prefer `image_generate.py` for AI image generation instead of ad-hoc provider commands.
9. Use provider smoke tests before claiming a live image provider is ready.
10. Export from `svg_final/`, not directly from `svg_output/`, unless you are intentionally debugging pre-finalized SVG.
11. Put reusable logic in `slidemax/`; keep `commands/` thin.
12. Do not create duplicate workflow sources outside `skills/slidemax_workflow/`.

## Tool Reliability Map

### Source Ingestion

- `commands/pdf_to_md.py`
  - Use for native PDF conversion.
  - Best when speed, privacy, and local execution matter.
- `commands/web_to_md.py`
  - Use for normal web pages.
- `commands/web_to_md.cjs`
  - Prefer for WeChat or high-protection sites.
- OCR skill: `.agent/skills/ocr_image_to_markdown/SKILL.md`
  - Use for screenshots, image-only pages, and image documents when the source must be transcribed into Markdown and no command-based OCR path is available.

### Project Lifecycle

- `commands/project_manager.py init`
  - Use before any project-local output is created.
- `commands/project_manager.py validate`
  - Use before claiming project completeness.
- `commands/project_manager.py info`
  - Use to inspect an existing project quickly.

### Image Acquisition

- `commands/image_generate.py`
  - Canonical AI image generation entry point.
  - Prefer this over provider-specific ad-hoc flows.
- `commands/smoke_test_image_provider.py`
  - Use before relying on a live provider configuration.
- `commands/download_stock_image.py`
  - Use when downloading a commercial stock image into a project.
- `commands/register_stock_image.py`
  - Use when the stock asset already exists locally and needs provenance tracking.

### Finalize and Export

- `commands/finalize_svg.py`
  - Canonical post-processing entry point.
- `commands/svg_to_pptx.py`
  - Canonical export command.
  - Prefer `-s final` for finalized assets.

### Quality and Diagnostics

- `commands/batch_validate.py`
  - Use for multi-project validation.
- `commands/svg_quality_checker.py`
  - Use for SVG quality diagnostics.
- `commands/error_helper.py`
  - Use when a command error needs repository-specific interpretation.

## Failure Recovery Guide

Use this section when a workflow run feels incomplete or unreliable.

### Symptom: Strategy started before source conversion

Fix:
- Stop the strategy phase.
- Convert PDF or URL into Markdown first.
- Resume from Stage 1.

### Symptom: Executor starts but images are not ready

Fix:
- Pause slide production.
- Complete Stage 5 first.
- Confirm assets exist under `images/` or `images/stock/`.

### Symptom: Provider works inconsistently or fails live

Fix:
- Run `smoke_test_image_provider.py` with the same provider, model, and output settings.
- Verify credentials and base URL.
- Record any provider-specific constraints before treating the setup as stable.

### Symptom: Exported PPTX looks wrong

Fix:
- Confirm export was run from finalized assets.
- Re-run `finalize_svg.py`.
- Re-export with `svg_to_pptx.py -s final`.
- Use quality and validation tools before changing unrelated workflow code.

### Symptom: Workflow docs disagree

Fix:
- Treat `skills/slidemax_workflow/AGENTS.md` as authoritative.
- Treat `workflows/generate-ppt.md` as a redirect only.
- Update this skill so future agents enter the same source of truth.

## Practical Operating Pattern

1. Enter through this skill.
2. Read `AGENTS.md`.
3. Identify the current stage.
4. Read the matching role file.
5. Run the canonical command from `commands/`.
6. Keep shared logic changes in `slidemax/`.
7. Validate outputs before declaring the workflow step complete.

## Examples

Input: Generate a PPT from a PDF source.
Output: Read `AGENTS.md`, convert the PDF with `commands/pdf_to_md.py`, initialize the project with `commands/project_manager.py init`, then follow Strategist, Image_Generator if required, Executor, finalize, and export.

Input: Generate a PPT from screenshots or image-only source pages.
Output: Read `AGENTS.md`, use the OCR skill at `.agent/skills/ocr_image_to_markdown/SKILL.md` to transcribe the images into Markdown first, then continue with project initialization and the normal PPT workflow.

Input: Improve image-provider reliability for PPT generation.
Output: Update `slidemax/image_generation.py`, keep `commands/image_generate.py` thin, validate the provider with `smoke_test_image_provider.py`, and synchronize the related docs and examples.

Input: Audit workflow duplication.
Output: Keep `skills/slidemax_workflow/` as the only workflow source of truth, reduce duplicate entry docs, and ensure this skill points future agents to the correct file order.

## Integration

- `brainstorming` - Use before broad workflow redesign, capability expansion, or major documentation restructuring.
- `writing-skills` - Use when editing this skill or validating whether the skill teaches the right workflow behavior.
- `software-engineering` - Use when reviewing repository architecture, module boundaries, or command-to-service layering.
- `verification-before-completion` - Use before claiming the workflow, docs, or tooling updates are complete.

## References

- `skills/slidemax_workflow/AGENTS.md` - Canonical workflow rules.
- `skills/slidemax_workflow/workflows/generate-ppt.md` - Redirect entry.
- `skills/slidemax_workflow/commands/README.md` - Command reference.
- `skills/slidemax_workflow/docs/ppt_workflow_operator_manual.md` - Chinese operator manual for execution flow and checklists.
- `.agent/skills/ocr_image_to_markdown/SKILL.md` - OCR fallback for screenshots and image-based source material.
- `skills/slidemax_workflow/roles/README.md` - Role map.
- `skills/slidemax_workflow/docs/image_generation_setup.md` - Image setup and credentials.
- `skills/slidemax_workflow/docs/image_stock_sources.md` - Stock image provenance workflow.
- `skills/slidemax_workflow/docs/ark_video_generation.md` - ARK image-to-video flow.

## Skill Metadata

- Created: 2026-03-07
- Last Updated: 2026-03-08
- Version: 1.2.0
