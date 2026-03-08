# Workflow References

This directory stores the canonical workflow entry documents for the `slidemax-workflow` skill.

## How This Directory Fits

- [`../AGENTS.md`](../AGENTS.md) is the full workflow and rules handbook.
- This `workflows/` directory stores the stage-entry documents referenced by that handbook.
- Update workflow-stage instructions here, and keep `AGENTS.md` aligned when stage order or gate rules change.

## Workflow Entries

- `generate-ppt.md` - main PPT workflow entry
- `create-template.md` - template creation workflow entry

## Maintenance Rules

- Treat `skills/slidemax_workflow/` as the only workflow source of truth.
- Read the relevant workflow entry before executing a workflow stage.
- Update workflow instructions here instead of duplicating them in other directories.
- If a workflow rule affects role switching, stage gates, or command ordering, update `../AGENTS.md` in the same change.
