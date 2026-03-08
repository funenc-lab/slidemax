# AI Role Definitions

[中文](./README_CN.md) | English

This directory contains the core AI role definition documents used by SlideMax.

> 📖 **Full workflow and usage handbook**: see [AGENTS.md](../AGENTS.md)

## Operational Role Quickstart

Use this page to decide which role document to read next before entering the detailed role instructions.

### Role Decision Flow

```text
Need to continue a PPT workflow task?
|
+-- No project strategy yet? ---------------- yes -> read `Strategist.md`
|
+-- Need reusable page templates? ----------- yes -> read `Template_Designer.md`
|
+-- Need AI-generated or stock images? ------ yes -> read `Image_Generator.md`
|
+-- Need slide production? ------------------ yes -> choose one Executor
|   |
|   +-- General storytelling / flexible visual style -> `Executor_General.md`
|   +-- Standard consulting / report style ----------> `Executor_Consultant.md`
|   +-- MBB-grade consulting style ------------------> `Executor_Consultant_Top.md`
|
+-- Need visual polish after first draft? --- yes -> read `Optimizer_CRAP.md`
```

### Role Handoff Gates

| Current Stage | Minimum Input Required | Next Role | Do Not Switch Until |
|---------------|------------------------|-----------|---------------------|
| Template creation request | Template brief and target format | `Template_Designer.md` | The task is confirmed to be template-building work |
| Project start | Source content and project path | `Strategist.md` | Source has been normalized when needed |
| Strategy complete | Design outline and content plan | `Image_Generator.md` or Executor | Asset decisions are explicit |
| Image planning complete | Prompt file and asset list | Matching Executor | Required images are local or scheduled |
| Slide draft complete | `svg_output/` and `notes/total.md` | `Optimizer_CRAP.md` or finalize/export | First draft exists and is reviewable |
| Optimization complete | Updated SVG output | Finalize/export flow | Post-processing has been re-run after edits |

### Reliable Role Routing Rules

- Start with `Strategist.md` unless the task is strictly template-only or maintenance-only.
- Do not enter any Executor before strategy output exists.
- Do not let Executor guess missing images; route through `Image_Generator.md` when image acquisition is still open.
- Use `Template_Designer.md` only for template-building work, not normal slide production.
- Use `Optimizer_CRAP.md` after a first complete draft, not before.

## Role Index

| Role | File | Responsibility | Trigger |
|------|------|----------------|---------|
| **Strategist** | [Strategist.md](./Strategist.md) | Eight confirmations and design brief | Required at project start |
| **Template Designer** | [Template_Designer.md](./Template_Designer.md) | Reusable page template creation | Use the `/create-template` workflow |
| **Image Generator** | [Image_Generator.md](./Image_Generator.md) | AI image generation and stock image planning | When image acquisition includes AI or stock assets |
| **Executor - General** | [Executor_General.md](./Executor_General.md) | Flexible general-style SVG slides | Choose the general visual route |
| **Executor - Consultant** | [Executor_Consultant.md](./Executor_Consultant.md) | Standard consulting-style SVG slides | Choose the consultant route |
| **Executor - Consultant Top** | [Executor_Consultant_Top.md](./Executor_Consultant_Top.md) | MBB-grade consulting SVG slides | Choose the top consulting route |
| **Optimizer - CRAP** | [Optimizer_CRAP.md](./Optimizer_CRAP.md) | Visual quality optimization and polish | Optional optimization stage |

## Supported Canvas Formats

- **Presentation**: PPT 16:9 (`1280×720`), PPT 4:3 (`1024×768`)
- **Social media**: Xiaohongshu (`1242×1660`), WeChat Moments (`1080×1080`), Story (`1080×1920`)
- **Marketing assets**: WeChat header (`900×383`), landscape and portrait posters

See [Canvas Formats](../docs/canvas_formats.md) for the full matrix.

## Executor Selection Guide

| PPT Type | Recommended Role |
|----------|------------------|
| Business consulting / financial analysis | `Executor_Consultant_Top` |
| Work report / government report | `Executor_Consultant` |
| Promotion / branding / mixed visual storytelling | `Executor_General` |
| Training deck / team sharing | `Executor_General` |

## Related Documents

| Document | Description |
|----------|-------------|
| [AGENTS.md](../AGENTS.md) | Full workflow, role switching protocol, and technical constraints |
| [Design Guidelines](../docs/design_guidelines.md) | Detailed color, typography, and layout rules |
| [Workflow Tutorial](../docs/workflow_tutorial.md) | End-to-end examples |
| [Operator Manual](../docs/ppt_workflow_operator_manual.md) | Execution-oriented operating manual |
| [Quick Reference](../docs/quick_reference.md) | Fast lookup for commands and parameters |
