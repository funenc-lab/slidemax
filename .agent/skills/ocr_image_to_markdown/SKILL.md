---
name: ocr-image-to-markdown
description: Use when the source material is a screenshot, scanned page, image-only document, table snapshot, slide image, or other visual content that must be transcribed into Markdown before further processing, especially when no command-based OCR path is available or when a workflow needs a multimodal fallback for image-based source ingestion.
---

# OCR Image to Markdown

## Overview

This skill converts image-based source material into structured Markdown by using the agent's visual understanding instead of a local OCR library.

Use it when the input is primarily visual and the next workflow stage needs editable Markdown rather than raw images.

This skill is especially useful as a fallback path for screenshot-heavy or scan-heavy source material in the PPT workflow.

## When to Use

- The source is a screenshot, scanned page, image-only PDF page, whiteboard capture, slide image, chart image, or table snapshot.
- The content must become Markdown before strategy, drafting, summarization, or downstream workflow steps can begin.
- A command-based OCR tool is unavailable, unreliable, or inappropriate for the current environment.
- The task requires preserving structure such as headings, bullet lists, tables, or reading order.
- The PPT workflow is blocked at source normalization because the input is image-based rather than text-based.

## When Not to Use

- The source is already readable text, Markdown, HTML, or a normal PDF that can be handled by a dedicated converter.
- The task only needs a high-level visual summary and not a faithful Markdown transcription.
- A canonical repository command already handles the source more directly and more reliably.
- The image is too low quality to support meaningful transcription and the user would be better served by a limitation notice.

## Quick Activation Flow

```text
Need Markdown from a visual source?
|
+-- Is the source already text-based? -------- yes -> use the normal text workflow
|
+-- Is the source a screenshot, scan, or image-only page? --- yes -> use this skill
|
+-- Read the image with the available image-viewing capability
|
+-- Extract structure first
|   -> headings
|   -> paragraphs
|   -> bullet lists
|   -> tables
|   -> chart labels / visible values
|
+-- Convert into clean Markdown
|
+-- Save the Markdown output to a project-local `.md` file
|
+-- Hand off the Markdown to the next workflow stage
```

## Input Contract

Before using this skill, confirm the following:

| Required Input | Why It Matters | Do Not Proceed Without |
|----------------|----------------|------------------------|
| One or more image paths or image attachments | The skill depends on visual access to the source | A readable image source |
| Clear output purpose | The Markdown structure should match the downstream use case | A known target workflow |
| Expected grouping or ordering | Multi-image tasks need stable sequencing | A defined image order |

## Output Contract

This skill should leave the workflow with:

- One or more Markdown sections that preserve the visible logical structure of the image source
- Tables converted into valid Markdown tables when possible
- Numeric values transcribed carefully and checked visually
- A saved `.md` file when the task expects a persistent project artifact
- Any limitations explicitly noted when parts of the image are unreadable or ambiguous

## Core Transcription Rules

### 1. Preserve Reading Order

Serialize content in the clearest logical order:

- Top to bottom
- Left to right when layout is column-based
- Section by section when there are panels or grouped regions

### 2. Preserve Structure

Map visible structure into Markdown deliberately:

- Titles -> `#`, `##`, `###`
- Bullet lists -> `-` or numbered lists
- Short labels -> inline text or compact lists
- Tables -> Markdown tables
- Chart legends or visible key values -> bullet lists or tables

### 3. Transcribe Tables Carefully

When a table is visible:

- Rebuild headers and rows explicitly
- Keep column order stable
- Expand merged cells logically when needed
- Leave cells empty if the visual merge makes the missing value ambiguous
- Prefer correctness over artificial completeness

### 4. Handle Charts and Diagrams Pragmatically

When the image contains a chart or logic diagram:

- Extract visible labels, categories, units, and explicit values
- Describe trends only when the values are not fully readable
- Do not invent hidden data points
- Distinguish clearly between observed text and inferred meaning

### 5. Mark Uncertainty Honestly

If part of the image cannot be read reliably:

- Say so explicitly
- Keep the uncertainty local to the affected text
- Do not silently guess numbers, names, or headings

## Reliability Rules

- Do not start transcription until the image has actually been viewed.
- Do not use local OCR libraries as a substitute for this skill's visual workflow unless the user explicitly requests a different method.
- Do not invent text that is not visible.
- Do not flatten complex content into plain paragraphs when structure is recoverable.
- Do not hide ambiguity in financial, tabular, or compliance-sensitive material.
- Do not leave the output only in chat when the workflow expects a saved Markdown artifact.

## Failure Recovery

### Symptom: The image is readable but the structure is messy

Fix:
- Re-read the image by regions
- Recover headings and groups first
- Rebuild the Markdown in logical blocks instead of line-by-line noise

### Symptom: The table is hard to reconstruct

Fix:
- Identify headers first
- Reconstruct one row at a time
- Leave uncertain cells blank or annotate uncertainty
- Avoid fabricating merged-cell behavior

### Symptom: The image quality is too poor

Fix:
- State the limitation explicitly
- Extract only the parts that are visually reliable
- Ask for a clearer source only if the task truly depends on the missing content

### Symptom: Multiple screenshots belong to one document

Fix:
- Establish a stable ordering first
- Process each image into a clearly labeled section
- Merge the results into one Markdown file only after the sequence is confirmed

## PPT Workflow Integration

In the PPT workflow, this skill acts as a Stage 1 fallback for image-based source normalization.

Use it when the source material is not suitable for `pdf_to_md.py`, `web_to_md.py`, or `web_to_md.cjs`, but the downstream PPT workflow still requires Markdown as the working source.

Recommended handoff pattern:

1. Transcribe screenshots or scan images into Markdown
2. Save the result as a project-local `.md` file
3. Continue with project initialization and the normal PPT workflow

Related workflow entry points:

- `skills/ppt_master_workflow/SKILL.md`
- `skills/ppt_master_workflow/AGENTS.md`
- `skills/ppt_master_workflow/docs/ppt_workflow_operator_manual.md`

## Example Scenarios

### Scenario 1: Financial table screenshots

Input:
- Three quarterly-report screenshots with tables

Output:
- One Markdown file with section headings and reconstructed tables

### Scenario 2: Slide screenshots from a reference deck

Input:
- A set of PNG slide captures

Output:
- One Markdown outline preserving slide titles, bullets, and visible key numbers

### Scenario 3: Scan-heavy source for the PPT workflow

Input:
- Image-only pages that cannot be consumed directly by the normal source-ingestion commands

Output:
- A normalized Markdown source that can be handed to the Strategist stage
