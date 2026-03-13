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
- Run or explain the `Strategist -> Image_Generator -> Executor -> Delivery -> Validate` process.
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
|   +-- PDF -> run `scripts/slidemax.py pdf_to_md` first       |
|   +-- URL -> run `scripts/slidemax.py web_to_md` first       |
|   +-- Screenshot/image document -> use OCR skill first       |
|   |      `.agent/skills/ocr_image_to_markdown/SKILL.md`      |
|   +-- Markdown/text -> continue                              |
|                                                              |
+-- Is there already a project folder? ------------------------+
|   |
|   +-- No -> run `scripts/slidemax.py project_manager init`  |
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
    +-- Stage 7: standard delivery path
    |      `total_md_split` -> `finalize_svg` -> `svg_to_pptx -s final` -> `project_manager validate`
    +-- Stage 8: optional visual optimization after first draft
           re-run Stage 7 after any optimizer edits
```

## Core Concepts

- `skills/slidemax_workflow/` is the only workflow source of truth.
- `AGENTS.md` is the canonical workflow handbook.
- `workflows/stages/` stores the detailed stage playbooks referenced by `AGENTS.md`.
- `workflows/generate-ppt.md` is a redirect entry, not a second workflow definition.
- `roles/guides/` stores dense role reference material referenced by the role entry files.
- `scripts/slidemax.py` is the canonical CLI surface.
- `scripts/` stores the canonical CLI surface and standalone fallback scripts.
- `references/docs/command_reference*.md` stores command documentation.
- `slidemax/` contains reusable Python services and the shared command registry.
- `web_to_md_cjs` remains the standalone Node fallback for protected sites and WeChat pages under `scripts/web_to_md.cjs`.
- `workspace/` stores runtime projects and generated artifacts, not canonical workflow assets.
- `references/docs/` stores topic-specific references, command documentation, and redirect entries only.
- `references/` should stay documentation-focused and should not become a second workflow handbook.

## Mandatory Read Order

Read in this order before executing or modifying a workflow task:

1. `skills/slidemax_workflow/AGENTS.md`
2. `skills/slidemax_workflow/workflows/generate-ppt.md` only to confirm the redirect behavior
3. The relevant stage playbook in `skills/slidemax_workflow/workflows/stages/` when stage detail is needed
4. The required role file in `skills/slidemax_workflow/roles/`
5. The matching role guide in `skills/slidemax_workflow/roles/guides/` when the role file points to one
6. The relevant command documentation in `skills/slidemax_workflow/references/docs/command_reference.md` when running or changing tooling
7. The shared service implementation in `skills/slidemax_workflow/slidemax/` when the task is not command-only

## Stage Execution Map

| Stage | Trigger | Mandatory Read | Primary Output | Canonical Commands |
|------|---------|----------------|----------------|--------------------|
| Stage 0 | Any PPT workflow task | `AGENTS.md` | Preflight confirmation | None |
| Stage 1 | Source is PDF, URL, or image-based document | `AGENTS.md` | Markdown source | `pdf_to_md`, `web_to_md`, `web_to_md_cjs`, OCR skill |
| Stage 2 | New project required | `AGENTS.md` | Project folder | `project_manager init` |
| Stage 3 | Template-based workflow | `AGENTS.md` | Template files in project | Copy assets before Strategist |
| Stage 4 | Every PPT project | `roles/Strategist.md` | Project design brief (`design_specification.md`) | `analyze_images` when user images exist |
| Stage 5 | AI or stock images needed | `roles/Image_Generator.md` | `images/`, `images/stock/`, `images/image_prompts.md` | `image_generate`, `download_stock_image`, `register_stock_image`, `smoke_test_image_provider` |
| Stage 6 | Slide production | Matching Executor role | `svg_output/`, `notes/total.md` | Role-driven generation |
| Stage 7 | SVG output exists | `AGENTS.md`, `references/docs/command_reference.md` | Split notes, `svg_final/`, `.pptx`, validation result | `total_md_split`, `finalize_svg`, `svg_to_pptx`, `project_manager validate` |
| Stage 8 | User requests polish after a first draft | `roles/Optimizer_CRAP.md` | Improved SVG/PPTX | Re-run Stage 7 after optimizer edits |

## Reliability Rules

These rules exist to reduce failure rates during PPT generation and workflow maintenance.

1. Never skip Stage 0 preflight.
2. Never enter a role stage before reading that role's file.
3. If the source is PDF or URL, convert it immediately before doing strategy work.
4. Create the project folder before writing workflow outputs.
5. If templates are used, copy template files into the project before Strategist starts.
6. Keep all generated or downloaded image assets on project-local paths.
7. When stock images are used, normalize them into `images/stock/` and register provenance before Executor references them.
8. Prefer `image_generate` for AI image generation instead of ad-hoc provider commands.
9. Use provider smoke tests before claiming a live image provider is ready.
10. Use the standard delivery path `total_md_split -> finalize_svg -> svg_to_pptx -s final -> project_manager validate` unless you are intentionally debugging a narrower step.
11. `svg_to_pptx` can auto-split `notes/total.md` when per-slide notes are missing, but explicit `total_md_split` remains the preferred delivery path for earlier note validation.
12. Export from `svg_final/`, not directly from `svg_output/`, unless you are intentionally debugging pre-finalized SVG.
13. Put reusable logic in `slidemax/`; keep all Python entrypoints in `scripts/`.
14. Do not create duplicate workflow sources outside `skills/slidemax_workflow/`.

## Tool Reliability Map

### Source Ingestion

- `scripts/slidemax.py pdf_to_md`
  - Use for native PDF conversion.
  - Best when speed, privacy, and local execution matter.
- `scripts/slidemax.py web_to_md`
  - Use for normal web pages.
- `scripts/slidemax.py web_to_md_cjs`
  - Prefer for WeChat or high-protection sites.
- OCR skill: `.agent/skills/ocr_image_to_markdown/SKILL.md`
  - Use for screenshots, image-only pages, and image documents when the source must be transcribed into Markdown and no command-based OCR path is available.

### Project Lifecycle

- `scripts/slidemax.py project_manager init`
  - Use before any project-local output is created.
- `scripts/slidemax.py project_manager validate`
  - Use before claiming project completeness.
- `scripts/slidemax.py project_manager info`
  - Use to inspect an existing project quickly.
- `scripts/slidemax.py project_manager audit`
  - Use to inspect workflow stage progression and detect blocking stage gaps.
- `scripts/slidemax.py project_manager doctor`
  - Use for preflight checks or machine-readable readiness reports.

### Image Acquisition

- `scripts/slidemax.py image_generate`
  - Canonical AI image generation entry point.
  - Prefer this over provider-specific ad-hoc flows.
- `scripts/slidemax.py smoke_test_image_provider`
  - Use before relying on a live provider configuration.
- `scripts/slidemax.py download_stock_image`
  - Use when downloading a commercial stock image into a project.
- `scripts/slidemax.py register_stock_image`
  - Use when the stock asset already exists locally and needs provenance tracking.

### Finalize and Export

- `scripts/slidemax.py finalize_svg`
  - Canonical post-processing entry point.
- `scripts/slidemax.py svg_to_pptx`
  - Canonical export command.
  - Prefer `-s final` for finalized assets.

### Quality and Diagnostics

- `scripts/slidemax.py batch_validate`
  - Use for multi-project validation.
- `scripts/slidemax.py svg_quality_checker`
  - Use for SVG quality diagnostics.
- `scripts/slidemax.py error_helper`
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
- Run `smoke_test_image_provider` with the same provider, model, and output settings.
- Verify credentials and base URL.
- Record any provider-specific constraints before treating the setup as stable.

### Symptom: Exported PPTX looks wrong

Fix:
- Confirm export was run from finalized assets.
- Re-run `finalize_svg`.
- Re-export with `svg_to_pptx -s final`.
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
5. Run the canonical command from `scripts/slidemax.py`.
6. Keep shared logic changes in `slidemax/`.
7. Validate outputs before declaring the workflow step complete.

## Examples

Input: Generate a PPT from a PDF source.
Output: Read `AGENTS.md`, convert the PDF with `scripts/slidemax.py pdf_to_md`, initialize the project with `scripts/slidemax.py project_manager init`, then follow Strategist, Image_Generator if required, Executor, `scripts/slidemax.py total_md_split`, `scripts/slidemax.py finalize_svg`, `scripts/slidemax.py svg_to_pptx -s final`, and `scripts/slidemax.py project_manager validate`.

Input: Generate a PPT from screenshots or image-only source pages.
Output: Read `AGENTS.md`, use the OCR skill at `.agent/skills/ocr_image_to_markdown/SKILL.md` to transcribe the images into Markdown first, then continue with project initialization and the normal PPT workflow.

Input: Improve image-provider reliability for PPT generation.
Output: Update `slidemax/image_generation.py`, keep the unified registry thin, validate the provider with `scripts/slidemax.py smoke_test_image_provider`, and synchronize the related docs and examples.

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
- `skills/slidemax_workflow/references/docs/command_reference.md` - Command reference.
- `skills/slidemax_workflow/references/docs/image_prompt_guidance.md` - Compact guide for drafting `images/image_prompts.md`.
- `.agent/skills/ocr_image_to_markdown/SKILL.md` - OCR fallback for screenshots and image-based source material.
- `skills/slidemax_workflow/roles/AGENTS.md` - Role map.
- `skills/slidemax_workflow/references/docs/image_generation_setup.md` - Image setup and credentials.
- `skills/slidemax_workflow/references/docs/image_stock_sources.md` - Stock image provenance workflow.
- `skills/slidemax_workflow/references/docs/ark_video_generation.md` - ARK image-to-video flow.

## Skill Metadata

- Created: 2026-03-07
- Last Updated: 2026-03-12
- Version: 1.3.1
