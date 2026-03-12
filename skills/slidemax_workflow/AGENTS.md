# AGENTS.md - SlideMax Workflow Handbook

> AI agent note: this file is the canonical workflow and rule handbook for PPT generation in this repository.
>
> Read this file before executing `/generate-ppt`.

---

## Navigation

| Section | Description |
|---------|-------------|
| [Workflow](#workflow) | End-to-end stage map and stage playbook routing |
| [Rulebook](#rulebook) | Constraints, handoff protocol, and non-negotiable rules |
| [Common Commands](#common-commands) | Canonical command quick reference |
| [Important Resources](#important-resources) | Roles, guides, templates, docs, and examples |

## Operational Quickstart

Use this section to choose the correct path before reading the detailed stage playbooks.

### End-to-End Flow

```text
User source
  -> Normalize source format
     -> PDF: `pdf_to_md`
     -> URL: `web_to_md` or `web_to_md_cjs`
     -> Screenshot or image document: use OCR skill `.agent/skills/ocr_image_to_markdown/SKILL.md`
     -> Markdown or text: use directly
  -> Initialize project with `project_manager init`
  -> Inspect or preflight the project when needed with `project_manager info|audit|doctor`
  -> Decide template strategy
     -> Template present: copy into `templates/` and `images/` first
     -> No template: continue with free design
  -> Run Strategist
  -> Run Image_Generator when AI or stock images are needed
  -> Run the matching Executor
  -> Run `total_md_split`
  -> Run `finalize_svg`
  -> Run `svg_to_pptx -s final`
  -> Run `project_manager validate`
  -> Spot check outputs before claiming completion
```

### Command Decision Flow

```text
Need to start or continue a PPT task?
|
+-- Source is PDF? ----------------------------- yes -> `pdf_to_md`
|
+-- Source is URL? ----------------------------- yes -> `web_to_md` / `web_to_md_cjs`
|
+-- Source is screenshot or image document? ---- yes -> OCR skill at `.agent/skills/ocr_image_to_markdown/SKILL.md`
|
+-- Project folder missing? -------------------- yes -> `project_manager init`
|
+-- Need project inspection or preflight? ------ yes -> `project_manager info|audit|doctor`
|
+-- Template-driven delivery? ------------------ yes -> copy template assets before Strategist
|
+-- User images provided? ---------------------- yes -> `analyze_images`
|
+-- AI or stock images needed? ----------------- yes -> Stage 5 image workflow
|                                                     -> `image_generate` or stock commands
|
+-- SVG output and `notes/total.md` ready? ----- yes -> `total_md_split`
|
+-- Per-slide notes ready? --------------------- yes -> `finalize_svg`
|
+-- Finalized SVG ready? ----------------------- yes -> `svg_to_pptx -s final`
|
+-- Need delivery verification? ---------------- yes -> `project_manager validate`
```

## Stage Gate Checklist

| Gate | Required Evidence | Do Not Proceed Until |
|------|-------------------|----------------------|
| Preflight | `AGENTS.md` has been read and the workflow is understood | Role switching rules and source normalization rules are clear |
| Source Ready | Source is already Markdown, or conversion has completed | PDF, URL, or image-based source has been normalized |
| Project Ready | Project directory exists under `workspace/` | Workflow outputs have a valid destination |
| Template Ready | Template files and assets are copied into the project | Strategist can reference the actual template materials |
| Strategy Ready | A design brief exists in the project | Executor has a design and content contract |
| Image Ready | Image prompts and assets exist on project-local paths | Executor will not need to guess or hotlink assets |
| SVG Ready | Slides exist in `svg_output/` and `notes/total.md` exists | Note splitting has real input to process |
| Notes Ready | `total_md_split` has produced per-slide notes in `notes/` | Finalize and export will not hide note mapping problems |
| Final Ready | Post-processing completed into `svg_final/` | Export uses finalized assets instead of raw SVG |
| Delivery Ready | PPTX exists, validation passes, and a spot check was completed | Completion claims are backed by current evidence |

## Reliability Checklist

- Always normalize PDF or URL sources before strategy work starts.
- Always create the project folder before writing prompts, notes, SVG, or exported files.
- Always resolve template files before Strategist begins.
- Always write image prompts before AI image generation.
- Always keep image assets on project-local paths under `images/` or `images/stock/`.
- Always run provider smoke tests before treating a live image provider as stable.
- Always split notes explicitly with `total_md_split` before delivery exports.
- Always treat exporter auto-split as a fallback, not the primary delivery path.
- Always finalize SVG before exporting PPTX for delivery.
- Always run `project_manager validate` before claiming the workflow is complete.
- Always spot check the latest output before saying delivery is done.

# Workflow

> This is the primary execution workflow for SlideMax PPT tasks.

## Workflow Overview

```text
Source -> Project Init -> Template Decision -> Strategist -> [Image_Generator] -> Executor -> Note Split -> Finalize -> Export -> Validate
```

## Stage Playbooks

Use these documents for detailed stage execution.

| Stage Group | File | Covers |
|-------------|------|--------|
| Preflight, source, and project setup | [workflows/stages/01-preflight-source-project.md](./workflows/stages/01-preflight-source-project.md) | Stage 0 to Stage 3 |
| Strategy and image acquisition | [workflows/stages/02-strategy-and-images.md](./workflows/stages/02-strategy-and-images.md) | Stage 4 to Stage 5 |
| Execution, delivery, and optimization | [workflows/stages/03-execution-delivery.md](./workflows/stages/03-execution-delivery.md) | Stage 6 to Stage 8 |

## Stage Summary

| Stage | Trigger | Mandatory Read | Primary Output | Canonical Commands |
|------|---------|----------------|----------------|--------------------|
| Stage 0 | Any PPT workflow task | `AGENTS.md`, Stage 0-3 playbook | Preflight confirmation | None |
| Stage 1 | Source is PDF, URL, or image-based document | Stage 0-3 playbook | Markdown source | `pdf_to_md`, `web_to_md`, `web_to_md_cjs`, OCR skill |
| Stage 2 | New project required | Stage 0-3 playbook | Project folder | `project_manager init` |
| Stage 3 | Template-based workflow | Stage 0-3 playbook | Template files in project | Copy assets before Strategist |
| Stage 4 | Every PPT project | `roles/Strategist.md`, Stage 4-5 playbook | Project design brief | `analyze_images` when user images exist |
| Stage 5 | AI or stock images needed | `roles/Image_Generator.md`, Stage 4-5 playbook | `images/`, `images/stock/`, `images/image_prompts.md` | `image_generate`, `download_stock_image`, `register_stock_image`, `smoke_test_image_provider` |
| Stage 6 | Slide production | Matching Executor role, Stage 6-8 playbook | `svg_output/`, `notes/total.md` | Role-driven generation |
| Stage 7 | SVG output exists | Stage 6-8 playbook, `references/docs/command_reference.md` | Split notes, `svg_final/`, `.pptx`, validation result | `total_md_split`, `finalize_svg`, `svg_to_pptx`, `project_manager validate` |
| Stage 8 | User requests polish after a first draft | `roles/Optimizer_CRAP.md`, Stage 6-8 playbook | Improved SVG/PPTX | Re-run Stage 7 after optimizer edits |

# Rulebook

> The following constraints and protocols are mandatory when executing the SlideMax workflow.

## Project Overview

SlideMax is an AI-assisted multi-format SVG content generation system. It turns source documents into presentation-ready outputs through staged role handoffs and canonical tooling.

## Role Switching Protocol

### 1. Read the Role Definition Before Switching

Before executing any stage, read the corresponding role file.

| Stage | Required File | Trigger |
|-------|---------------|---------|
| Strategy planning | `skills/slidemax_workflow/roles/Strategist.md` | New PPT or related content-generation request |
| Image acquisition | `skills/slidemax_workflow/roles/Image_Generator.md` | Image strategy includes AI generation or stock assets |
| General execution | `skills/slidemax_workflow/roles/Executor_General.md` | User chooses the general visual route |
| Consultant execution | `skills/slidemax_workflow/roles/Executor_Consultant.md` | User chooses the consultant route |
| Top consultant execution | `skills/slidemax_workflow/roles/Executor_Consultant_Top.md` | User chooses the top consultant route |
| Visual optimization | `skills/slidemax_workflow/roles/Optimizer_CRAP.md` | User requests polish or quality is not yet good enough |
| Template creation | `skills/slidemax_workflow/roles/Template_Designer.md` | The task is specifically to build reusable templates |

Do not perform a role's task before reading its file.

### 2. Emit an Explicit Role Switch Marker

Use a marker like this:

```markdown
---
## [Role Switch: Image_Generator]

Read: `skills/slidemax_workflow/roles/Image_Generator.md`
Task: Create prompts and prepare required image assets for the project
---
```

### 3. Emit Phase Checkpoints

Every phase must end with a clear completion checkpoint and the next step.

Reference markers live in:

- `workflows/stages/02-strategy-and-images.md`
- `workflows/stages/03-execution-delivery.md`
- `roles/guides/strategist-design-brief-contract.md`

## Automatic Source Normalization

When the user provides a PDF or URL, convert it immediately.

| Source | Tool | Command |
|--------|------|---------|
| PDF | `pdf_to_md` | `python3 skills/slidemax_workflow/scripts/slidemax.py pdf_to_md <file>` |
| Web page | `web_to_md` | `python3 skills/slidemax_workflow/scripts/slidemax.py web_to_md <url>` |
| WeChat or protected site | `web_to_md_cjs` | `python3 skills/slidemax_workflow/scripts/slidemax.py web_to_md_cjs <url>` |

Prohibited behavior:

- Waiting for the user to explicitly ask for conversion after already detecting a PDF or URL
- Starting strategy work before normalization

Correct behavior:

- Convert first
- Create the project
- Resolve template choice
- Enter Strategist

## Critical Rules

### 1. Strategist Must Start with Eight Confirmations

Before any detailed content analysis, Strategist must complete the eight confirmations documented in `roles/guides/strategist-confirmations.md`.

If the image strategy includes user-provided assets, run:

```bash
python3 skills/slidemax_workflow/scripts/slidemax.py analyze_images <project-path>/images
```

Do that after the eight confirmations and before finalizing the design brief.

### 2. Image Assets Must Be Localized Before Execution

- `Image_Generator` must write `images/image_prompts.md` before live generation starts.
- Stock assets must be registered under `images/stock/`.
- Required image files must be local before Executor starts, unless the brief intentionally marks them as placeholders.

### 3. Executor Must Produce Both Slides and Notes

Executor outputs are incomplete without both:

- `svg_output/`
- `notes/total.md`

### 4. Delivery Uses the Standard Four-Step Path

```text
total_md_split -> finalize_svg -> svg_to_pptx -s final -> project_manager validate
```

Do not bypass this path for delivery work unless you are intentionally debugging an internal step.

### 5. SVG Technical Constraints

Executor role files contain the detailed examples. These baseline rules are non-negotiable:

Base rules:

- `viewBox` must match the target canvas
- Use `<rect>` for the background
- Use system fonts defined by the chosen typography strategy
- Use manual line breaks with `<tspan>`

Blacklist:

`clipPath` | `mask` | `<style>` | `class` | `id` | external CSS | `<foreignObject>` | `textPath` | `@font-face` | `<animate*>` | `<script>` | `marker-end` | `<iframe>`

PPT compatibility replacements:

| Avoid | Use Instead |
|-------|-------------|
| `rgba()` colors | `fill-opacity` or `stroke-opacity` |
| `<g opacity>` | Per-element opacity |
| `<image opacity>` | Overlay-based dimming or masking approach |
| `marker-end` arrows | Explicit shapes such as `<polygon>` |

### 6. Canvas Formats

| Format | Size | viewBox |
|--------|------|---------|
| PPT 16:9 | 1280x720 | `0 0 1280 720` |
| PPT 4:3 | 1024x768 | `0 0 1024 768` |
| Xiaohongshu | 1242x1660 | `0 0 1242 1660` |
| WeChat Moments | 1080x1080 | `0 0 1080 1080` |
| Story | 1080x1920 | `0 0 1080 1920` |
| WeChat Header | 900x383 | `0 0 900 383` |

Full format reference: [references/docs/canvas_formats.md](./references/docs/canvas_formats.md)

## Common Commands

```bash
# Convert PDF to Markdown
python3 skills/slidemax_workflow/scripts/slidemax.py pdf_to_md <pdf-file>

# Convert a web page to Markdown
python3 skills/slidemax_workflow/scripts/slidemax.py web_to_md <url>
python3 skills/slidemax_workflow/scripts/slidemax.py web_to_md_cjs <url>

# Initialize a project
python3 skills/slidemax_workflow/scripts/slidemax.py project_manager init <name> --format ppt169

# Inspect or validate a project
python3 skills/slidemax_workflow/scripts/slidemax.py project_manager info <path>
python3 skills/slidemax_workflow/scripts/slidemax.py project_manager doctor <path>
python3 skills/slidemax_workflow/scripts/slidemax.py project_manager validate <path>

# Check SVG quality
python3 skills/slidemax_workflow/scripts/slidemax.py svg_quality_checker <path>

# Split notes
python3 skills/slidemax_workflow/scripts/slidemax.py total_md_split <project-path>

# Finalize SVG
python3 skills/slidemax_workflow/scripts/slidemax.py finalize_svg <project-path>

# Export PPTX with notes
python3 skills/slidemax_workflow/scripts/slidemax.py svg_to_pptx <project-path> -s final

# Export PPTX without notes
python3 skills/slidemax_workflow/scripts/slidemax.py svg_to_pptx <project-path> -s final --no-notes
```

## Project Layout

```text
project/
├── svg_output/
│   ├── 01_cover.svg
│   ├── 02_toc.svg
│   └── ...
├── svg_final/
├── images/
│   └── stock/
├── notes/
│   ├── total.md
│   ├── 01_cover.md
│   ├── 02_toc.md
│   └── ...
└── *.pptx
```

## Important Resources

| Resource | Path |
|----------|------|
| Workflow redirect | `skills/slidemax_workflow/workflows/generate-ppt.md` |
| Stage playbooks index | `skills/slidemax_workflow/workflows/stages/README.md` |
| Role index | `skills/slidemax_workflow/roles/AGENTS.md` |
| Role guides index | `skills/slidemax_workflow/roles/guides/README.md` |
| Chart templates | `skills/slidemax_workflow/templates/charts/` |
| Icon library | `skills/slidemax_workflow/templates/icons/` |
| Design guidelines | `skills/slidemax_workflow/references/docs/design_guidelines.md` |
| Image layout specification | `skills/slidemax_workflow/references/docs/image_layout_spec.md` |
| Canvas formats | `skills/slidemax_workflow/references/docs/canvas_formats.md` |
| SVG image embedding | `skills/slidemax_workflow/references/docs/svg_image_embedding.md` |
| Image generation providers | `skills/slidemax_workflow/references/docs/image_generation_providers.md` |
| Image setup | `skills/slidemax_workflow/references/docs/image_generation_setup.md` |
| Image prompt guidance | `skills/slidemax_workflow/references/docs/image_prompt_guidance.md` |
| Example projects | `skills/slidemax_workflow/examples/` |
| Command reference | `skills/slidemax_workflow/references/docs/command_reference.md` |

## AI Agent Notes

### Core Principles

- This repository defines a role-based workflow, not a single monolithic prompt.
- Quality depends on strict adherence to the design brief, canvas format, and delivery chain.
- The role switching protocol is mandatory.

### Mandatory Rules for Agents

1. Read the target role file before switching stages.
2. Emit an explicit role switch marker.
3. Emit a checkpoint at the end of each stage.
4. Create the project immediately after source normalization is complete.
5. Resolve template choice before Strategist begins.
6. Treat the Strategist eight confirmations as mandatory, regardless of template usage.
7. If the image strategy includes user-provided assets, run `analyze_images` before finalizing the design brief.
8. If the image strategy includes AI generation or stock assets, finish Image_Generator before Executor starts.
9. Treat the Executor workflow as two required phases: visual construction and logic construction.
10. After SVG and notes are ready, run the full Stage 7 delivery chain in order.

### Delivery Reminder

Once SVG and notes are complete, run:

```bash
python3 skills/slidemax_workflow/scripts/slidemax.py total_md_split <project-path>
python3 skills/slidemax_workflow/scripts/slidemax.py finalize_svg <project-path>
python3 skills/slidemax_workflow/scripts/slidemax.py svg_to_pptx <project-path> -s final
python3 skills/slidemax_workflow/scripts/slidemax.py project_manager validate <project-path>
```

Do not add narrow `--only` flags to bypass the standard delivery path unless you are intentionally debugging a specific internal step.
