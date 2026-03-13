# Stage Playbooks

This directory stores the detailed stage playbooks referenced by `../../AGENTS.md`.

## Purpose

- Keep `../../AGENTS.md` short enough to act as the canonical handbook entry.
- Keep stage-specific operating detail in focused documents.
- Provide stable extension points when a stage gains more rules or tooling.

## Stage Groups

| Stage Group | File | Covers |
|-------------|------|--------|
| Preflight, source, and project setup | [01-preflight-source-project.md](./01-preflight-source-project.md) | Stage 0 to Stage 3 |
| Strategy and image acquisition | [02-strategy-and-images.md](./02-strategy-and-images.md) | Stage 4 to Stage 5 |
| Execution, delivery, and optimization | [03-execution-delivery.md](./03-execution-delivery.md) | Stage 6 to Stage 8 |

## Maintenance Rules

- Update `../../AGENTS.md` first when stage order or gate rules change.
- Keep each playbook scoped to one stage group.
- Put role-specific detail in `../../roles/` or `../../roles/guides/`, not here.
- Put command detail in `../../references/docs/command_reference.md`, not here.
